from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from ..utils.category import ProductCategory


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
    category: ProductCategory = ProductCategory.OTHER
    raw_categories: list[str] = Field(default_factory=list)


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
    category: ProductCategory
    raw_categories: list[str]
    created_at: datetime
    updated_at: datetime


class ProductSyncStatus(BaseModel):
    """Status of a product sync operation."""

    store_id: str
    total_fetched: int
    total_valid: int
    total_rejected: int
    rejection_reasons: dict[str, int] = Field(default_factory=dict)


class BatchIngestRequest(BaseModel):
    """Request body for batch product ingestion."""

    products: list[ProductCreate]


class RejectedItem(BaseModel):
    """A product that failed batch ingestion."""

    external_id: str
    store_id: str
    error: str
    retryable: bool


class BatchIngestResponse(BaseModel):
    """Response from a batch product ingestion."""

    total: int
    created: int
    updated: int
    failed: int
    accepted_ids: list[str] = Field(default_factory=list)
    rejected: list[RejectedItem] = Field(default_factory=list)
