"""FeedService: Orchestrates candidate retrieval and multi-factor ranking.

Two-stage feed pipeline:
1. Qdrant retrieves ~100 candidates via user-vector cosine search with filtering
2. Python re-ranks candidates with multi-factor scoring

Uses qdrant_client.search() (NOT query_points()) for Qdrant v1.7.4 compatibility.
"""

from __future__ import annotations

import logging

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    HasIdCondition,
    Range,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings
from src.features.feed.service.ranking_service import RankedCandidate, rank_candidates
from src.models.user import User

logger = logging.getLogger(__name__)

# Candidate retrieval settings
_OVERRETRIEVE_LIMIT = 100
_SCORE_THRESHOLD = 0.2
_PRICE_FILTER_LOW_FACTOR = 0.5
_PRICE_FILTER_HIGH_FACTOR = 2.0

# Scroll batch size for loading cluster priors
_SCROLL_BATCH_SIZE = 100


class FeedService:
    """Orchestrates feed generation: retrieval and ranking.

    Args:
        qdrant_client: Async Qdrant client instance.
        settings: Application settings.
    """

    def __init__(self, qdrant_client: AsyncQdrantClient, settings: Settings) -> None:
        self._qdrant = qdrant_client
        self._settings = settings

    async def _load_user_vector(self, user_id: str) -> list[float] | None:
        """Load user style vector from Qdrant user_profiles collection.

        Returns the vector as a list of floats, or None if not found.
        """
        points = await self._qdrant.retrieve(
            collection_name=self._settings.user_profiles_collection,
            ids=[user_id],
            with_vectors=True,
            with_payload=False,
        )
        if not points or points[0].vector is None:
            return None
        return points[0].vector

    async def _load_price_profile(self, user_id: str, session: AsyncSession) -> dict:
        """Load user price profile from PostgreSQL users table.

        Returns the price_profile JSONB dict, or a neutral default if not set.
        """
        from uuid import UUID

        stmt = select(User.price_profile).where(User.id == UUID(user_id))
        result = await session.execute(stmt)
        price_profile = result.scalar_one_or_none()

        if price_profile is None:
            return {
                "price_min": 0.0,
                "price_max": 0.0,
                "price_median": 0.0,
                "price_std": 0.0,
            }
        return price_profile

    async def _load_cluster_priors(self) -> dict[int, float]:
        """Load cluster priors from Qdrant style_clusters collection.

        Scrolls all points from the small style_clusters collection (~10-200
        clusters) and builds a dict mapping cluster_id -> prior_probability.

        Does NOT cache results (caching deferred to Phase 12).
        """
        priors: dict[int, float] = {}
        offset = None

        while True:
            results, next_offset = await self._qdrant.scroll(
                collection_name=self._settings.cluster_collection,
                limit=_SCROLL_BATCH_SIZE,
                offset=offset,
                with_vectors=False,
                with_payload=True,
            )

            if not results:
                break

            for point in results:
                payload = point.payload or {}
                cluster_index = payload.get("cluster_index")
                prior = payload.get("prior_probability", 0.0)
                if cluster_index is not None:
                    priors[int(cluster_index)] = float(prior)

            if next_offset is None:
                break
            offset = next_offset

        logger.info("Loaded %d cluster priors from Qdrant", len(priors))
        return priors

    def _build_candidate_filter(
        self,
        seen_ids: list[str],
        price_min: float,
        price_max: float,
        *,
        exclude_seen: bool = True,
        apply_price: bool = True,
    ) -> Filter | None:
        """Build a Qdrant filter for candidate retrieval.

        Args:
            seen_ids: Product IDs to exclude.
            price_min: User's minimum preferred price.
            price_max: User's maximum preferred price.
            exclude_seen: Whether to exclude seen items.
            apply_price: Whether to apply price range filter.
        """
        must: list = []
        must_not: list = []

        if exclude_seen and seen_ids:
            must_not.append(HasIdCondition(has_id=seen_ids))

        if apply_price and price_min > 0 and price_max > 0:
            must.append(
                FieldCondition(
                    key="price",
                    range=Range(
                        gte=price_min * _PRICE_FILTER_LOW_FACTOR,
                        lte=price_max * _PRICE_FILTER_HIGH_FACTOR,
                    ),
                )
            )

        if not must and not must_not:
            return None

        return Filter(must=must or None, must_not=must_not or None)

    async def _retrieve_candidates(
        self,
        user_vector: list[float],
        query_filter: Filter | None,
        limit: int = _OVERRETRIEVE_LIMIT,
    ) -> list:
        """Retrieve candidate products from Qdrant via vector search.

        Uses qdrant_client.search() for Qdrant v1.7.4 compatibility.
        """
        return await self._qdrant.search(
            collection_name=self._settings.qdrant_collection,
            query_vector=user_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=_SCORE_THRESHOLD,
            with_payload=True,
            with_vectors=False,
        )

    async def _retrieve_with_shortfall_handling(
        self,
        user_vector: list[float],
        seen_ids: list[str],
        price_min: float,
        price_max: float,
        page_size: int,
    ) -> list:
        """Retrieve candidates with progressive filter widening on shortfall.

        Pattern 4 from RESEARCH.md: Narrow first, broaden on shortfall.
        1. Full filter (price + seen exclusion)
        2. Drop price filter
        3. Drop seen exclusion (allow revisits)
        """
        # Attempt 1: Full filters
        query_filter = self._build_candidate_filter(
            seen_ids,
            price_min,
            price_max,
            exclude_seen=True,
            apply_price=True,
        )
        candidates = await self._retrieve_candidates(user_vector, query_filter)

        if len(candidates) >= page_size:
            return candidates

        logger.warning(
            "Shortfall after full filter: got %d, need %d. "
            "Retrying without price filter.",
            len(candidates),
            page_size,
        )

        # Attempt 2: Drop price filter
        query_filter = self._build_candidate_filter(
            seen_ids,
            price_min,
            price_max,
            exclude_seen=True,
            apply_price=False,
        )
        candidates = await self._retrieve_candidates(user_vector, query_filter)

        if len(candidates) >= page_size:
            return candidates

        logger.warning(
            "Shortfall after dropping price filter: got %d, need %d. "
            "Allowing revisits.",
            len(candidates),
            page_size,
        )

        # Attempt 3: Allow revisits (drop seen exclusion)
        query_filter = self._build_candidate_filter(
            seen_ids,
            price_min,
            price_max,
            exclude_seen=False,
            apply_price=False,
        )
        candidates = await self._retrieve_candidates(user_vector, query_filter)

        return candidates

    async def generate_feed(
        self,
        user_id: str,
        seen_ids: list[str],
        session: AsyncSession,
        page_size: int = 20,
    ) -> list[RankedCandidate]:
        """Generate a ranked feed for a user.

        Pipeline:
        1. Load user vector from Qdrant user_profiles
        2. Load price profile from PostgreSQL
        3. Load cluster priors from Qdrant style_clusters
        4. Retrieve ~100 candidates via Qdrant search()
        5. Apply multi-factor ranking
        6. Return top page_size items

        Args:
            user_id: The user's UUID string.
            seen_ids: List of product IDs already seen by the user.
            session: Async SQLAlchemy session.
            page_size: Number of items to return (default 20).

        Returns:
            List of RankedCandidate sorted by final score.

        Raises:
            ValueError: If user vector is not found.
        """
        # Step 1: Load user vector
        user_vector = await self._load_user_vector(user_id)
        if user_vector is None:
            raise ValueError(
                f"User vector not found for user {user_id}. "
                "Has the user completed onboarding?"
            )

        # Step 2: Load price profile
        price_profile = await self._load_price_profile(user_id, session)
        price_min = price_profile.get("price_min", 0.0)
        price_max = price_profile.get("price_max", 0.0)

        # Step 3: Load cluster priors
        cluster_priors = await self._load_cluster_priors()

        # Step 4: Retrieve candidates with shortfall handling
        candidates = await self._retrieve_with_shortfall_handling(
            user_vector=user_vector,
            seen_ids=seen_ids,
            price_min=price_min,
            price_max=price_max,
            page_size=page_size,
        )

        if not candidates:
            logger.warning("No candidates found for user %s", user_id)
            return []

        # Step 5: Rank candidates
        user_price_profile = {
            "median": price_profile.get("price_median", 0.0),
            "std": price_profile.get("price_std", 0.0),
        }

        ranked = rank_candidates(candidates, user_price_profile, cluster_priors)

        # Step 6: Return top page_size items
        return ranked[:page_size]
