"""Onboarding feature router with photo upload, calibration items, and completion endpoints.

Endpoints:
    POST /api/onboarding/photos           - Upload photo with quality validation + embedding
    POST /api/onboarding/calibration-items - Get calibration swipe items from cold-start service
"""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.core.qdrant import get_qdrant_client
from src.features.ai.service.quality_gate import QualityGateService
from src.features.clustering.service.cold_start_service import ColdStartService
from src.features.onboarding.schemas.schemas import (
    CalibrationItemsRequest,
    CalibrationItemsResponse,
    PhotoUploadResponse,
)
from src.features.onboarding.service.service import OnboardingService
from src.features.storage.service.service import S3StorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

# Module-level quality gate and storage service (stateless singletons)
_quality_gate = QualityGateService()
_storage_service = S3StorageService()


async def get_onboarding_service(request: Request) -> OnboardingService:
    """Build OnboardingService with all dependencies wired up.

    Args:
        request: FastAPI request to access app.state for embedding service.

    Returns:
        A fully configured OnboardingService instance.
    """
    qdrant_client = await get_qdrant_client()
    settings = get_settings()
    cold_start_service = ColdStartService(
        qdrant_client=qdrant_client, settings=settings
    )

    return OnboardingService(
        embedding_service=request.app.state.embedding_service,
        quality_gate=_quality_gate,
        storage_service=_storage_service,
        cold_start_service=cold_start_service,
    )


@router.post(
    "/photos",
    response_model=PhotoUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_photo(
    file: UploadFile,
    user_id: Annotated[UUID, Depends(get_current_user)],
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> PhotoUploadResponse:
    """Upload a photo for onboarding with quality validation and embedding generation.

    Accepts an image file, validates quality (dimensions, blur, file size),
    stores in S3, and generates a 768-dim FashionSigLIP embedding.

    Args:
        file: Uploaded image file.
        user_id: Authenticated user ID from JWT token.
        service: OnboardingService with all dependencies.

    Returns:
        PhotoUploadResponse with S3 key, URL, and embedding vector.

    Raises:
        HTTPException: 422 if image fails quality validation.
    """
    return await service.upload_and_embed_photo(file=file, user_id=user_id)


@router.post(
    "/calibration-items",
    response_model=CalibrationItemsResponse,
)
async def get_calibration_items(
    body: CalibrationItemsRequest,
    user_id: Annotated[UUID, Depends(get_current_user)],
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CalibrationItemsResponse:
    """Get calibration items for the onboarding swipe feed.

    Accepts 1-2 photo embeddings and returns 15 product recommendations
    from the cold-start service with mandatory diversity injection.

    Uses POST because embeddings are too large for query parameters.

    Args:
        body: Request with 1-2 photo embeddings (768-dim each).
        user_id: Authenticated user ID from JWT token.
        service: OnboardingService with all dependencies.
        session: Async SQLAlchemy session for product lookup.

    Returns:
        CalibrationItemsResponse with 15 calibration items.
    """
    return await service.get_calibration_items(
        embeddings=body.embeddings,
        session=session,
    )
