"""Vector sync service for embedding products into Qdrant.

Handles the Qdrant side of product sync:
- Embed new/changed products and upsert vectors
- Remove vectors for deleted products
- Conditional re-clustering when enough products change

Reuses the existing EmbeddingService and QualityGateService instances
from the main ingestion pipeline — no new model instances are created.
"""

from __future__ import annotations

import asyncio
import logging
from io import BytesIO
from typing import TYPE_CHECKING

import httpx
from PIL import Image
from qdrant_client.models import PointIdsList, PointStruct

if TYPE_CHECKING:
    from qdrant_client import AsyncQdrantClient
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.features.ai.service.embedding_service import EmbeddingService
    from src.features.ai.service.quality_gate import QualityGateService
    from src.models.product import Product

logger = logging.getLogger(__name__)


class VectorSyncService:
    """Service for syncing product embeddings to Qdrant.

    Embeds new/changed products, removes deleted product vectors, and
    triggers conditional re-clustering when a significant fraction of
    products have changed.

    Args:
        embedding_service: Shared EmbeddingService instance (FashionSigLIP).
        quality_gate: Shared QualityGateService instance.
        qdrant_client: Async Qdrant client singleton.
        collection_name: Qdrant collection name. Defaults to "products".
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        quality_gate: QualityGateService,
        qdrant_client: AsyncQdrantClient,
        collection_name: str = "products",
    ) -> None:
        self.embedding_service = embedding_service
        self.quality_gate = quality_gate
        self.qdrant = qdrant_client
        self.collection_name = collection_name

    async def sync_products_to_qdrant(
        self,
        products: list[Product],
    ) -> tuple[int, int]:
        """Embed and upsert a list of products into Qdrant.

        Delegates to sync_products_batch for efficient batch processing.

        Args:
            products: Product model instances from PostgreSQL.

        Returns:
            Tuple of (success_count, failed_count).
        """
        return await self.sync_products_batch(products)

    async def sync_products_batch(
        self,
        products: list[Product],
        batch_size: int = 8,
    ) -> tuple[int, int]:
        """Embed and upsert products using concurrent fetching and batch embeddings.

        Pipeline:
        1. Pre-fetch all images concurrently (up to 4 at a time)
        2. Validate through quality gate
        3. Batch embed via EmbeddingService
        4. Bulk upsert to Qdrant

        Args:
            products: Product model instances from PostgreSQL.
            batch_size: Embedding batch size. Defaults to 8.

        Returns:
            Tuple of (success_count, failed_count).
        """
        if not products:
            return (0, 0)

        total = len(products)
        logger.info("Starting vector sync for %d products", total)

        # Step 1: Pre-fetch all images concurrently (semaphore limits to 4)
        fetch_semaphore = asyncio.Semaphore(4)
        fetched: list[tuple[Product, Image.Image, int]] = []
        fetch_failed = 0

        async def _fetch_one(
            product: Product,
        ) -> tuple[Product, Image.Image, int] | None:
            async with fetch_semaphore:
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(product.image_url)
                        response.raise_for_status()
                        data = response.content
                        image = Image.open(BytesIO(data))
                        return (product, image, len(data))
                except Exception as e:
                    logger.warning(
                        "Failed to fetch image for product %s (%s): %s",
                        product.id,
                        product.image_url,
                        e,
                    )
                    return None

        tasks = [_fetch_one(p) for p in products]
        results = await asyncio.gather(*tasks)

        for result in results:
            if result is not None:
                fetched.append(result)
            else:
                fetch_failed += 1

        if not fetched:
            logger.warning("All %d image fetches failed", total)
            return (0, total)

        # Step 2: Validate through quality gate
        validated: list[tuple[Product, Image.Image]] = []
        quality_failed = 0

        for product, image, file_size in fetched:
            quality_result = self.quality_gate.validate_image(image, file_size)
            if quality_result.passed:
                validated.append((product, image))
            else:
                quality_failed += 1
                logger.warning(
                    "Quality gate failed for product %s: %s",
                    product.id,
                    [issue.value for issue in quality_result.issues],
                )

        if not validated:
            logger.warning("All %d products failed quality gate", len(fetched))
            return (0, total)

        # Step 3: Batch embed
        images = [image for _, image in validated]
        try:
            embeddings = await self.embedding_service.get_embeddings_batch(
                images,
                batch_size=batch_size,
            )
        except Exception as e:
            logger.error("Batch embedding failed: %s", e)
            return (0, total)

        # Step 4: Bulk upsert to Qdrant
        points: list[PointStruct] = []
        for (product, _), embedding in zip(validated, embeddings):
            points.append(
                PointStruct(
                    id=str(product.id),
                    vector=embedding,
                    payload={
                        "product_id": str(product.id),
                        "store_id": product.store_id,
                        "price": float(product.price),
                        "created_at": product.created_at.isoformat(),
                    },
                )
            )

        try:
            await self.qdrant.upsert(
                collection_name=self.collection_name,
                points=points,
            )
        except Exception as e:
            logger.error("Qdrant bulk upsert failed: %s", e)
            return (0, total)

        success_count = len(points)
        failed_count = fetch_failed + quality_failed
        logger.info(
            "%d/%d products embedded and upserted to Qdrant (%d failed)",
            success_count,
            total,
            failed_count,
        )

        return (success_count, failed_count)

    async def remove_from_qdrant(self, product_ids: list[str]) -> None:
        """Remove vectors for products that have been deleted.

        Args:
            product_ids: List of product ID strings to remove from Qdrant.
        """
        if not product_ids:
            return

        await self.qdrant.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=product_ids),
        )
        logger.info("%d vectors removed from Qdrant", len(product_ids))

    async def should_recluster(
        self,
        changed_count: int,
        total_count: int,
        threshold: float,
    ) -> bool:
        """Check whether re-clustering should be triggered.

        Args:
            changed_count: Number of products that changed.
            total_count: Total number of products.
            threshold: Fraction threshold (e.g., 0.05 for 5%).

        Returns:
            True if the changed ratio exceeds the threshold.
        """
        ratio = changed_count / max(total_count, 1)
        should = ratio > threshold
        logger.info(
            "Re-cluster check: %d/%d = %.1f%% (threshold: %.1f%%) -> %s",
            changed_count,
            total_count,
            ratio * 100,
            threshold * 100,
            "yes" if should else "no",
        )
        return should

    async def trigger_recluster(self, session: AsyncSession) -> None:
        """Trigger a full cluster rebuild.

        Instantiates ClusteringService with the existing Qdrant client and
        calls rebuild_clusters. CPU-intensive sklearn operations are handled
        internally by ClusteringService via asyncio.to_thread.

        Args:
            session: Async SQLAlchemy session for persisting cluster metadata.
        """
        from src.core.config import get_settings
        from src.features.clustering.service.clustering_service import (
            ClusteringService,
        )

        settings = get_settings()
        clustering_service = ClusteringService(
            qdrant_client=self.qdrant,
            settings=settings,
        )
        await clustering_service.rebuild_clusters(session)
        logger.info("Re-clustering complete")
