"""Products feature router with ingestion and query endpoints.

Endpoints:
    GET  /api/products/health  - Health check for products feature
    GET  /api/products/count   - Get total product count from PostgreSQL
    POST /api/products/ingest  - Ingest a single product (testing/manual)
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.qdrant import get_qdrant_client
from ....models.product import Product
from ...ai.service.quality_gate import QualityGateService
from ..schemas.schemas import ProductCreate
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
