"""Push scraped products to WooCommerce REST API."""

from __future__ import annotations

import logging
import os

import httpx

from .schemas import ScrapedProduct

logger = logging.getLogger(__name__)


class WooSync:
    """Minimal WooCommerce client — just batch create/update."""

    def __init__(
        self,
        store_url: str | None = None,
        consumer_key: str | None = None,
        consumer_secret: str | None = None,
    ) -> None:
        self.store_url = (store_url or os.getenv("WOO_STORE_URL", "")).rstrip("/")
        self.consumer_key = consumer_key or os.getenv("WOO_CONSUMER_KEY", "")
        self.consumer_secret = consumer_secret or os.getenv("WOO_CONSUMER_SECRET", "")
        self.enabled = bool(self.store_url and self.consumer_key and self.consumer_secret)

        if not self.enabled:
            logger.warning("WooCommerce not configured — sync disabled")

    @property
    def _base(self) -> str:
        return f"{self.store_url}/wp-json/wc/v3"

    @property
    def _auth(self) -> tuple[str, str]:
        return (self.consumer_key, self.consumer_secret)

    async def push_products(self, products: list[ScrapedProduct]) -> int:
        """Create products in WooCommerce. Returns count created."""
        if not self.enabled or not products:
            return 0

        created = 0
        for i in range(0, len(products), 100):
            chunk = products[i : i + 100]
            payload = {
                "create": [
                    {
                        "name": p.title,
                        "sku": p.external_id,
                        "regular_price": str(p.price) if p.price else "0",
                        "description": p.description or "",
                        "images": [{"src": img} for img in p.image_urls[:1]],
                        "status": "publish",
                    }
                    for p in chunk
                ]
            }
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    r = await client.post(
                        f"{self._base}/products/batch",
                        json=payload,
                        auth=self._auth,
                    )
                    r.raise_for_status()
                    data = r.json()
                    created += len(data.get("create", []))
            except Exception as e:
                logger.warning("WooCommerce batch create failed: %s", e)

        logger.info("%d products pushed to WooCommerce", created)
        return created

    async def update_products(self, products: list[ScrapedProduct]) -> int:
        """Update changed products in WooCommerce. Returns count updated."""
        if not self.enabled or not products:
            return 0

        updated = 0
        for p in products:
            try:
                # Find by SKU
                async with httpx.AsyncClient(timeout=30) as client:
                    r = await client.get(
                        f"{self._base}/products",
                        params={"sku": p.external_id, "per_page": 1},
                        auth=self._auth,
                    )
                    r.raise_for_status()
                    results = r.json()
                    if not results:
                        continue

                    woo_id = results[0]["id"]
                    r = await client.put(
                        f"{self._base}/products/{woo_id}",
                        json={
                            "name": p.title,
                            "regular_price": str(p.price) if p.price else "0",
                            "description": p.description or "",
                        },
                        auth=self._auth,
                    )
                    r.raise_for_status()
                    updated += 1
            except Exception as e:
                logger.warning("WooCommerce update failed for %s: %s", p.external_id, e)

        logger.info("%d products updated in WooCommerce", updated)
        return updated
