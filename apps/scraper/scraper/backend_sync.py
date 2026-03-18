"""Push scraped products to the Stylipp backend API."""

from __future__ import annotations

import logging
import os

import httpx

from .schemas import ScrapedProduct

logger = logging.getLogger(__name__)


class BackendSync:
    """Sync scraped products to the backend via HTTP API."""

    def __init__(self, api_url: str | None = None) -> None:
        self.api_url = (api_url or os.getenv("BACKEND_API_URL", "")).rstrip("/")
        self.enabled = bool(self.api_url)
        if not self.enabled:
            logger.warning("BACKEND_API_URL not set — sync disabled")

    def _to_payload(self, product: ScrapedProduct) -> dict:
        """Convert ScrapedProduct to backend ProductCreate format."""
        return {
            "external_id": product.external_id,
            "store_id": product.store_id,
            "title": product.title,
            "description": product.description or "",
            "price": str(product.sale_price or product.price or 0),
            "currency": product.currency,
            "image_url": product.image_urls[0] if product.image_urls else "",
            "product_url": product.url,
        }

    async def push_products(self, products: list[ScrapedProduct]) -> int:
        """Push new products to backend. Returns count created."""
        if not self.enabled or not products:
            return 0

        # Filter out products with no images (backend requires image_url)
        valid = [p for p in products if p.image_urls]
        if not valid:
            return 0

        created = 0
        # Send in batches of 50
        for i in range(0, len(valid), 50):
            chunk = valid[i:i + 50]
            payload = {"products": [self._to_payload(p) for p in chunk]}
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    r = await client.post(
                        f"{self.api_url}/api/products/ingest/batch",
                        json=payload,
                    )
                    r.raise_for_status()
                    data = r.json()
                    created += data.get("created", 0)
                    failed = data.get("failed", 0)
                    if failed:
                        for err in data.get("errors", [])[:5]:
                            logger.warning("Ingest failed: %s — %s", err.get("external_id"), err.get("error"))
            except Exception as e:
                logger.error("Backend batch push failed: %s", e)

        logger.info("%d products pushed to backend", created)
        return created

    async def update_products(self, products: list[ScrapedProduct]) -> int:
        """Push changed products to backend (handled as upsert). Returns count updated."""
        if not self.enabled or not products:
            return 0

        valid = [p for p in products if p.image_urls]
        if not valid:
            return 0

        updated = 0
        for i in range(0, len(valid), 50):
            chunk = valid[i:i + 50]
            payload = {"products": [self._to_payload(p) for p in chunk]}
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    r = await client.post(
                        f"{self.api_url}/api/products/ingest/batch",
                        json=payload,
                    )
                    r.raise_for_status()
                    data = r.json()
                    updated += data.get("updated", 0)
            except Exception as e:
                logger.error("Backend batch update failed: %s", e)

        logger.info("%d products updated in backend", updated)
        return updated
