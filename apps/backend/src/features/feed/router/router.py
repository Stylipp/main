"""Feed API router with cursor-based pagination.

Provides GET /feed endpoint that returns a ranked, diversity-injected
personalized feed for authenticated users. Uses opaque cursor pagination
for infinite scroll support.

Cursor format: base64-encoded JSON {"o": offset, "b": batch_id}
"""

from __future__ import annotations

import base64
import json
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.core.qdrant import get_qdrant_client
from src.features.feed.schemas.schemas import FeedItem, FeedResponse
from src.features.feed.service.feed_service import FeedService
from src.features.feed.service.ranking_service import RankedCandidate
from src.models.product import Product

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feed", tags=["Feed"])

# Explanation templates (exactly 3 per PROJECT.md)
_EXPLANATION_SIMILAR = "Similar to your recent likes"
_EXPLANATION_STYLE = "Matches your style"
_EXPLANATION_PRICE = "Within your usual price range"


def _encode_cursor(offset: int, batch_id: str) -> str:
    """Encode pagination state into an opaque cursor string.

    Args:
        offset: Number of items already returned from this batch.
        batch_id: Unique identifier for this feed generation batch.

    Returns:
        URL-safe base64-encoded JSON string.
    """
    payload = json.dumps({"o": offset, "b": batch_id})
    return base64.urlsafe_b64encode(payload.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[int, str]:
    """Decode an opaque cursor string into pagination state.

    Args:
        cursor: URL-safe base64-encoded JSON string.

    Returns:
        Tuple of (offset, batch_id).

    Raises:
        ValueError: If the cursor is malformed or contains invalid data.
    """
    try:
        raw = base64.urlsafe_b64decode(cursor.encode())
        data = json.loads(raw)
        offset = int(data["o"])
        batch_id = str(data["b"])
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        return offset, batch_id
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
        raise ValueError(f"Invalid cursor format: {exc}") from exc


def _select_explanation(candidate: RankedCandidate) -> str:
    """Select an explanation template based on the dominant scoring factor.

    Simple rule per PROJECT.md (3 templates only, no category labeling):
    - If price_score is the highest non-cosine factor -> price explanation
    - If cluster_prior_score is highest non-cosine -> style explanation
    - Default -> similarity explanation

    Args:
        candidate: Ranked candidate with individual score components.

    Returns:
        One of the 3 explanation template strings.
    """
    if (
        candidate.price_score >= candidate.cluster_prior_score
        and candidate.price_score >= candidate.freshness_score
    ):
        return _EXPLANATION_PRICE
    if (
        candidate.cluster_prior_score >= candidate.price_score
        and candidate.cluster_prior_score >= candidate.freshness_score
    ):
        return _EXPLANATION_STYLE
    return _EXPLANATION_SIMILAR


@router.get("/", response_model=FeedResponse)
async def get_feed(
    cursor: str | None = None,
    page_size: int = Query(default=20, ge=1, le=50),
    user_id: UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> FeedResponse:
    """Get the personalized feed for the authenticated user.

    Returns ranked, diversity-injected product recommendations with
    cursor-based pagination for infinite scroll.

    Args:
        cursor: Opaque pagination cursor (base64 JSON). None for first page.
        page_size: Number of items per page (1-50, default 20).
        user_id: Authenticated user ID from JWT token.
        session: Async SQLAlchemy database session.

    Returns:
        FeedResponse with feed items, pagination cursor, and metadata.

    Raises:
        HTTPException 400: Invalid cursor format.
        HTTPException 404: User vector not found (onboarding incomplete).
    """
    # Step 1: Decode cursor if provided
    offset = 0
    batch_id = str(uuid4())

    if cursor is not None:
        try:
            offset, batch_id = _decode_cursor(cursor)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid pagination cursor",
            )

    # Step 2: Instantiate FeedService
    qdrant_client = await get_qdrant_client()
    settings = get_settings()
    feed_service = FeedService(qdrant_client=qdrant_client, settings=settings)

    # Step 3: Generate feed (retrieve, rank, inject diversity)
    try:
        ranked_candidates = await feed_service.generate_feed(
            user_id=str(user_id),
            seen_ids=[],
            session=session,
            page_size=page_size + offset,  # Fetch enough to skip offset items
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    # Apply offset for cursor pagination
    total_in_batch = len(ranked_candidates)
    paged_candidates = ranked_candidates[offset : offset + page_size]

    if not paged_candidates:
        return FeedResponse(
            items=[],
            next_cursor=None,
            has_more=False,
            total_in_batch=total_in_batch,
        )

    # Step 4: Enrich with product metadata from PostgreSQL
    product_ids = []
    for product_id in (c.product_id for c in paged_candidates):
        try:
            product_ids.append(UUID(product_id))
        except ValueError:
            logger.warning("Skipping invalid feed product_id=%s", product_id)

    stmt = select(Product).where(Product.id.in_(product_ids))
    result = await session.execute(stmt)
    products = result.scalars().all()

    # Build lookup by PostgreSQL UUID string (matches Qdrant point ID payload).
    product_map: dict[str, Product] = {str(p.id): p for p in products}

    # Step 5: Build FeedItem list with explanation templates
    items: list[FeedItem] = []
    for candidate in paged_candidates:
        product = product_map.get(candidate.product_id)
        if product is None:
            # Skip candidates without matching product metadata
            logger.warning(
                "Product metadata not found for product_id=%s, skipping",
                candidate.product_id,
            )
            continue

        items.append(
            FeedItem(
                product_id=candidate.product_id,
                title=product.title,
                price=float(product.price),
                currency=product.currency,
                image_url=product.image_url,
                product_url=product.product_url,
                score=candidate.score,
                explanation=_select_explanation(candidate),
            )
        )

    # Step 6: Encode next cursor if more items available
    new_offset = offset + page_size
    has_more = new_offset < total_in_batch
    next_cursor = _encode_cursor(new_offset, batch_id) if has_more else None

    # Step 7: Return response
    return FeedResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        total_in_batch=total_in_batch,
    )
