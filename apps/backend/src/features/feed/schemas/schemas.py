"""Pydantic v2 schemas for the feed API endpoint.

Defines FeedItem (individual product in the feed) and FeedResponse
(paginated feed response with cursor-based pagination).
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict


class FeedMode(str, Enum):
    TRENDING = "trending"
    HYBRID = "hybrid"
    PERSONALIZED = "personalized"


class FeedItem(BaseModel):
    """A single product item in the personalized feed.

    Attributes:
        product_id: External product identifier.
        title: Product title/name.
        price: Product price as a float.
        currency: ISO currency code (e.g. "USD").
        image_url: URL to the product image.
        product_url: URL to the product page.
        score: Final ranking score from multi-factor scoring.
        explanation: Template explanation for why the item appears in the feed:
            - "Similar to your recent likes"
            - "Matches your style"
            - "Within your usual price range"
            - "Trending with other shoppers"
    """

    product_id: str
    title: str
    price: float
    currency: str
    image_url: str
    product_url: str
    category: str
    score: float
    explanation: str

    model_config = ConfigDict(from_attributes=True)


class FeedResponse(BaseModel):
    """Paginated feed response with cursor-based pagination.

    Attributes:
        items: List of feed items for this page.
        next_cursor: Opaque cursor for fetching the next page, or None if no more.
        has_more: Whether there are more items available.
        total_in_batch: Total number of ranked items in the current batch.
    """

    items: list[FeedItem]
    next_cursor: str | None
    has_more: bool
    total_in_batch: int
    active_category: str | None = None
    feed_mode: FeedMode
