"""ColdStartService: Maps user photo embeddings to a similarity-ranked cold-start feed.

When a new user uploads 1-2 outfit photos during onboarding, this service:
1. Averages their photo embeddings into a single style vector
2. Finds the nearest pre-computed style clusters in Qdrant
3. Uses those clusters as retrieval filters while ranking actual products
   by cosine similarity to the user's averaged vector
4. Injects diversity items from adjacent clusters into the final sequence

Diversity injection is MANDATORY per PROJECT.md to prevent echo chambers.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Iterable

import numpy as np
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from src.core.config import Settings
from src.features.clustering.schemas.schemas import ColdStartMatch, ColdStartResponse

logger = logging.getLogger(__name__)

# Mandatory diversity injection: 3 items from adjacent clusters.
_DIVERSITY_COUNT = 3
_PRIMARY_CLUSTER_COUNT = 3
_DIVERSITY_CLUSTER_COUNT = 2
_SEARCH_OVERSAMPLE_FACTOR = 4
_MIN_SEARCH_LIMIT = 24


class ColdStartService:
    """Matches user photo embeddings to nearest clusters and builds cold-start feed.

    Args:
        qdrant_client: Async Qdrant client instance.
        settings: Application settings with clustering config.
    """

    def __init__(self, qdrant_client: AsyncQdrantClient, settings: Settings) -> None:
        self._qdrant = qdrant_client
        self._settings = settings

    @staticmethod
    def _average_embeddings(embeddings: list[list[float]]) -> list[float]:
        """Average multiple photo embeddings into a single query vector."""
        return np.mean(np.array(embeddings, dtype=np.float32), axis=0).tolist()

    async def find_nearest_clusters(
        self, embeddings: list[list[float]], top_k: int = 5
    ) -> list[dict]:
        """Find nearest style clusters for given photo embeddings.

        Averages the input embeddings (if multiple photos, compute mean vector),
        then searches the "style_clusters" Qdrant collection for the top_k
        nearest centroids by cosine similarity.

        Args:
            embeddings: List of 1-2 photo embedding vectors (768-dim each).
            top_k: Number of nearest clusters to return.

        Returns:
            List of dicts with keys: cluster_index, score, product_count,
            sorted by score descending.
        """
        # Average embeddings into a single style vector
        avg_embedding = self._average_embeddings(embeddings)

        # Search style_clusters collection for nearest centroids
        response = await self._qdrant.query_points(
            collection_name=self._settings.cluster_collection,
            query=avg_embedding,
            limit=top_k,
        )
        results = response.points

        clusters = []
        for hit in results:
            payload = hit.payload or {}
            clusters.append(
                {
                    "cluster_index": payload.get("cluster_index", hit.id),
                    "score": hit.score,
                    "product_count": payload.get("product_count", 0),
                }
            )

        logger.info(
            "Found %d nearest clusters for %d input embeddings",
            len(clusters),
            len(embeddings),
        )

        return clusters

    @staticmethod
    def _build_cluster_filter(cluster_indices: list[int]) -> Filter | None:
        """Create an OR filter for a set of cluster ids."""
        if not cluster_indices:
            return None

        return Filter(
            should=[
                FieldCondition(
                    key="cluster_id",
                    match=MatchValue(value=int(cluster_index)),
                )
                for cluster_index in cluster_indices
            ]
        )

    async def _search_products(
        self,
        query_vector: list[float],
        limit: int,
        cluster_indices: list[int] | None = None,
    ) -> list[dict]:
        """Search products by vector similarity, optionally constrained to clusters."""
        response = await self._qdrant.query_points(
            collection_name=self._settings.qdrant_collection,
            query=query_vector,
            query_filter=self._build_cluster_filter(cluster_indices or []),
            limit=max(1, limit),
            with_payload=True,
            with_vectors=False,
        )
        results = response.points

        products = []
        for hit in results:
            payload = hit.payload or {}
            cluster_index = payload.get("cluster_id")
            products.append(
                {
                    "product_id": str(hit.id),
                    "score": float(hit.score),
                    "cluster_index": (
                        int(cluster_index) if cluster_index is not None else -1
                    ),
                }
            )

        logger.info(
            "Vector search returned %d products%s",
            len(products),
            (
                f" for clusters {cluster_indices}"
                if cluster_indices
                else " across the full catalog"
            ),
        )

        return products

    @staticmethod
    def _to_matches(
        products: Iterable[dict],
        limit: int,
        is_diversity: bool,
        exclude_ids: set[str] | None = None,
    ) -> list[ColdStartMatch]:
        """Transform search hits into API matches with deduplication."""
        if limit <= 0:
            return []

        seen = set(exclude_ids or set())
        matches: list[ColdStartMatch] = []

        for product in products:
            product_id = product["product_id"]
            if product_id in seen:
                continue

            seen.add(product_id)
            matches.append(
                ColdStartMatch(
                    product_id=product_id,
                    score=product["score"],
                    cluster_index=product["cluster_index"],
                    is_diversity=is_diversity,
                )
            )

            if len(matches) >= limit:
                break

        return matches

    @staticmethod
    def _interleave_diversity(
        primary_matches: list[ColdStartMatch],
        diversity_matches: list[ColdStartMatch],
    ) -> list[ColdStartMatch]:
        """Spread diversity items through the feed instead of appending them all last."""
        if not diversity_matches:
            return primary_matches
        if not primary_matches:
            return diversity_matches

        chunk_size = max(1, math.ceil(len(primary_matches) / len(diversity_matches)))
        merged: list[ColdStartMatch] = []
        primary_index = 0
        diversity_index = 0

        while primary_index < len(primary_matches) or diversity_index < len(
            diversity_matches
        ):
            next_primary_index = min(len(primary_matches), primary_index + chunk_size)
            merged.extend(primary_matches[primary_index:next_primary_index])
            primary_index = next_primary_index

            if diversity_index < len(diversity_matches):
                merged.append(diversity_matches[diversity_index])
                diversity_index += 1

        return merged

    async def get_cold_start_feed(
        self, embeddings: list[list[float]], feed_size: int = 20
    ) -> ColdStartResponse:
        """Build the cold-start product feed with mandatory diversity injection.

        Orchestrates the full cold-start flow:
        a) Find top 3 nearest clusters (primary clusters).
        b) Find 2 adjacent clusters ranked 4th-5th (diversity clusters).
        c) Allocate: (feed_size - 3) primary items + 3 diversity items.
           Primary items are ranked by product-vector similarity.
        d) Retrieve products via vector search within those cluster groups.
        e) Interleave diversity items into the final list.

        Diversity injection is MANDATORY (per PROJECT.md). Always inject exactly
        3 items from adjacent clusters to prevent echo chambers.

        Args:
            embeddings: List of 1-2 photo embedding vectors (768-dim each).
            feed_size: Total number of items in the feed (default 20).

        Returns:
            ColdStartResponse with matches, cluster info, and total count.
        """
        # Total clusters needed: 3 primary + 2 diversity = 5
        total_clusters_needed = _PRIMARY_CLUSTER_COUNT + _DIVERSITY_CLUSTER_COUNT
        nearest = await self.find_nearest_clusters(
            embeddings, top_k=total_clusters_needed
        )
        avg_embedding = self._average_embeddings(embeddings)

        if not nearest:
            logger.warning("No clusters found. Returning empty cold-start feed.")
            return ColdStartResponse(
                matches=[],
                primary_clusters=[],
                diversity_clusters=[],
                total_matches=0,
            )

        # Split into primary (top 3) and diversity (4th-5th) clusters
        primary_clusters = nearest[:_PRIMARY_CLUSTER_COUNT]
        diversity_clusters = nearest[_PRIMARY_CLUSTER_COUNT:total_clusters_needed]

        primary_indices = [c["cluster_index"] for c in primary_clusters]
        diversity_indices = [c["cluster_index"] for c in diversity_clusters]

        # Allocate item counts
        diversity_count = min(_DIVERSITY_COUNT, feed_size)
        primary_count = feed_size - diversity_count

        primary_products = await self._search_products(
            query_vector=avg_embedding,
            cluster_indices=primary_indices,
            limit=max(_MIN_SEARCH_LIMIT, primary_count * _SEARCH_OVERSAMPLE_FACTOR),
        )
        primary_matches = self._to_matches(
            products=primary_products,
            limit=primary_count,
            is_diversity=False,
        )

        diversity_products = await self._search_products(
            query_vector=avg_embedding,
            cluster_indices=diversity_indices,
            limit=max(_MIN_SEARCH_LIMIT, diversity_count * _SEARCH_OVERSAMPLE_FACTOR),
        )
        diversity_matches = self._to_matches(
            products=diversity_products,
            limit=diversity_count,
            is_diversity=True,
            exclude_ids={match.product_id for match in primary_matches},
        )

        all_matches = self._interleave_diversity(primary_matches, diversity_matches)

        remaining_slots = feed_size - len(all_matches)
        if remaining_slots > 0:
            fallback_products = await self._search_products(
                query_vector=avg_embedding,
                limit=max(
                    _MIN_SEARCH_LIMIT, remaining_slots * _SEARCH_OVERSAMPLE_FACTOR
                ),
            )
            fallback_matches = self._to_matches(
                products=fallback_products,
                limit=remaining_slots,
                is_diversity=False,
                exclude_ids={match.product_id for match in all_matches},
            )
            all_matches.extend(fallback_matches)

        return ColdStartResponse(
            matches=all_matches,
            primary_clusters=primary_indices,
            diversity_clusters=diversity_indices,
            total_matches=len(all_matches),
        )
