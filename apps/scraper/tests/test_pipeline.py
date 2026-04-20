"""Regression tests for pipeline selective hash updates and archive flow."""

from datetime import datetime, UTC
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.scraper.scraper.change_detection import ChangeDetector
from apps.scraper.scraper.pipeline import run_store
from apps.scraper.scraper.schemas import ChangeReport, ScrapedProduct, SyncResult


def _make_product(external_id: str, title: str = "Test") -> ScrapedProduct:
    return ScrapedProduct(
        url=f"https://store.example.com/product/{external_id}",
        external_id=external_id,
        title=title,
        store_id="test-store",
        scraped_at=datetime.now(UTC),
        price=Decimal("100"),
        currency="ILS",
        image_urls=["https://cdn.example.com/img.jpg"],
        categories=["shoes"],
    )


def _make_store():
    store = MagicMock()
    store.name = "TestStore"
    store.id = "test-store"
    store.currency = "ILS"
    store.rate_limit_seconds = 0
    store.timeout_seconds = 10
    store.platform = "woocommerce"
    store.base_url = "https://store.example.com"
    store.selectors = {}
    return store


@pytest.mark.asyncio
async def test_pipeline_updates_hashes_only_for_accepted() -> None:
    """Pipeline updates hashes only for accepted products, not rejected ones."""
    p_new = _make_product("prod_new")
    p_changed = _make_product("prod_changed")

    store = _make_store()

    sync = AsyncMock()
    sync.push_products.return_value = SyncResult(
        created=1, accepted_ids=["prod_new"]
    )
    sync.update_products.return_value = SyncResult(
        updated=0, failed=1, accepted_ids=[]  # prod_changed rejected
    )
    sync.archive_products.return_value = 0

    detector = AsyncMock(spec=ChangeDetector)
    detector.detect_changes.return_value = ChangeReport(
        store_id="test-store",
        new=[p_new],
        changed=[p_changed],
        removed_ids=[],
        unchanged_count=5,
    )

    with patch(
        "apps.scraper.scraper.pipeline.fetch_product_urls",
        return_value=["url1"],
    ), patch(
        "apps.scraper.scraper.pipeline.scrape_batch",
        return_value=[p_new, p_changed],
    ), patch(
        "apps.scraper.scraper.pipeline.telegram",
    ):
        stats = await run_store(store, sync, detector)

    # Verify update_hashes called with accepted new products only
    new_hash_call = detector.update_hashes.call_args_list[0]
    assert new_hash_call[0][0] == "test-store"
    accepted_new = new_hash_call[0][1]
    assert len(accepted_new) == 1
    assert accepted_new[0].external_id == "prod_new"

    # Changed products had 0 accepted — update_hashes should NOT be called for them
    assert detector.update_hashes.call_count == 1


@pytest.mark.asyncio
async def test_pipeline_archives_removed_products() -> None:
    """Pipeline calls mark_removed and archive_products for removed products."""
    store = _make_store()

    sync = AsyncMock()
    sync.archive_products.return_value = 2

    detector = AsyncMock(spec=ChangeDetector)
    detector.detect_changes.return_value = ChangeReport(
        store_id="test-store",
        new=[],
        changed=[],
        removed_ids=["old_1", "old_2"],
        unchanged_count=3,
    )

    with patch(
        "apps.scraper.scraper.pipeline.fetch_product_urls",
        return_value=["url1"],
    ), patch(
        "apps.scraper.scraper.pipeline.scrape_batch",
        return_value=[],
    ), patch(
        "apps.scraper.scraper.pipeline.telegram",
    ):
        stats = await run_store(store, sync, detector)

    # mark_removed called with removed IDs
    detector.mark_removed.assert_called_once_with("test-store", ["old_1", "old_2"])
    # archive_products called with store_id and removed IDs
    sync.archive_products.assert_called_once_with("test-store", ["old_1", "old_2"])
    assert stats["removed"] == 2
