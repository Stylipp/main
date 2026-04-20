"""Pydantic v2 schemas for the feedback API endpoint.

Defines FeedbackAction enum, FeedbackRequest, and FeedbackResponse
for recording user interactions (like/dislike/save) with products.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.features.feed.schemas.schemas import FeedMode


class FeedbackAction(str, Enum):
    """Valid feedback actions for user-product interactions."""

    LIKE = "like"
    DISLIKE = "dislike"
    SAVE = "save"


class FeedbackRequest(BaseModel):
    """Request body for recording user feedback on a product.

    Attributes:
        product_id: External product identifier (Qdrant point ID, NOT UUID).
        action: The feedback action (like, dislike, or save).
    """

    product_id: str
    action: FeedbackAction


class FeedbackResponse(BaseModel):
    """Response body after recording user feedback.

    Attributes:
        id: Unique identifier of the created interaction record.
        action: The recorded feedback action.
        created_at: Timestamp when the interaction was recorded.
    """

    id: str
    action: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExposureEvent(BaseModel):
    """A single feed exposure or exposure completion event."""

    product_id: str
    session_id: str = Field(min_length=1, max_length=64)
    feed_mode: FeedMode
    position: int = Field(ge=1)
    shown_at: datetime
    action: FeedbackAction | None = None
    action_at: datetime | None = None
    dwell_ms: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_action_fields(self) -> "ExposureEvent":
        if self.action is None:
            if self.action_at is not None or self.dwell_ms is not None:
                raise ValueError(
                    "action_at and dwell_ms require an action to be present"
                )
            return self

        if self.action_at is None:
            raise ValueError("action_at is required when action is present")
        return self


class ExposureBatchRequest(BaseModel):
    """Batch request for recording exposure events."""

    events: list[ExposureEvent] = Field(min_length=1, max_length=100)


class ExposureBatchResponse(BaseModel):
    """Response after recording a batch of exposure events."""

    received: int
    processed: int
