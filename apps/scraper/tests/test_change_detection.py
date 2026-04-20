"""Regression tests for change detection: removal, return, and hash update flows."""

import asyncio
import tempfile
from datetime import datetime, UTC
from decimal import Decimal
from pathlib import Path

import pytest

from apps.scraper.scraper.change_detection import ChangeDetector
from apps.scraper.scraper.schemas import ScrapedProduct


def _make_product(
    external_id: str = "prod_1",
    title: str = "Test Product",
    price: Decimal | None = Decimal("100"),
    **kwargs,
) -> ScrapedProduct:
    defaults = dict(
        url=f"https://store.example.com/product/{external_id}",
        external_id=external_id,
        title=title,
        store_id="test-store",
        scraped_at=datetime.now(UTC),
        price=price,
        currency="ILS",
        image_urls=["https://cdn.example.com/img.jpg"],
        categories=["shoes"],
    )
    defaults.update(kwargs)
    return ScrapedProduct(**defaults)


@pytest.fixture
def detector(tmp_path: Path):
    return ChangeDetector(db_path=tmp_path / "test_state.db")


@pytest.mark.asyncio
async def test_mark_removed_soft_deletes(detector: ChangeDetector) -> None:
    """mark_removed sets removed_at instead of hard-deleting the row."""
    await detector.initialize()
    p = _make_product("prod_1")
    await detector.update_hashes("test-store", [p])

    await detector.mark_removed("test-store", ["prod_1"])

    # Product should not appear in active set
    report = await detector.detect_changes("test-store", [])
    assert report.removed_ids == []  # already removed, not re-detected

    # But the row still exists (not hard deleted) — verify via returning detection
    report2 = await detector.detect_changes("test-store", [p])
    # Returning product detected as changed (not new)
    assert len(report2.changed) == 1
    assert report2.changed[0].external_id == "prod_1"
    assert len(report2.new) == 0


@pytest.mark.asyncio
async def test_returning_product_clears_removed_at(detector: ChangeDetector) -> None:
    """A returning product clears removed_at and is treated as changed, not duplicated."""
    await detector.initialize()
    p = _make_product("prod_1")
    await detector.update_hashes("test-store", [p])
    await detector.mark_removed("test-store", ["prod_1"])

    # Product returns in next scrape
    report = await detector.detect_changes("test-store", [p])
    assert len(report.changed) == 1
    assert report.changed[0].external_id == "prod_1"
    assert len(report.new) == 0

    # After detect_changes clears removed_at, subsequent scrape sees it as unchanged
    await detector.update_hashes("test-store", [p])
    report2 = await detector.detect_changes("test-store", [p])
    assert report2.unchanged_count == 1
    assert len(report2.new) == 0
    assert len(report2.changed) == 0


@pytest.mark.asyncio
async def test_selective_hash_update_only_accepted(detector: ChangeDetector) -> None:
    """Only accepted products get their hashes updated; rejected keep old hash."""
    await detector.initialize()

    p1 = _make_product("prod_1", title="Original A")
    p2 = _make_product("prod_2", title="Original B")
    await detector.update_hashes("test-store", [p1, p2])

    # Both products change
    p1_changed = _make_product("prod_1", title="Changed A")
    p2_changed = _make_product("prod_2", title="Changed B")
    report = await detector.detect_changes("test-store", [p1_changed, p2_changed])
    assert len(report.changed) == 2

    # Simulate: only prod_1 accepted, prod_2 rejected
    accepted = [p for p in report.changed if p.external_id == "prod_1"]
    await detector.update_hashes("test-store", accepted)

    # Next run: prod_1 unchanged (hash updated), prod_2 still changed (old hash)
    report2 = await detector.detect_changes("test-store", [p1_changed, p2_changed])
    assert report2.unchanged_count == 1
    assert len(report2.changed) == 1
    assert report2.changed[0].external_id == "prod_2"
