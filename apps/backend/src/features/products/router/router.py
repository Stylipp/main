"""Products feature router with ingestion, query, and archival endpoints.

Endpoints:
    GET  /api/products/health        - Health check for products feature
    GET  /api/products/count         - Get total product count from PostgreSQL
    POST /api/products/ingest        - Ingest a single product (testing/manual)
    POST /api/products/ingest/batch  - Batch ingest/upsert products from scraper
    POST /api/products/archive/batch - Batch archive (soft-delete) products
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.qdrant import get_qdrant_client
from ....models.product import Product
from ...ai.service.quality_gate import QualityGateService
from ..schemas.schemas import (
    BatchArchiveRequest,
    BatchArchiveResponse,
    BatchIngestRequest,
    BatchIngestResponse,
    ProductCreate,
    RejectedItem,
)
from ..service.ingestion_service import IngestionService
from ..service.product_repository import ProductRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["products"])

# Stateless service — safe to instantiate at module level
_quality_gate_service = QualityGateService()


async def get_ingestion_service(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> IngestionService:
    """Build IngestionService with all dependencies wired up.

    Pulls the EmbeddingService from app state and creates a fresh
    ProductRepository per-request with the current DB session.

    Args:
        request: FastAPI request (for app.state access).
        session: Async SQLAlchemy session from dependency injection.

    Returns:
        A fully configured IngestionService instance.

    Raises:
        HTTPException: If the embedding service is not available.
    """
    embedding_service = getattr(request.app.state, "embedding_service", None)
    if embedding_service is None or not embedding_service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service not available",
        )

    qdrant_client = await get_qdrant_client()
    repository = ProductRepository(session)

    return IngestionService(
        repository=repository,
        embedding_service=embedding_service,
        quality_gate=_quality_gate_service,
        qdrant_client=qdrant_client,
    )


@router.get("/health")
async def products_health() -> dict:
    """Health check for the products feature.

    Returns:
        Status dict with feature name.
    """
    return {"status": "ok", "feature": "products"}


@router.get("/count")
async def get_product_count(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get total product count from PostgreSQL.

    Args:
        session: Async SQLAlchemy session.

    Returns:
        Dict with product count.
    """
    result = await session.execute(select(func.count(Product.id)))
    return {"count": result.scalar()}


@router.post("/ingest")
async def ingest_single_product(
    product: ProductCreate,
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> dict:
    """Ingest a single product through the full pipeline.

    This endpoint is primarily for testing and manual ingestion.
    Full batch ingestion will use a dedicated sync endpoint.

    Args:
        product: Product data to ingest.
        service: IngestionService with all dependencies.

    Returns:
        Dict with ingestion result details.

    Raises:
        HTTPException: If ingestion fails unexpectedly.
    """
    result = await service.ingest_product(product)

    if not result.success:
        return {
            "success": False,
            "error": result.error,
            "quality_issues": result.quality_issues,
        }

    return {
        "success": True,
        "product_id": str(result.product_id),
    }


@router.post("/ingest/batch")
async def ingest_batch(
    request_body: BatchIngestRequest,
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BatchIngestResponse:
    """Batch ingest/upsert products from the scraper.

    Processes products sequentially. Each product is either created or updated.
    Individual product failures are captured in the errors list without aborting
    the batch. All successful changes are committed once at the end.

    Args:
        request_body: Batch of products to ingest.
        service: IngestionService with all dependencies.
        session: Async SQLAlchemy session for final commit.

    Returns:
        BatchIngestResponse with counts and per-product error details.
    """
    total = len(request_body.products)
    created = 0
    updated = 0
    failed = 0
    accepted_ids: list[str] = []
    rejected: list[RejectedItem] = []

    for product in request_body.products:
        try:
            result = await service.ingest_or_update_product(product)
        except Exception as e:
            logger.error(
                "Unexpected error ingesting %s/%s: %s",
                product.store_id,
                product.external_id,
                e,
            )
            failed += 1
            rejected.append(
                RejectedItem(
                    external_id=product.external_id,
                    store_id=product.store_id,
                    error=f"Unexpected error: {e!s}",
                    retryable=True,
                )
            )
            continue

        if result.success:
            accepted_ids.append(product.external_id)
            if result.updated:
                updated += 1
            else:
                created += 1
        else:
            failed += 1
            rejected.append(
                RejectedItem(
                    external_id=product.external_id,
                    store_id=product.store_id,
                    error=result.error or "Unknown error",
                    retryable=False,
                )
            )

    await session.commit()

    response = BatchIngestResponse(
        total=total,
        created=created,
        updated=updated,
        failed=failed,
        accepted_ids=accepted_ids,
        rejected=rejected,
    )

    if accepted_ids and rejected:
        return JSONResponse(
            status_code=207,
            content=response.model_dump(mode="json"),
        )

    return response


@router.post("/archive/batch")
async def archive_batch(
    request_body: BatchArchiveRequest,
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BatchArchiveResponse:
    """Batch archive products (soft-delete).

    Sets archived_at timestamp in PostgreSQL and archived=True payload
    flag in Qdrant. Does not hard-delete any data.

    Args:
        request_body: Store ID and external IDs to archive.
        service: IngestionService with all dependencies.
        session: Async SQLAlchemy session for commit.

    Returns:
        BatchArchiveResponse with count and IDs of archived products.
    """
    archived_ids = await service.archive_products(
        external_ids=request_body.external_ids,
        store_id=request_body.store_id,
        session=session,
    )
    await session.commit()

    return BatchArchiveResponse(
        archived_count=len(archived_ids),
        archived_ids=archived_ids,
    )
