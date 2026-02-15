from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    """Data needed to create a product in our system."""

    external_id: str
    store_id: str
    title: str
    description: str | None = None
    price: Decimal
    currency: str = "USD"
    image_url: str
    product_url: str


class ProductResponse(BaseModel):
    """Product data returned by API."""

    id: UUID
    external_id: str
    store_id: str
    title: str
    description: str | None
    price: Decimal
    currency: str
    image_url: str
    product_url: str
    created_at: datetime
    updated_at: datetime


class ProductSyncStatus(BaseModel):
    """Status of a product sync operation."""

    store_id: str
    total_fetched: int
    total_valid: int
    total_rejected: int
    rejection_reasons: dict[str, int] = Field(default_factory=dict)
