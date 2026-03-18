"""Orchestrate: scrape → diff → push to WooCommerce."""

from __future__ import annotations

import asyncio
import logging
import time

from .change_detection import ChangeDetector
from .config import StoreConfig, load_stores
from .product_scraper import scrape_batch
from .schemas import ScrapedProduct
from .sitemap import fetch_product_urls
from .woo_sync import WooSync

logger = logging.getLogger(__name__)


async def run_store(
    store: StoreConfig,
    woo: WooSync,
    detector: ChangeDetector,
    *,
    dry_run: bool = False,
) -> dict:
    """Full pipeline for one store. Returns stats dict."""
    start = time.monotonic()
    stats = {"store": store.name, "urls": 0, "scraped": 0, "new": 0, "changed": 0, "removed": 0, "error": None}

    try:
        urls = await fetch_product_urls(store)
        stats["urls"] = len(urls)
        if not urls:
            return stats

        products = await scrape_batch(urls, store)
        stats["scraped"] = len(products)

        report = await detector.detect_changes(store.id, products)
        stats["new"] = len(report.new)
        stats["changed"] = len(report.changed)
        stats["removed"] = len(report.removed_ids)

        logger.info(
            "%s: %d new, %d changed, %d removed, %d unchanged",
            store.name, stats["new"], stats["changed"], stats["removed"], report.unchanged_count,
        )

        if dry_run:
            logger.info("[DRY RUN] Would sync %d new, %d changed for %s", stats["new"], stats["changed"], store.name)
            return stats

        if report.new:
            await woo.push_products(report.new)
        if report.changed:
            await woo.update_products(report.changed)

        # Update hashes after successful sync
        all_synced = report.new + report.changed
        if all_synced:
            await detector.update_hashes(store.id, all_synced)
        if report.removed_ids:
            await detector.mark_removed(store.id, report.removed_ids)

    except Exception as e:
        stats["error"] = str(e)
        logger.error("Pipeline failed for %s: %s", store.name, e, exc_info=True)

    stats["duration"] = round(time.monotonic() - start, 1)
    return stats


async def run_all(
    stores: list[StoreConfig] | None = None,
    *,
    dry_run: bool = False,
) -> list[dict]:
    """Run all stores in parallel."""
    if stores is None:
        stores = load_stores()

    if not stores:
        logger.warning("No stores configured")
        return []

    logger.info("Starting scraper for %d stores", len(stores))

    woo = WooSync()
    detector = ChangeDetector()
    await detector.initialize()

    results = await asyncio.gather(
        *[run_store(s, woo, detector, dry_run=dry_run) for s in stores],
        return_exceptions=True,
    )

    # Handle exceptions from gather
    final = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error("Store %s crashed: %s", stores[i].name, r)
            final.append({"store": stores[i].name, "error": str(r)})
        else:
            final.append(r)

    return final
