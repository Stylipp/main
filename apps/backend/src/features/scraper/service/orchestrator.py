"""Top-level orchestrator for the automated scraper pipeline.

Coordinates the full scrape-diff-sync pipeline per store and runs
multiple stores in parallel. Ties together sitemap fetch, product
scrape, change detection, database sync, WooCommerce sync, vector
sync, and conditional re-clustering into a single invocable pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import Settings
from src.core.qdrant import get_qdrant_client
from src.features.ai.service.embedding_service import EmbeddingService
from src.features.ai.service.quality_gate import QualityGateService
from src.features.products.service.woocommerce_client import WooCommerceClient
from src.features.scraper.config.stores import (
    StoreConfig,
    load_store_configs,
)
from src.features.scraper.schemas.schemas import (
    PipelineResult,
    ScrapeResult,
    SyncResult,
)
from src.features.scraper.service.change_detection import ChangeDetectionService
from src.features.scraper.service.db_sync_service import DbSyncService
from src.features.scraper.service.product_scraper import ProductScraper
from src.features.scraper.service.sitemap_service import SitemapService
from src.features.scraper.service.vector_sync_service import VectorSyncService
from src.models.product import Product

logger = logging.getLogger(__name__)


class ScraperOrchestrator:
    """Coordinates the full scrape-diff-sync pipeline for stores.

    Runs each store through: sitemap fetch -> product scrape ->
    change detection -> database sync -> WooCommerce sync ->
    vector sync. Multiple stores run concurrently via asyncio.gather.

    Args:
        settings: Application settings instance.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def run_store(
        self, store: StoreConfig, *, dry_run: bool = False
    ) -> tuple[ScrapeResult, SyncResult | None]:
        """Execute the full pipeline for a single store.

        Steps:
            1. Initialize services (sitemap, scraper, change detection)
            2. Fetch sitemap URLs
            3. Scrape product pages sequentially (rate-limited)
            4. Detect changes against previous run
            5. Sync changes to PostgreSQL, WooCommerce, and Qdrant (unless dry_run)
            6. Update change detection hashes

        Args:
            store: Store configuration to scrape.
            dry_run: If True, skip all sync operations (steps 5-6).

        Returns:
            Tuple of (ScrapeResult, SyncResult or None).
        """
        start = time.monotonic()

        try:
            # Step 1: Initialize services
            sitemap_service = SitemapService()
            product_scraper = ProductScraper()
            change_detection = ChangeDetectionService(self.settings.scraper_sqlite_path)
            await change_detection.initialize()

            # Step 2: Fetch sitemap
            urls = await sitemap_service.fetch_product_urls(store)
            logger.info("Found %d product URLs for %s", len(urls), store.name)

            if not urls:
                duration = time.monotonic() - start
                return (
                    ScrapeResult(
                        store_id=store.id,
                        total_urls=0,
                        total_scraped=0,
                        total_failed=0,
                        total_new=0,
                        total_changed=0,
                        total_removed=0,
                        duration_seconds=round(duration, 2),
                    ),
                    None,
                )

            # Step 3: Scrape products
            products = await product_scraper.scrape_batch(urls, store)
            logger.info(
                "Scraped %d/%d products from %s",
                len(products),
                len(urls),
                store.name,
            )

            # Step 4: Detect changes
            report = await change_detection.detect_changes(store.id, products)
            logger.info(
                "Changes for %s: %d new, %d changed, %d removed, %d unchanged",
                store.name,
                len(report.new),
                len(report.changed),
                len(report.removed_ids),
                report.unchanged_count,
            )

            scrape_result = ScrapeResult(
                store_id=store.id,
                total_urls=len(urls),
                total_scraped=len(products),
                total_failed=len(urls) - len(products),
                total_new=len(report.new),
                total_changed=len(report.changed),
                total_removed=len(report.removed_ids),
                duration_seconds=round(time.monotonic() - start, 2),
            )

            # Step 5: Sync to systems (skip if dry_run or no changes)
            if dry_run:
                logger.info(
                    "[DRY RUN] Would sync %d new, %d changed products for %s",
                    len(report.new),
                    len(report.changed),
                    store.name,
                )
                return scrape_result, None

            has_changes = report.new or report.changed or report.removed_ids
            if not has_changes:
                return scrape_result, None

            sync_result = await self._sync_changes(store, report, change_detection)
            scrape_result.duration_seconds = round(time.monotonic() - start, 2)

            return scrape_result, sync_result

        except Exception as exc:
            duration = time.monotonic() - start
            logger.error(
                "Pipeline failed for store %s: %s",
                store.name,
                exc,
                exc_info=True,
            )
            return (
                ScrapeResult(
                    store_id=store.id,
                    total_urls=0,
                    total_scraped=0,
                    total_failed=0,
                    total_new=0,
                    total_changed=0,
                    total_removed=0,
                    duration_seconds=round(duration, 2),
                    errors=[str(exc)],
                ),
                None,
            )

    async def _sync_changes(
        self,
        store: StoreConfig,
        report,
        change_detection: ChangeDetectionService,
    ) -> SyncResult:
        """Sync detected changes to PostgreSQL, WooCommerce, and Qdrant.

        WooCommerce sync is best-effort: failures are logged but not fatal.

        Args:
            store: The store configuration.
            report: ChangeReport from change detection.
            change_detection: Service for updating hashes after sync.

        Returns:
            SyncResult with counts from each system.
        """
        errors: list[str] = []
        woo_created = 0
        woo_updated = 0
        db_created_count = 0
        db_updated_count = 0
        qdrant_upserted = 0
        qdrant_removed = 0

        engine = create_async_engine(self.settings.database_url)
        session_factory = async_sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )

        try:
            async with session_factory() as session:
                # a. Sync to PostgreSQL
                db_sync = DbSyncService(session)

                if report.new:
                    created = await db_sync.sync_new_products(
                        report.new, store.woo_store_id
                    )
                    db_created_count = len(created)

                if report.changed:
                    updated = await db_sync.sync_changed_products(
                        report.changed, store.woo_store_id
                    )
                    db_updated_count = len(updated)

                if report.removed_ids:
                    await db_sync.remove_products(
                        report.removed_ids, store.woo_store_id
                    )

                # b. WooCommerce sync (best-effort)
                try:
                    if (
                        self.settings.woo_store_url
                        and self.settings.woo_consumer_key
                        and self.settings.woo_consumer_secret
                    ):
                        woo_client = WooCommerceClient(
                            store_url=self.settings.woo_store_url,
                            consumer_key=self.settings.woo_consumer_key,
                            consumer_secret=self.settings.woo_consumer_secret,
                        )

                        if report.new:
                            woo_products = [
                                {
                                    "name": p.title,
                                    "regular_price": str(p.price) if p.price else "0",
                                    "description": p.description or "",
                                    "images": [
                                        {"src": img} for img in p.image_urls[:1]
                                    ],
                                    "status": "publish",
                                }
                                for p in report.new
                            ]
                            created_woo = await woo_client.batch_create_products(
                                woo_products
                            )
                            woo_created = len(created_woo)

                        if report.changed:
                            # For updates, we need to find existing WooCommerce IDs
                            woo_updates: list[dict] = []
                            for p in report.changed:
                                existing = await woo_client.find_product_by_sku(
                                    p.external_id
                                )
                                if existing:
                                    woo_updates.append(
                                        {
                                            "id": existing["id"],
                                            "name": p.title,
                                            "regular_price": (
                                                str(p.price) if p.price else "0"
                                            ),
                                            "description": p.description or "",
                                        }
                                    )
                            if woo_updates:
                                updated_woo = await woo_client.batch_update_products(
                                    woo_updates
                                )
                                woo_updated = len(updated_woo)
                    else:
                        logger.info(
                            "WooCommerce not configured, skipping WooCommerce sync"
                        )
                except Exception as woo_exc:
                    logger.warning("WooCommerce sync failed (non-fatal): %s", woo_exc)
                    errors.append(f"WooCommerce sync: {woo_exc}")

                # c. Vector sync (embed and upsert to Qdrant)
                try:
                    embedding_service = EmbeddingService()
                    embedding_service.load_model()

                    quality_gate = QualityGateService()
                    qdrant_client = await get_qdrant_client()

                    vector_sync = VectorSyncService(
                        embedding_service=embedding_service,
                        quality_gate=quality_gate,
                        qdrant_client=qdrant_client,
                    )

                    # Gather all new + changed DB products for vector sync
                    all_products_to_embed: list[Product] = []
                    if report.new:
                        all_products_to_embed.extend(created)
                    if report.changed:
                        all_products_to_embed.extend(updated)

                    if all_products_to_embed:
                        success, failed = await vector_sync.sync_products_to_qdrant(
                            all_products_to_embed
                        )
                        qdrant_upserted = success

                    if report.removed_ids:
                        await vector_sync.remove_from_qdrant(report.removed_ids)
                        qdrant_removed = len(report.removed_ids)

                except Exception as vec_exc:
                    logger.error("Vector sync failed: %s", vec_exc, exc_info=True)
                    errors.append(f"Vector sync: {vec_exc}")

                # d. Commit database changes
                await session.commit()

                # e. Update change detection hashes
                products_to_update = report.new + report.changed
                if products_to_update:
                    await change_detection.update_hashes(store.id, products_to_update)

                # f. Mark removed products
                if report.removed_ids:
                    await change_detection.mark_removed(store.id, report.removed_ids)

        finally:
            await engine.dispose()

        return SyncResult(
            store_id=store.id,
            woo_created=woo_created,
            woo_updated=woo_updated,
            db_created=db_created_count,
            db_updated=db_updated_count,
            qdrant_upserted=qdrant_upserted,
            qdrant_removed=qdrant_removed,
            errors=errors,
        )

    async def run_all(
        self,
        stores: list[StoreConfig] | None = None,
        *,
        dry_run: bool = False,
    ) -> PipelineResult:
        """Run the pipeline for all enabled stores concurrently.

        Steps:
            1. Load or filter store configs
            2. Run stores in parallel via asyncio.gather
            3. Evaluate re-clustering threshold
            4. Trigger re-clustering if needed

        Args:
            stores: Optional list of stores to run. If None, loads from config.
            dry_run: If True, skip sync and re-clustering.

        Returns:
            PipelineResult with timing, per-store results, and recluster status.
        """
        started_at = datetime.now(timezone.utc)

        # Step 1: Load store configs
        if stores is None:
            config = load_store_configs()
            enabled_stores = config.get_enabled_stores()
        else:
            enabled_stores = [s for s in stores if s.enabled]

        logger.info("Starting scraper pipeline for %d stores", len(enabled_stores))

        if not enabled_stores:
            logger.warning("No enabled stores found")
            return PipelineResult(
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                stores=[],
                sync=[],
                recluster_triggered=False,
            )

        # Step 2: Run stores concurrently
        raw_results = await asyncio.gather(
            *[self.run_store(store, dry_run=dry_run) for store in enabled_stores],
            return_exceptions=True,
        )

        scrape_results: list[ScrapeResult] = []
        sync_results: list[SyncResult] = []

        for i, result in enumerate(raw_results):
            if isinstance(result, Exception):
                logger.error(
                    "Store %s raised exception: %s",
                    enabled_stores[i].name,
                    result,
                )
                scrape_results.append(
                    ScrapeResult(
                        store_id=enabled_stores[i].id,
                        total_urls=0,
                        total_scraped=0,
                        total_failed=0,
                        total_new=0,
                        total_changed=0,
                        total_removed=0,
                        duration_seconds=0,
                        errors=[str(result)],
                    )
                )
            else:
                scrape_result, sync_result = result
                scrape_results.append(scrape_result)
                if sync_result is not None:
                    sync_results.append(sync_result)

        # Step 3: Re-clustering decision
        recluster_triggered = False

        if not dry_run:
            total_new = sum(r.total_new for r in scrape_results)
            total_changed = sum(r.total_changed for r in scrape_results)
            total_removed = sum(r.total_removed for r in scrape_results)
            changed_total = total_new + total_changed

            # Get total product count from PostgreSQL
            try:
                engine = create_async_engine(self.settings.database_url)
                session_factory = async_sessionmaker(
                    engine, expire_on_commit=False, class_=AsyncSession
                )
                async with session_factory() as session:
                    result = await session.execute(
                        select(func.count()).select_from(Product)
                    )
                    product_total = result.scalar() or 0

                    # Check threshold
                    vector_sync = VectorSyncService(
                        embedding_service=EmbeddingService(),
                        quality_gate=QualityGateService(),
                        qdrant_client=await get_qdrant_client(),
                    )
                    should_recluster = await vector_sync.should_recluster(
                        changed_total,
                        product_total,
                        self.settings.scraper_recluster_threshold,
                    )

                    if should_recluster:
                        logger.info("Triggering re-clustering")
                        await vector_sync.trigger_recluster(session)
                        recluster_triggered = True

                await engine.dispose()
            except Exception as exc:
                logger.error(
                    "Re-clustering check/trigger failed: %s", exc, exc_info=True
                )

        # Step 4: Build final result
        finished_at = datetime.now(timezone.utc)
        duration = (finished_at - started_at).total_seconds()

        total_new = sum(r.total_new for r in scrape_results)
        total_changed = sum(r.total_changed for r in scrape_results)
        total_removed = sum(r.total_removed for r in scrape_results)

        logger.info(
            "Pipeline complete: %d new, %d changed, %d removed across %d stores in %.1fs",
            total_new,
            total_changed,
            total_removed,
            len(enabled_stores),
            duration,
        )

        return PipelineResult(
            started_at=started_at,
            finished_at=finished_at,
            stores=scrape_results,
            sync=sync_results,
            recluster_triggered=recluster_triggered,
        )
