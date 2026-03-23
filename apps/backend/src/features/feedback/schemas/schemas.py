"""Pydantic v2 schemas for the feedback API endpoint.

Defines FeedbackAction enum, FeedbackRequest, and FeedbackResponse
for recording user interactions (like/dislike/save) with products.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


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
