"""Data models for scraped products."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class ScrapedProduct:
    url: str
    external_id: str
    title: str
    store_id: str
    scraped_at: datetime
    description: str | None = None
    price: Decimal | None = None
    sale_price: Decimal | None = None
    currency: str = "ILS"
    image_urls: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    failed: int = 0
    accepted_ids: list[str] = field(default_factory=list)


@dataclass
class ChangeReport:
    store_id: str
    new: list[ScrapedProduct]
    changed: list[ScrapedProduct]
    removed_ids: list[str]
    unchanged_count: int
