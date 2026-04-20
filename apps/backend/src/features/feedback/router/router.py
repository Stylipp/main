"""Feedback API router.

Provides POST /feedback endpoint for recording user interactions
(like/dislike/save) with products.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.features.feedback.schemas.schemas import (
    ExposureBatchRequest,
    ExposureBatchResponse,
    FeedbackRequest,
    FeedbackResponse,
)
from src.features.feedback.service.exposure_service import ExposureService
from src.features.feedback.service.profile_update_service import ProfileUpdateService
from src.features.feedback.service.service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["Feedback"])

_feedback_service = FeedbackService()
_exposure_service = ExposureService()
_profile_update_service = ProfileUpdateService()


@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def record_feedback(
    body: FeedbackRequest,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    """Record user feedback (like/dislike/save) on a product.

    Args:
        body: Request body with product_id (external_id) and action.
        user_id: Authenticated user ID from JWT token.
        session: Async SQLAlchemy database session.

    Returns:
        FeedbackResponse with the created interaction record.

    Raises:
        HTTPException 404: Product not found with the given external_id.
    """
    try:
        interaction = await _feedback_service.record_feedback(
            user_id=user_id,
            product_id_external=body.product_id,
            action=body.action.value,
            session=session,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    background_tasks.add_task(_profile_update_service.process_pending_updates, user_id)

    return FeedbackResponse(
        id=str(interaction.id),
        action=interaction.action,
        created_at=interaction.created_at,
    )


@router.post("/exposures", response_model=ExposureBatchResponse)
async def record_exposures(
    body: ExposureBatchRequest,
    user_id: UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ExposureBatchResponse:
    """Record visible-card exposures and action completions."""
    processed = await _exposure_service.record_exposures(
        user_id=user_id,
        events=body.events,
        session=session,
    )
    return ExposureBatchResponse(received=len(body.events), processed=processed)
