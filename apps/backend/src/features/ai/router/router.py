"""AI feature router with embedding and quality check endpoints.

Endpoints:
    GET  /api/ai/health         - Check model status
    POST /api/ai/embed          - Generate embedding from image URL (testing only)
    POST /api/ai/quality-check  - Validate image quality before embedding
"""

from __future__ import annotations

import logging
from io import BytesIO
from typing import TYPE_CHECKING

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from PIL import Image

from src.features.ai.schemas import (
    EmbeddingHealthResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    QualityCheckRequest,
    QualityCheckResponse,
)
from src.features.ai.service.quality_gate import QualityGateService

if TYPE_CHECKING:
    from src.features.ai.service.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])


def get_embedding_service(request: Request) -> EmbeddingService:
    """Get EmbeddingService from app state.

    Args:
        request: FastAPI request object.

    Returns:
        The EmbeddingService instance.

    Raises:
        HTTPException: If the service is not available.
    """
    service = getattr(request.app.state, "embedding_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service not available",
        )
    return service


@router.get("/health", response_model=EmbeddingHealthResponse)
async def ai_health(request: Request) -> EmbeddingHealthResponse:
    """Check the status of the embedding service and model.

    Returns:
        Model status including loaded state and configuration.
    """
    try:
        service = get_embedding_service(request)
        return EmbeddingHealthResponse(
            status="healthy" if service.is_loaded else "degraded",
            model_loaded=service.is_loaded,
            model_name=service.MODEL_NAME,
            embedding_dimension=service.EMBEDDING_DIM,
        )
    except HTTPException:
        return EmbeddingHealthResponse(
            status="unavailable",
            model_loaded=False,
        )


@router.post("/embed", response_model=EmbeddingResponse)
async def embed_image(
    request: Request,
    payload: EmbeddingRequest,
) -> EmbeddingResponse:
    """Generate embedding for an image URL.

    This endpoint is for testing purposes only. In production,
    embeddings are generated during product ingestion, not on-demand.

    Args:
        request: FastAPI request object.
        payload: Request containing the image URL.

    Returns:
        The 768-dimensional embedding for the image.

    Raises:
        HTTPException: If image fetch or embedding fails.
    """
    service = get_embedding_service(request)

    if not service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded",
        )

    # Fetch the image from URL
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(payload.image_url)
            response.raise_for_status()
            image_bytes = response.content
    except httpx.HTTPError as e:
        logger.warning("Failed to fetch image: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch image: {e}",
        ) from e

    # Convert to PIL Image
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        logger.warning("Failed to parse image: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format",
        ) from e

    # Generate embedding
    try:
        embedding = await service.get_embedding(image)
    except Exception as e:
        logger.exception("Embedding generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Embedding generation failed",
        ) from e

    return EmbeddingResponse(
        embedding=embedding,
        dimension=len(embedding),
    )


# Stateless service — safe to instantiate at module level
_quality_gate_service = QualityGateService()


@router.post("/quality-check", response_model=QualityCheckResponse)
async def quality_check(
    payload: QualityCheckRequest,
) -> QualityCheckResponse:
    """Validate image quality before embedding generation.

    Checks image dimensions, file size, and blur level against
    configured thresholds. Use this to pre-validate images before
    submitting them for embedding.

    Args:
        payload: Request containing the image URL to validate.

    Returns:
        Quality check results including pass/fail, issues, and scores.

    Raises:
        HTTPException: If the image cannot be fetched or parsed.
    """
    try:
        result = await _quality_gate_service.validate_from_url(payload.image_url)
    except httpx.HTTPError as e:
        logger.warning("Failed to fetch image for quality check: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch image: {e}",
        ) from e
    except Exception as e:
        logger.warning("Failed to parse image for quality check: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format",
        ) from e

    return QualityCheckResponse(
        passed=result.passed,
        issues=[issue.value for issue in result.issues],
        blur_score=result.blur_score,
        width=result.width,
        height=result.height,
        file_size_bytes=result.file_size_bytes,
    )
