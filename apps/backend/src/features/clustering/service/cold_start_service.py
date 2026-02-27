"""ColdStartService: Maps user photo embeddings to nearest style clusters
and retrieves initial product recommendations with diversity injection.

When a new user uploads 1-2 outfit photos during onboarding, this service:
1. Averages their photo embeddings into a single style vector
2. Finds the nearest pre-computed style clusters in Qdrant
3. Retrieves products from those clusters with mandatory diversity injection

Diversity injection (3/20 items from adjacent clusters) is MANDATORY per
PROJECT.md to prevent echo chambers. This is not configurable.
"""

from __future__ import annotations

import logging
import math

import numpy as np
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from src.core.config import Settings
from src.features.clustering.schemas.schemas import ColdStartMatch, ColdStartResponse

logger = logging.getLogger(__name__)

# Mandatory diversity injection: 3 out of 20 items from adjacent clusters.
# Per PROJECT.md: "mandatory diversity injection (3/20 items from adjacent clusters)"
_DIVERSITY_COUNT = 3
_PRIMARY_COUNT_DEFAULT = 17  # feed_size - _DIVERSITY_COUNT for default feed_size=20
_PRIMARY_CLUSTER_COUNT = 3
_DIVERSITY_CLUSTER_COUNT = 2

# Batch size for Qdrant scroll operations
_SCROLL_BATCH_SIZE = 100


class ColdStartService:
    """Matches user photo embeddings to nearest clusters and builds cold-start feed.

    Args:
        qdrant_client: Async Qdrant client instance.
        settings: Application settings with clustering config.
    """

    def __init__(self, qdrant_client: AsyncQdrantClient, settings: Settings) -> None:
        self._qdrant = qdrant_client
        self._settings = settings

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
        avg_embedding = np.mean(np.array(embeddings, dtype=np.float32), axis=0).tolist()

        # Search style_clusters collection for nearest centroids
        results = await self._qdrant.search(
            collection_name=self._settings.cluster_collection,
            query_vector=avg_embedding,
            limit=top_k,
        )

        clusters = []
        for hit in results:
            clusters.append(
                {
                    "cluster_index": hit.payload.get("cluster_index", hit.id),
                    "score": hit.score,
                    "product_count": hit.payload.get("product_count", 0),
                }
            )

        logger.info(
            "Found %d nearest clusters for %d input embeddings",
            len(clusters),
            len(embeddings),
        )

        return clusters

    async def get_products_by_cluster(
        self, cluster_index: int, limit: int = 20
    ) -> list[dict]:
        """Retrieve products from a specific cluster.

        Scrolls the "products" Qdrant collection filtered by cluster_id payload
        matching the given cluster_index.

        Args:
            cluster_index: The cluster label to filter by.
            limit: Maximum number of products to return.

        Returns:
            List of dicts with keys: product_id, payload, score (None for scroll).
        """
        records, _next_offset = await self._qdrant.scroll(
            collection_name=self._settings.qdrant_collection,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="cluster_id",
                        match=MatchValue(value=cluster_index),
                    )
                ]
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        products = []
        for point in records:
            products.append(
                {
                    "product_id": str(point.id),
                    "payload": point.payload or {},
                }
            )

        logger.info(
            "Retrieved %d products from cluster %d", len(products), cluster_index
        )

        return products

    async def get_cold_start_feed(
        self, embeddings: list[list[float]], feed_size: int = 20
    ) -> ColdStartResponse:
        """Build the cold-start product feed with mandatory diversity injection.

        Orchestrates the full cold-start flow:
        a) Find top 3 nearest clusters (primary clusters).
        b) Find 2 adjacent clusters ranked 4th-5th (diversity clusters).
        c) Allocate: (feed_size - 3) primary items + 3 diversity items.
           Primary items distributed proportionally to similarity score.
        d) Retrieve products from each cluster via scroll with cluster_id filter.
        e) Build ColdStartResponse with is_diversity flag on diversity items.

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

        # --- Fetch primary cluster products ---
        primary_matches = await self._fetch_proportional_products(
            clusters=primary_clusters,
            total_items=primary_count,
            is_diversity=False,
        )

        # --- Fetch diversity cluster products ---
        diversity_matches = await self._fetch_proportional_products(
            clusters=diversity_clusters,
            total_items=diversity_count,
            is_diversity=True,
        )

        # Combine: primary items first, then diversity items interleaved at end
        all_matches = primary_matches + diversity_matches

        return ColdStartResponse(
            matches=all_matches,
            primary_clusters=primary_indices,
            diversity_clusters=diversity_indices,
            total_matches=len(all_matches),
        )

    async def _fetch_proportional_products(
        self,
        clusters: list[dict],
        total_items: int,
        is_diversity: bool,
    ) -> list[ColdStartMatch]:
        """Fetch products from clusters proportional to their similarity scores.

        Distributes the total_items budget across clusters weighted by their
        similarity score. Each cluster gets at least 1 item (if budget allows).

        Args:
            clusters: List of cluster dicts with cluster_index and score.
            total_items: Total number of products to fetch.
            is_diversity: Whether these are diversity cluster items.

        Returns:
            List of ColdStartMatch items.
        """
        if not clusters or total_items <= 0:
            return []

        # Calculate proportional allocation based on similarity scores
        total_score = sum(c["score"] for c in clusters)
        allocations: list[int] = []

        if total_score > 0:
            for cluster in clusters:
                proportion = cluster["score"] / total_score
                alloc = max(1, math.floor(proportion * total_items))
                allocations.append(alloc)
        else:
            # Equal distribution fallback
            per_cluster = max(1, total_items // len(clusters))
            allocations = [per_cluster] * len(clusters)

        # Adjust allocations to match total_items exactly
        current_total = sum(allocations)
        if current_total < total_items:
            # Add remaining to highest-scoring cluster
            allocations[0] += total_items - current_total
        elif current_total > total_items:
            # Remove excess from lowest-scoring cluster
            excess = current_total - total_items
            for i in range(len(allocations) - 1, -1, -1):
                reduction = min(excess, allocations[i] - 1)
                allocations[i] -= reduction
                excess -= reduction
                if excess <= 0:
                    break

        # Fetch products from each cluster
        matches: list[ColdStartMatch] = []
        for cluster, alloc in zip(clusters, allocations):
            if alloc <= 0:
                continue

            products = await self.get_products_by_cluster(
                cluster_index=cluster["cluster_index"],
                limit=alloc,
            )

            for product in products:
                matches.append(
                    ColdStartMatch(
                        product_id=product["product_id"],
                        score=cluster["score"],
                        cluster_index=cluster["cluster_index"],
                        is_diversity=is_diversity,
                    )
                )

        return matches
