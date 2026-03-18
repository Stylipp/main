import hashlib
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class ScrapedProduct(BaseModel):
    """A single product extracted from a store page."""

    url: str
    external_id: str = ""
    title: str
    description: str | None = None
    price: Decimal | None = None
    sale_price: Decimal | None = None
    currency: str = "ILS"
    image_urls: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    store_id: str
    scraped_at: datetime

    @field_validator("external_id", mode="before")
    @classmethod
    def derive_external_id(cls, v: str, info) -> str:
        """Derive external_id from URL hash if not explicitly provided."""
        if v:
            return v
        url = info.data.get("url", "")
        if url:
            return hashlib.md5(url.encode()).hexdigest()[:16]
        return ""


class ScrapeResult(BaseModel):
    """Result of scraping a single store."""

    store_id: str
    total_urls: int
    total_scraped: int
    total_failed: int
    total_new: int
    total_changed: int
    total_removed: int
    duration_seconds: float
    errors: list[str] = Field(default_factory=list)


class SyncResult(BaseModel):
    """Result of syncing changes to backend systems."""

    store_id: str
    woo_created: int
    woo_updated: int
    db_created: int
    db_updated: int
    qdrant_upserted: int
    qdrant_removed: int
    errors: list[str] = Field(default_factory=list)


class PipelineResult(BaseModel):
    """Overall nightly run result."""

    started_at: datetime
    finished_at: datetime
    stores: list[ScrapeResult] = Field(default_factory=list)
    sync: list[SyncResult] = Field(default_factory=list)
    recluster_triggered: bool
