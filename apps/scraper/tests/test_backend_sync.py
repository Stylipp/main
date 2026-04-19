from datetime import UTC, datetime
from decimal import Decimal

from apps.scraper.scraper.backend_sync import BackendSync
from apps.scraper.scraper.schemas import ScrapedProduct


def test_to_payload_preserves_raw_categories() -> None:
    sync = BackendSync(api_url="https://api.example.com")
    product = ScrapedProduct(
        url="https://store.example.com/p/123",
        external_id="123",
        title="Structured blazer",
        store_id="example-store",
        scraped_at=datetime.now(UTC),
        description="Sharp tailoring",
        price=Decimal("199.00"),
        sale_price=Decimal("149.00"),
        currency="ILS",
        image_urls=["https://cdn.example.com/1.jpg"],
        categories=["בלייזרים", "sale"],
    )

    payload = sync._to_payload(product)

    assert payload["price"] == "149.00"
    assert payload["raw_categories"] == ["בלייזרים", "sale"]
    assert "category" not in payload
