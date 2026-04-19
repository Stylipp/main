"""FeedService: Orchestrates candidate retrieval, ranking, and diversity injection.

Two-stage feed pipeline:
1. Qdrant retrieves ~100 candidates via user-vector cosine search with filtering
2. Python re-ranks candidates with multi-factor scoring and diversity injection

Diversity injection is MANDATORY per PROJECT.md: 3/20 items from adjacent clusters.

Uses qdrant_client.search() (NOT query_points()) for Qdrant v1.7.4 compatibility.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    HasIdCondition,
    MatchValue,
    Range,
)
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings
from src.features.feed.schemas.schemas import FeedMode
from src.features.feed.service.ranking_service import RankedCandidate, rank_candidates
from src.features.feed.utils.scoring import compute_freshness_score, normalize_scores
from src.models.product import Product
from src.models.user import User
from src.models.user_interaction import UserInteraction

logger = logging.getLogger(__name__)

# Candidate retrieval settings
_OVERRETRIEVE_LIMIT = 100
_SCORE_THRESHOLD = 0.2
_PRICE_FILTER_LOW_FACTOR = 0.5
_PRICE_FILTER_HIGH_FACTOR = 2.0

# Diversity injection constants (hardcoded per PROJECT.md and Phase 03-02)
_DIVERSITY_COUNT = 3
_PRIMARY_CLUSTER_COUNT = 3
_DIVERSITY_CLUSTER_COUNT = 2
_DIVERSITY_CANDIDATE_LIMIT = 20
_TRENDING_WEIGHT = 0.8
_TRENDING_FRESHNESS_WEIGHT = 0.2

# Scroll batch size for loading cluster priors
_SCROLL_BATCH_SIZE = 100


@dataclass
class FeedGenerationResult:
    feed_mode: FeedMode
    candidates: list[RankedCandidate]


class FeedService:
    """Orchestrates feed generation: retrieval, ranking, and diversity injection.

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

    async def _load_user_profile_state(
        self, user_id: str, session: AsyncSession
    ) -> User | None:
        """Load the user's profile maturity state from PostgreSQL."""
        stmt = select(User).where(User.id == UUID(user_id))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    def _select_feed_mode(
        self,
        *,
        user_vector: list[float] | None,
        profile_confidence: float,
    ) -> FeedMode:
        """Choose feed mode from vector availability and profile maturity."""
        if user_vector is None:
            return FeedMode.TRENDING

        if profile_confidence < self._settings.feed_hybrid_confidence_threshold:
            return FeedMode.HYBRID

        return FeedMode.PERSONALIZED

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

    @staticmethod
    def _coerce_product_ids(product_ids: list[str]) -> list[UUID]:
        """Parse valid UUID product ids for SQL filtering."""
        parsed: list[UUID] = []
        for product_id in product_ids:
            try:
                parsed.append(UUID(product_id))
            except ValueError:
                logger.warning(
                    "Skipping invalid product id=%s in SQL filter", product_id
                )
        return parsed

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

    @staticmethod
    def _build_candidate_filter(
        seen_ids: list[str],
        price_min: float,
        price_max: float,
        category: str | None = None,
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

        if category is not None:
            must.append(
                FieldCondition(
                    key="category",
                    match=MatchValue(value=category),
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
        category: str | None,
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
            category,
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
            category,
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
            category,
            exclude_seen=False,
            apply_price=False,
        )
        candidates = await self._retrieve_candidates(user_vector, query_filter)

        return candidates

    async def _get_interacted_product_ids(
        self, user_id: str, session: AsyncSession
    ) -> set[str]:
        """Get Qdrant point IDs of products the user has already interacted with.

        Queries UserInteraction joined with Product to retrieve the set of
        PostgreSQL product UUIDs that back the Qdrant point IDs the user has
        already liked/disliked/saved.

        Args:
            user_id: The user's UUID string.
            session: Async SQLAlchemy session.

        Returns:
            Set of product UUID strings for already-interacted products.
        """
        from uuid import UUID

        stmt = (
            select(Product.id)
            .join(UserInteraction, UserInteraction.product_id == Product.id)
            .where(UserInteraction.user_id == UUID(user_id))
        )
        result = await session.execute(stmt)
        product_ids = {str(row[0]) for row in result.all()}

        if product_ids:
            logger.info(
                "User %s has %d previously interacted products",
                user_id,
                len(product_ids),
            )

        return product_ids

    async def _retrieve_trending_products(
        self,
        session: AsyncSession,
        exclude_ids: list[str],
        category: str | None,
        limit: int,
        *,
        exclude_seen: bool,
    ) -> list[SimpleNamespace]:
        """Load trending products from PostgreSQL using interaction popularity."""
        interaction_weight = case(
            (UserInteraction.action == "save", 3.0),
            (UserInteraction.action == "like", 2.0),
            (UserInteraction.action == "dislike", -1.0),
            else_=0.0,
        )
        popularity_subquery = (
            select(
                UserInteraction.product_id.label("product_id"),
                func.sum(interaction_weight).label("popularity"),
            )
            .group_by(UserInteraction.product_id)
            .subquery()
        )

        popularity = func.coalesce(popularity_subquery.c.popularity, 0.0)
        stmt = (
            select(
                Product.id,
                Product.price,
                Product.created_at,
                Product.category,
                popularity.label("popularity"),
            )
            .outerjoin(
                popularity_subquery, popularity_subquery.c.product_id == Product.id
            )
            .order_by(popularity.desc(), Product.created_at.desc())
            .limit(limit)
        )

        if category is not None:
            stmt = stmt.where(Product.category == category)

        if exclude_seen and exclude_ids:
            stmt = stmt.where(Product.id.notin_(self._coerce_product_ids(exclude_ids)))

        result = await session.execute(stmt)
        rows = result.all()
        return [
            SimpleNamespace(
                product_id=str(row.id),
                price=float(row.price),
                created_at=row.created_at,
                category=row.category,
                popularity=float(row.popularity or 0.0),
            )
            for row in rows
        ]

    async def _retrieve_trending_with_shortfall_handling(
        self,
        session: AsyncSession,
        exclude_ids: list[str],
        category: str | None,
        page_size: int,
    ) -> list[SimpleNamespace]:
        """Retrieve trending products, then allow revisits if needed."""
        candidates = await self._retrieve_trending_products(
            session=session,
            exclude_ids=exclude_ids,
            category=category,
            limit=_OVERRETRIEVE_LIMIT,
            exclude_seen=True,
        )
        if len(candidates) >= page_size:
            return candidates

        logger.info(
            "Trending shortfall with exclusions: got %d, need %d. Allowing revisits.",
            len(candidates),
            page_size,
        )
        return await self._retrieve_trending_products(
            session=session,
            exclude_ids=exclude_ids,
            category=category,
            limit=_OVERRETRIEVE_LIMIT,
            exclude_seen=False,
        )

    @staticmethod
    def _rank_trending_candidates(
        candidates: list[SimpleNamespace],
    ) -> list[RankedCandidate]:
        """Rank trending candidates from popularity plus freshness."""
        if not candidates:
            return []

        popularity_scores = [candidate.popularity for candidate in candidates]
        freshness_scores = []
        for candidate in candidates:
            created_at = candidate.created_at
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            freshness_scores.append(compute_freshness_score(created_at))

        normalized_popularity = normalize_scores(popularity_scores)
        normalized_freshness = normalize_scores(freshness_scores)

        ranked = []
        for index, candidate in enumerate(candidates):
            final_score = (
                _TRENDING_WEIGHT * normalized_popularity[index]
                + _TRENDING_FRESHNESS_WEIGHT * normalized_freshness[index]
            )
            ranked.append(
                RankedCandidate(
                    product_id=candidate.product_id,
                    score=final_score,
                    cosine_score=0.0,
                    cluster_prior_score=0.0,
                    price_score=0.0,
                    freshness_score=normalized_freshness[index],
                    source="trending",
                )
            )

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked

    @staticmethod
    def _blend_ranked_candidates(
        primary: list[RankedCandidate],
        secondary: list[RankedCandidate],
        *,
        page_size: int,
        primary_target: int,
    ) -> list[RankedCandidate]:
        """Interleave two ranked lists while preserving primary preference."""
        primary_ids = {item.product_id for item in primary}
        unique_secondary = [
            candidate
            for candidate in secondary
            if candidate.product_id not in primary_ids
        ]
        primary_slice = primary[:primary_target]
        secondary_slice = unique_secondary[: max(page_size - len(primary_slice), 0)]
        merged = FeedService._interleave_diversity(primary_slice, secondary_slice)

        if len(merged) < page_size:
            seen_ids = {candidate.product_id for candidate in merged}
            for candidate in primary[primary_target:]:
                if candidate.product_id in seen_ids:
                    continue
                merged.append(candidate)
                seen_ids.add(candidate.product_id)
                if len(merged) >= page_size:
                    break

            if len(merged) < page_size:
                for candidate in unique_secondary[len(secondary_slice) :]:
                    if candidate.product_id in seen_ids:
                        continue
                    merged.append(candidate)
                    seen_ids.add(candidate.product_id)
                    if len(merged) >= page_size:
                        break

        return merged[:page_size]

    @staticmethod
    def _prepare_candidates_for_ranking(
        candidates: list,
        *,
        source: str,
    ) -> list[SimpleNamespace]:
        """Normalize Qdrant candidates before ranking.

        Older or partially-clustered product payloads may be missing fields such
        as cluster_id. The ranker expects a stable payload shape, so we drop
        irreparably malformed candidates and default missing cluster_id to 0.0.
        """
        prepared: list[SimpleNamespace] = []
        dropped_count = 0
        missing_cluster_count = 0

        for candidate in candidates:
            payload = dict(candidate.payload or {})

            missing_required = [
                key
                for key in ("product_id", "price", "created_at")
                if key not in payload
            ]
            if missing_required:
                dropped_count += 1
                logger.warning(
                    "Dropping %s candidate missing payload keys %s",
                    source,
                    ",".join(missing_required),
                )
                continue

            if "cluster_id" not in payload:
                payload["cluster_id"] = 0
                missing_cluster_count += 1

            prepared.append(
                SimpleNamespace(
                    score=candidate.score,
                    payload=payload,
                )
            )

        if missing_cluster_count:
            logger.warning(
                "Defaulted missing cluster_id to 0 for %d %s candidates",
                missing_cluster_count,
                source,
            )

        if dropped_count:
            logger.warning(
                "Dropped %d malformed %s candidates before ranking",
                dropped_count,
                source,
            )

        return prepared

    async def _generate_personalized_feed(
        self,
        *,
        user_vector: list[float],
        user_id: str,
        session: AsyncSession,
        seen_ids: list[str],
        category: str | None,
        page_size: int,
    ) -> list[RankedCandidate]:
        """Run the existing vector-based ranking pipeline."""
        price_profile = await self._load_price_profile(user_id, session)
        price_min = price_profile.get("price_min", 0.0)
        price_max = price_profile.get("price_max", 0.0)
        cluster_priors = await self._load_cluster_priors()

        candidates = await self._retrieve_with_shortfall_handling(
            user_vector=user_vector,
            seen_ids=seen_ids,
            price_min=price_min,
            price_max=price_max,
            category=category,
            page_size=page_size,
        )
        candidates = self._prepare_candidates_for_ranking(
            candidates,
            source="primary",
        )
        if not candidates:
            return []

        user_price_profile = {
            "median": price_profile.get("price_median", 0.0),
            "std": price_profile.get("price_std", 0.0),
        }
        ranked = rank_candidates(candidates, user_price_profile, cluster_priors)
        return await self._inject_diversity(
            user_vector=user_vector,
            cluster_priors=cluster_priors,
            user_price_profile=user_price_profile,
            primary_ranked=ranked,
            seen_ids=seen_ids,
            category=category,
            page_size=page_size,
        )

    async def _generate_trending_feed(
        self,
        *,
        session: AsyncSession,
        seen_ids: list[str],
        category: str | None,
        page_size: int,
    ) -> list[RankedCandidate]:
        """Build a non-vector feed from popularity plus freshness."""
        candidates = await self._retrieve_trending_with_shortfall_handling(
            session=session,
            exclude_ids=seen_ids,
            category=category,
            page_size=page_size,
        )
        return self._rank_trending_candidates(candidates)

    async def generate_feed(
        self,
        user_id: str,
        seen_ids: list[str],
        session: AsyncSession,
        category: str | None = None,
        page_size: int = 20,
    ) -> FeedGenerationResult:
        """Generate a ranked, diversity-injected feed for a user."""
        user_vector = await self._load_user_vector(user_id)
        user = await self._load_user_profile_state(user_id, session)
        interacted_ids = await self._get_interacted_product_ids(user_id, session)
        all_exclude_ids = list(set(seen_ids) | interacted_ids)
        feed_mode = self._select_feed_mode(
            user_vector=user_vector,
            profile_confidence=user.profile_confidence if user is not None else 0.0,
        )

        if feed_mode is FeedMode.TRENDING:
            ranked = await self._generate_trending_feed(
                session=session,
                seen_ids=all_exclude_ids,
                category=category,
                page_size=page_size,
            )
            return FeedGenerationResult(
                feed_mode=FeedMode.TRENDING,
                candidates=ranked[:page_size],
            )

        personalized_ranked = await self._generate_personalized_feed(
            user_vector=user_vector,
            user_id=user_id,
            session=session,
            seen_ids=all_exclude_ids,
            category=category,
            page_size=page_size,
        )

        trending_ranked = await self._generate_trending_feed(
            session=session,
            seen_ids=all_exclude_ids,
            category=category,
            page_size=page_size,
        )

        if not personalized_ranked:
            return FeedGenerationResult(
                feed_mode=FeedMode.TRENDING,
                candidates=trending_ranked[:page_size],
            )

        if feed_mode is FeedMode.HYBRID:
            primary_target = max(
                1,
                min(
                    page_size,
                    math.ceil(
                        page_size * self._settings.feed_hybrid_personalized_ratio
                    ),
                ),
            )
            blended = self._blend_ranked_candidates(
                personalized_ranked,
                trending_ranked,
                page_size=page_size,
                primary_target=primary_target,
            )
            return FeedGenerationResult(feed_mode=FeedMode.HYBRID, candidates=blended)

        discovery_count = min(
            self._settings.feed_personalized_discovery_count,
            max(page_size - 1, 0),
        )
        if discovery_count > 0 and trending_ranked:
            personalized_ranked = self._blend_ranked_candidates(
                personalized_ranked,
                trending_ranked,
                page_size=page_size,
                primary_target=max(page_size - discovery_count, 1),
            )

        return FeedGenerationResult(
            feed_mode=FeedMode.PERSONALIZED,
            candidates=personalized_ranked[:page_size],
        )

    async def _identify_diversity_clusters(
        self,
        user_vector: list[float],
    ) -> list[int]:
        """Identify diversity clusters (4th-5th ranked by similarity).

        Searches style_clusters collection with user_vector to find the
        nearest clusters, then takes the 4th and 5th ranked as diversity
        clusters (adjacent, not random -- per Phase 03-02 decision).

        Returns:
            List of cluster indices for diversity injection.
        """
        total_needed = _PRIMARY_CLUSTER_COUNT + _DIVERSITY_CLUSTER_COUNT
        results = await self._qdrant.search(
            collection_name=self._settings.cluster_collection,
            query_vector=user_vector,
            limit=total_needed,
            with_payload=True,
            with_vectors=False,
        )

        if len(results) <= _PRIMARY_CLUSTER_COUNT:
            logger.info(
                "Not enough clusters for diversity injection "
                "(found %d, need %d for diversity).",
                len(results),
                total_needed,
            )
            return []

        # Take 4th-5th ranked clusters as diversity clusters
        diversity_clusters = []
        for hit in results[_PRIMARY_CLUSTER_COUNT:total_needed]:
            payload = hit.payload or {}
            cluster_index = payload.get("cluster_index")
            if cluster_index is not None:
                diversity_clusters.append(int(cluster_index))

        logger.info("Diversity clusters identified: %s", diversity_clusters)
        return diversity_clusters

    async def _inject_diversity(
        self,
        user_vector: list[float],
        cluster_priors: dict[int, float],
        user_price_profile: dict,
        primary_ranked: list[RankedCandidate],
        seen_ids: list[str],
        category: str | None,
        page_size: int,
    ) -> list[RankedCandidate]:
        """Inject diversity items into the ranked feed.

        Mandatory per PROJECT.md: 3/20 items from adjacent clusters.
        - Reserve 3 slots for diversity items
        - Take top (page_size - 3) from primary ranking
        - Top 3 from diversity ranking
        - Interleave evenly across the feed

        Args:
            user_vector: User's style vector.
            cluster_priors: Cluster ID -> prior probability mapping.
            user_price_profile: Dict with 'median' and 'std' keys.
            primary_ranked: Primary ranked candidates.
            seen_ids: Already seen product IDs.
            page_size: Target feed size.

        Returns:
            Diversity-injected list of RankedCandidate.
        """
        # Identify diversity clusters
        diversity_cluster_ids = await self._identify_diversity_clusters(user_vector)

        if not diversity_cluster_ids:
            return primary_ranked[:page_size]

        # Build filter for diversity candidates: must be in diversity clusters
        cluster_should = [
            FieldCondition(
                key="cluster_id",
                match=MatchValue(value=cid),
            )
            for cid in diversity_cluster_ids
        ]

        # Exclude seen IDs and primary candidate IDs from diversity pool
        primary_ids = {rc.product_id for rc in primary_ranked}
        all_exclude_ids = list(set(seen_ids) | primary_ids)

        must_not = []
        if all_exclude_ids:
            must_not.append(HasIdCondition(has_id=all_exclude_ids))

        must = None
        if category is not None:
            must = [
                FieldCondition(
                    key="category",
                    match=MatchValue(value=category),
                )
            ]

        diversity_filter = Filter(
            should=cluster_should, must=must, must_not=must_not or None
        )

        # Retrieve diversity candidates
        diversity_candidates = await self._qdrant.search(
            collection_name=self._settings.qdrant_collection,
            query_vector=user_vector,
            query_filter=diversity_filter,
            limit=_DIVERSITY_CANDIDATE_LIMIT,
            score_threshold=_SCORE_THRESHOLD,
            with_payload=True,
            with_vectors=False,
        )
        diversity_candidates = self._prepare_candidates_for_ranking(
            diversity_candidates,
            source="diversity",
        )

        if not diversity_candidates:
            logger.info("No diversity candidates found. Returning primary only.")
            return primary_ranked[:page_size]

        # Rank diversity candidates through the same pipeline
        diversity_ranked = rank_candidates(
            diversity_candidates, user_price_profile, cluster_priors
        )

        # Allocate slots: 3 diversity, rest primary
        actual_diversity_count = min(_DIVERSITY_COUNT, len(diversity_ranked))
        primary_count = page_size - actual_diversity_count

        primary_slice = primary_ranked[:primary_count]
        diversity_slice = diversity_ranked[:actual_diversity_count]

        # Interleave diversity items evenly
        return self._interleave_diversity(primary_slice, diversity_slice)

    @staticmethod
    def _interleave_diversity(
        primary: list[RankedCandidate],
        diversity: list[RankedCandidate],
    ) -> list[RankedCandidate]:
        """Spread diversity items evenly through the feed.

        Follows the same interleaving pattern as cold_start_service:
        divides primary items into chunks and inserts one diversity item
        after each chunk.
        """
        if not diversity:
            return primary
        if not primary:
            return diversity

        chunk_size = max(1, math.ceil(len(primary) / len(diversity)))
        merged: list[RankedCandidate] = []
        primary_index = 0
        diversity_index = 0

        while primary_index < len(primary) or diversity_index < len(diversity):
            next_primary = min(len(primary), primary_index + chunk_size)
            merged.extend(primary[primary_index:next_primary])
            primary_index = next_primary

            if diversity_index < len(diversity):
                merged.append(diversity[diversity_index])
                diversity_index += 1

        return merged
