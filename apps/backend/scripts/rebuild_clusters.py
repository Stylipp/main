#!/usr/bin/env python3
"""
Cluster rebuild management script.

Triggers a full K-means clustering rebuild of the product catalog.
Standalone async script that creates its own DB session and Qdrant client
(does NOT depend on FastAPI/main.py).

Usage:
    cd apps/backend
    python -m scripts.rebuild_clusters
    python -m scripts.rebuild_clusters --min-k 5 --max-k 50
    python -m scripts.rebuild_clusters --dry-run
"""

import argparse
import asyncio
import logging
import sys

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import get_settings
from src.core.qdrant import ensure_cluster_collection, get_qdrant_client
from src.features.clustering.service.clustering_service import ClusteringService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description="Rebuild style clusters from product embeddings in Qdrant."
    )
    parser.add_argument(
        "--min-k",
        type=int,
        default=settings.min_clusters,
        help=f"Minimum number of clusters to test (default: {settings.min_clusters})",
    )
    parser.add_argument(
        "--max-k",
        type=int,
        default=settings.max_clusters,
        help=f"Maximum number of clusters to test (default: {settings.max_clusters})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show stats without persisting results to DB/Qdrant",
    )

    return parser.parse_args()


async def main() -> None:
    """Run the cluster rebuild pipeline."""
    args = parse_args()
    settings = get_settings()

    # Override clustering settings from CLI args
    settings.min_clusters = args.min_k
    settings.max_clusters = args.max_k

    logger.info("=" * 60)
    logger.info("CLUSTER REBUILD")
    logger.info("=" * 60)
    logger.info("Min k: %d", args.min_k)
    logger.info("Max k: %d", args.max_k)
    logger.info("Dry run: %s", args.dry_run)
    logger.info("=" * 60)

    # Initialize Qdrant client and ensure collection exists
    await ensure_cluster_collection()
    qdrant_client = await get_qdrant_client()

    # Initialize database session
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create clustering service
    service = ClusteringService(qdrant_client=qdrant_client, settings=settings)

    try:
        if args.dry_run:
            # Dry run: fetch embeddings and find optimal k without persisting
            logger.info("DRY RUN: Fetching embeddings...")
            point_ids, embeddings = await service.fetch_all_embeddings()

            if len(point_ids) == 0:
                logger.error(
                    "No products found in Qdrant collection '%s'. "
                    "Run product ingestion first (e.g., python -m scripts.seed_bootstrap).",
                    settings.qdrant_collection,
                )
                sys.exit(1)

            logger.info("Found %d product embeddings", len(point_ids))
            logger.info("DRY RUN: Finding optimal k (this may take a while)...")

            optimal_k = await asyncio.to_thread(service.find_optimal_k, embeddings)

            logger.info("DRY RUN: Running K-means with k=%d...", optimal_k)
            centroids, labels = await asyncio.to_thread(
                service.run_kmeans, embeddings, optimal_k
            )

            # Compute silhouette score
            from sklearn.metrics import silhouette_score

            score = await asyncio.to_thread(silhouette_score, embeddings, labels)

            # Print cluster size distribution
            import numpy as np

            cluster_sizes = {
                int(i): int(np.sum(labels == i)) for i in range(optimal_k)
            }

            logger.info("")
            logger.info("=" * 60)
            logger.info("DRY RUN RESULTS (nothing persisted)")
            logger.info("=" * 60)
            logger.info("Optimal k: %d", optimal_k)
            logger.info("Silhouette score: %.4f", score)
            logger.info("Total products: %d", len(point_ids))
            logger.info("Cluster sizes: %s", cluster_sizes)
            logger.info(
                "Min cluster: %d, Max cluster: %d, Avg: %.1f",
                min(cluster_sizes.values()),
                max(cluster_sizes.values()),
                np.mean(list(cluster_sizes.values())),
            )
            logger.info("=" * 60)
            logger.info("To persist results, run without --dry-run")
        else:
            # Full rebuild: run the complete pipeline
            async with async_session() as session:
                stats = await service.rebuild_clusters(session)

                if stats["k"] == 0:
                    logger.error(
                        "No products found in Qdrant collection '%s'. "
                        "Run product ingestion first (e.g., python -m scripts.seed_bootstrap).",
                        settings.qdrant_collection,
                    )
                    sys.exit(1)

                await session.commit()

            logger.info("")
            logger.info("=" * 60)
            logger.info("REBUILD COMPLETE")
            logger.info("=" * 60)
            logger.info("Optimal k: %d", stats["k"])
            logger.info("Silhouette score: %.4f", stats["silhouette_score"])
            logger.info("Total products: %d", stats["product_count"])
            logger.info("Cluster sizes: %s", stats["cluster_sizes"])
            logger.info("=" * 60)
    except Exception:
        logger.exception("Cluster rebuild failed")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
