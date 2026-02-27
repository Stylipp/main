"""ClusteringService: K-means clustering engine for style cluster generation.

Processes all product embeddings from Qdrant into style clusters using K-means
with automatic optimal k determination via silhouette analysis.

CPU-intensive operations (find_optimal_k, run_kmeans) are offloaded to threads
via asyncio.to_thread to avoid blocking the event loop.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import numpy as np
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings
from src.features.clustering.service.cluster_repository import ClusterRepository

logger = logging.getLogger(__name__)

# Batch size for Qdrant scroll operations
_SCROLL_BATCH_SIZE = 100
# Batch size for Qdrant payload updates
_PAYLOAD_BATCH_SIZE = 100


class ClusteringService:
    """K-means clustering engine for generating style clusters.

    Orchestrates the full pipeline: fetch embeddings -> determine optimal k ->
    run K-means -> persist results to PostgreSQL and Qdrant.

    Args:
        qdrant_client: Async Qdrant client instance.
        settings: Application settings with clustering config.
    """

    def __init__(self, qdrant_client: AsyncQdrantClient, settings: Settings) -> None:
        self._qdrant = qdrant_client
        self._settings = settings
        self._repository = ClusterRepository()

    async def fetch_all_embeddings(self) -> tuple[list[str], np.ndarray]:
        """Scroll ALL product points from the Qdrant products collection.

        Returns:
            Tuple of (point_ids, embeddings_matrix) where point_ids is a list
            of string point IDs and embeddings_matrix is a numpy array of shape
            (n_samples, 768).
        """
        point_ids: list[str] = []
        embeddings: list[list[float]] = []

        offset = None
        while True:
            results, next_offset = await self._qdrant.scroll(
                collection_name=self._settings.qdrant_collection,
                limit=_SCROLL_BATCH_SIZE,
                offset=offset,
                with_vectors=True,
            )

            if not results:
                break

            for point in results:
                point_ids.append(str(point.id))
                embeddings.append(point.vector)

            if next_offset is None:
                break
            offset = next_offset

        logger.info(
            "Fetched %d product embeddings from Qdrant collection '%s'",
            len(point_ids),
            self._settings.qdrant_collection,
        )

        return point_ids, np.array(embeddings, dtype=np.float32)

    def find_optimal_k(self, embeddings: np.ndarray) -> int:
        """Determine optimal number of clusters using silhouette analysis.

        Tests k values from min_clusters to min(max_clusters, n_samples // 2)
        and returns the k with the highest silhouette score.

        For small catalogs (n_samples < min_clusters * 2), adjusts min k to
        n_samples // 5 to avoid degenerate clustering.

        Args:
            embeddings: Numpy array of shape (n_samples, 768).

        Returns:
            Optimal number of clusters (k).
        """
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score

        n_samples = len(embeddings)
        min_k = self._settings.min_clusters
        max_k = min(self._settings.max_clusters, n_samples // 2)

        # Handle small catalogs
        if n_samples < min_k * 2:
            min_k = max(2, n_samples // 5)
            logger.warning(
                "Small catalog (%d products). Adjusted min_k to %d",
                n_samples,
                min_k,
            )

        # Ensure we have a valid range
        if min_k >= max_k:
            max_k = min_k + 1

        best_k = min_k
        best_score = -1.0

        logger.info("Testing k values from %d to %d", min_k, max_k)

        for k in range(min_k, max_k + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels)

            logger.info("k=%d, silhouette_score=%.4f", k, score)

            if score > best_score:
                best_score = score
                best_k = k

        logger.info("Optimal k=%d with silhouette_score=%.4f", best_k, best_score)

        return best_k

    def run_kmeans(
        self, embeddings: np.ndarray, k: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """Run K-means clustering with the given k.

        Args:
            embeddings: Numpy array of shape (n_samples, 768).
            k: Number of clusters.

        Returns:
            Tuple of (centroids, labels) where centroids has shape (k, 768)
            and labels has shape (n_samples,).
        """
        from sklearn.cluster import KMeans

        logger.info("Running K-means with k=%d on %d samples", k, len(embeddings))

        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        centroids = kmeans.cluster_centers_

        logger.info("K-means complete. %d centroids generated.", len(centroids))

        return centroids, labels

    async def store_results(
        self,
        point_ids: list[str],
        labels: np.ndarray,
        centroids: np.ndarray,
        session: AsyncSession,
    ) -> None:
        """Persist clustering results to PostgreSQL and Qdrant.

        a) Upsert cluster metadata to PostgreSQL (cluster_index, product_count,
           prior_probability for each cluster).
        b) Upsert centroid vectors to Qdrant "style_clusters" collection.
        c) Update product points in Qdrant "products" collection with
           cluster_id in payload.

        Args:
            point_ids: List of Qdrant point IDs for products.
            labels: Cluster labels for each product, shape (n_samples,).
            centroids: Cluster centroids, shape (k, 768).
            session: Async SQLAlchemy session.
        """
        n_samples = len(point_ids)
        k = len(centroids)

        # --- (a) Upsert cluster metadata to PostgreSQL ---
        cluster_data: list[dict[str, Any]] = []
        for cluster_idx in range(k):
            count = int(np.sum(labels == cluster_idx))
            cluster_data.append(
                {
                    "cluster_index": cluster_idx,
                    "product_count": count,
                    "prior_probability": count / n_samples if n_samples > 0 else 0.0,
                    "status": "active",
                }
            )

        await self._repository.upsert_clusters(session, cluster_data)
        logger.info("Stored %d cluster records in PostgreSQL", k)

        # --- (b) Upsert centroid vectors to Qdrant style_clusters collection ---
        centroid_points = [
            PointStruct(
                id=cluster_idx,
                vector=centroids[cluster_idx].tolist(),
                payload={
                    "cluster_index": cluster_idx,
                    "product_count": int(np.sum(labels == cluster_idx)),
                    "prior_probability": (
                        float(np.sum(labels == cluster_idx) / n_samples)
                        if n_samples > 0
                        else 0.0
                    ),
                },
            )
            for cluster_idx in range(k)
        ]

        await self._qdrant.upsert(
            collection_name=self._settings.cluster_collection,
            points=centroid_points,
        )
        logger.info(
            "Stored %d centroid vectors in Qdrant collection '%s'",
            k,
            self._settings.cluster_collection,
        )

        # --- (c) Update product points with cluster_id in Qdrant ---
        for batch_start in range(0, n_samples, _PAYLOAD_BATCH_SIZE):
            batch_end = min(batch_start + _PAYLOAD_BATCH_SIZE, n_samples)
            batch_ids = point_ids[batch_start:batch_end]
            batch_labels = labels[batch_start:batch_end]

            for pid, label in zip(batch_ids, batch_labels):
                await self._qdrant.set_payload(
                    collection_name=self._settings.qdrant_collection,
                    payload={"cluster_id": int(label)},
                    points=[pid],
                )

        logger.info("Updated cluster_id payload for %d products in Qdrant", n_samples)

    async def rebuild_clusters(self, session: AsyncSession) -> dict[str, Any]:
        """Orchestrate full clustering pipeline.

        Fetches all product embeddings, determines optimal k, runs K-means,
        and persists all results.

        Args:
            session: Async SQLAlchemy session.

        Returns:
            Stats dict with k, silhouette_score, product_count, cluster_sizes.
        """
        from sklearn.metrics import silhouette_score

        # Step 1: Fetch all embeddings
        logger.info("Starting cluster rebuild...")
        point_ids, embeddings = await self.fetch_all_embeddings()

        if len(point_ids) == 0:
            logger.warning("No product embeddings found. Skipping clustering.")
            return {
                "k": 0,
                "silhouette_score": 0.0,
                "product_count": 0,
                "cluster_sizes": [],
            }

        # Step 2: Find optimal k (CPU-intensive, run in thread)
        logger.info("Finding optimal k...")
        optimal_k = await asyncio.to_thread(self.find_optimal_k, embeddings)

        # Step 3: Run K-means (CPU-intensive, run in thread)
        logger.info("Running K-means with k=%d...", optimal_k)
        centroids, labels = await asyncio.to_thread(
            self.run_kmeans, embeddings, optimal_k
        )

        # Compute silhouette score for final result
        final_score = await asyncio.to_thread(silhouette_score, embeddings, labels)

        # Step 4: Store results
        logger.info("Storing clustering results...")
        await self.store_results(point_ids, labels, centroids, session)

        # Compute cluster sizes
        cluster_sizes = [int(np.sum(labels == i)) for i in range(optimal_k)]

        stats = {
            "k": optimal_k,
            "silhouette_score": float(final_score),
            "product_count": len(point_ids),
            "cluster_sizes": cluster_sizes,
        }

        logger.info("Cluster rebuild complete: %s", stats)
        return stats
