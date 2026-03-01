"""Clustering feature router with rebuild, stats, and cold-start endpoints.

Endpoints:
    POST /api/clustering/rebuild     - Trigger full cluster rebuild
    GET  /api/clustering/stats       - Get cluster statistics
    POST /api/clustering/cold-start  - Get cold-start recommendations from embeddings
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.config import get_settings
from ....core.database import get_db
from ....core.qdrant import get_qdrant_client
from ..schemas.schemas import (
    ClusterInfo,
    ClusterStatsResponse,
    ColdStartRequest,
    ColdStartResponse,
    RebuildResponse,
)
from ..service.cluster_repository import ClusterRepository
from ..service.clustering_service import ClusteringService
from ..service.cold_start_service import ColdStartService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clustering", tags=["clustering"])

# Embedding dimension expected by the model
_EMBEDDING_DIM = 768


async def get_clustering_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ClusteringService:
    """Build ClusteringService with all dependencies wired up.

    Args:
        session: Async SQLAlchemy session from dependency injection.

    Returns:
        A fully configured ClusteringService instance.
    """
    qdrant_client = await get_qdrant_client()
    settings = get_settings()
    return ClusteringService(qdrant_client=qdrant_client, settings=settings)


async def get_cold_start_service() -> ColdStartService:
    """Build ColdStartService with all dependencies wired up.

    Returns:
        A fully configured ColdStartService instance.
    """
    qdrant_client = await get_qdrant_client()
    settings = get_settings()
    return ColdStartService(qdrant_client=qdrant_client, settings=settings)


@router.post("/rebuild")
async def rebuild_clusters(
    session: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[ClusteringService, Depends(get_clustering_service)],
) -> RebuildResponse:
    """Trigger a full cluster rebuild.

    This is a long-running operation (~10-60s depending on catalog size).
    It fetches all product embeddings, determines optimal k via silhouette
    analysis, runs K-means, and persists results to PostgreSQL and Qdrant.

    Args:
        session: Async SQLAlchemy session.
        service: ClusteringService with all dependencies.

    Returns:
        RebuildResponse with k, silhouette_score, product_count, cluster_sizes.

    Raises:
        HTTPException: If the rebuild fails unexpectedly.
    """
    try:
        stats = await service.rebuild_clusters(session)
    except Exception:
        logger.exception("Cluster rebuild failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cluster rebuild failed. Check server logs for details.",
        )

    return RebuildResponse(
        k=stats["k"],
        silhouette_score=stats["silhouette_score"],
        product_count=stats["product_count"],
        cluster_sizes={i: size for i, size in enumerate(stats["cluster_sizes"])},
    )


@router.get("/stats")
async def get_cluster_stats(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ClusterStatsResponse:
    """Get cluster statistics from PostgreSQL.

    Queries all StyleCluster records and returns aggregated stats
    including total cluster count, total product count, and per-cluster info.

    Args:
        session: Async SQLAlchemy session.

    Returns:
        ClusterStatsResponse with cluster count, product count, and cluster info.
    """
    repository = ClusterRepository()
    clusters = await repository.get_all_clusters(session)

    cluster_infos = [
        ClusterInfo(
            cluster_index=c.cluster_index,
            product_count=c.product_count,
            prior_probability=c.prior_probability,
        )
        for c in clusters
    ]

    total_products = sum(c.product_count for c in clusters)

    return ClusterStatsResponse(
        total_clusters=len(clusters),
        total_products=total_products,
        clusters=cluster_infos,
    )


@router.post("/cold-start")
async def get_cold_start_feed(
    request: ColdStartRequest,
    service: Annotated[ColdStartService, Depends(get_cold_start_service)],
) -> ColdStartResponse:
    """Get cold-start product recommendations from photo embeddings.

    Accepts 1-2 photo embeddings from user uploads during onboarding,
    matches them to the nearest style clusters, and returns a product feed
    with mandatory diversity injection (3/20 items from adjacent clusters).

    Args:
        request: ColdStartRequest with list of embeddings.
        service: ColdStartService with all dependencies.

    Returns:
        ColdStartResponse with matches, cluster info, and total count.

    Raises:
        HTTPException: If embeddings have incorrect dimensions.
    """
    # Validate embedding dimensions
    for i, embedding in enumerate(request.embeddings):
        if len(embedding) != _EMBEDDING_DIM:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Embedding at index {i} has {len(embedding)} dimensions, "
                    f"expected {_EMBEDDING_DIM}."
                ),
            )

    return await service.get_cold_start_feed(request.embeddings)
