"""Pydantic models for onboarding API contracts.

Defines request/response schemas for:
- Photo upload with quality validation and embedding generation
- Calibration item selection via cold-start service
- Calibration completion with user vector and price profile computation
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PhotoUploadResponse(BaseModel):
    """Response after a successful photo upload with quality validation.

    Attributes:
        key: S3 object key for the uploaded photo.
        url: Public URL of the uploaded photo.
        embedding: 768-dimensional embedding vector from FashionSigLIP.
    """

    key: str
    url: str
    embedding: list[float] = Field(
        ...,
        description="768-dimensional FashionSigLIP embedding vector",
    )


class CalibrationItemsRequest(BaseModel):
    """Request body for retrieving calibration items.

    Contains 1-2 photo embeddings from user uploads during onboarding.
    """

    embeddings: list[list[float]] = Field(
        ...,
        min_length=1,
        max_length=2,
        description="1-2 photo embeddings (768-dim each) from user uploads",
    )


class CalibrationItem(BaseModel):
    """A single product for the calibration swipe feed.

    Attributes:
        product_id: Unique product identifier.
        title: Product display title.
        price: Product price value.
        currency: Currency code (e.g. USD).
        image_url: URL of the product image.
        is_diversity: True if this item is from an adjacent diversity cluster.
    """

    product_id: str
    title: str
    price: float
    currency: str
    image_url: str
    is_diversity: bool = Field(
        default=False,
        description="True if this item is from an adjacent diversity cluster",
    )


class CalibrationItemsResponse(BaseModel):
    """Response containing calibration items for the swipe feed."""

    items: list[CalibrationItem]
    total: int
