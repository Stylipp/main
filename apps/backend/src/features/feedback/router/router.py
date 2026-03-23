"""Feedback API router.

Provides POST /feedback endpoint for recording user interactions
(like/dislike/save) with products.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.features.feedback.schemas.schemas import (
    FeedbackRequest,
    FeedbackResponse,
)
from src.features.feedback.service.service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["Feedback"])

_feedback_service = FeedbackService()


@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def record_feedback(
    body: FeedbackRequest,
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

    return FeedbackResponse(
        id=str(interaction.id),
        action=interaction.action,
        created_at=interaction.created_at,
    )
