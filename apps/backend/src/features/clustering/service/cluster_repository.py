"""Repository for StyleCluster CRUD operations in PostgreSQL."""

from __future__ import annotations

import logging

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.cluster import StyleCluster

logger = logging.getLogger(__name__)


class ClusterRepository:
    """Handles all PostgreSQL operations for style clusters."""

    async def get_all_clusters(self, session: AsyncSession) -> list[StyleCluster]:
        """Fetch all active style clusters.

        Args:
            session: Async SQLAlchemy session.

        Returns:
            List of all StyleCluster records.
        """
        result = await session.execute(
            select(StyleCluster).order_by(StyleCluster.cluster_index)
        )
        return list(result.scalars().all())

    async def upsert_clusters(self, session: AsyncSession, clusters: list[dict]) -> int:
        """Bulk upsert cluster metadata (delete old + insert new).

        This is a full replacement strategy: all existing clusters are removed
        and the new set is inserted. This ensures consistency after a full
        re-clustering run.

        Args:
            session: Async SQLAlchemy session.
            clusters: List of dicts with keys: cluster_index, product_count,
                      prior_probability, status.

        Returns:
            Number of clusters inserted.
        """
        # Delete all existing clusters
        await session.execute(delete(StyleCluster))

        # Insert new clusters
        new_clusters = [StyleCluster(**cluster_data) for cluster_data in clusters]
        session.add_all(new_clusters)
        await session.flush()

        logger.info("Upserted %d style clusters in PostgreSQL", len(new_clusters))
        return len(new_clusters)

    async def get_cluster_by_index(
        self, session: AsyncSession, cluster_index: int
    ) -> StyleCluster | None:
        """Fetch a single cluster by its cluster_index.

        Args:
            session: Async SQLAlchemy session.
            cluster_index: The K-means cluster label.

        Returns:
            The StyleCluster if found, else None.
        """
        result = await session.execute(
            select(StyleCluster).where(StyleCluster.cluster_index == cluster_index)
        )
        return result.scalar_one_or_none()
