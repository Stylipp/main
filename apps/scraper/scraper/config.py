"""Store configuration — just add a URL and go."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import yaml


# Common sitemap paths to try (WooCommerce)
SITEMAP_CANDIDATES = [
    "/product-sitemap.xml",
    "/wp-sitemap-posts-product-1.xml",
    "/sitemap.xml",
    "/wp-sitemap.xml",
    "/sitemap_index.xml",
]

# Default WooCommerce CSS selectors (fallback when no JSON-LD)
DEFAULT_SELECTORS = {
    "title": ".product_title h1, h1.product_title, h1.entry-title",
    "price_regular": ".summary .price del .woocommerce-Price-amount",
    "price_sale": ".summary .price ins .woocommerce-Price-amount",
    "price_single": ".summary .price .woocommerce-Price-amount",
    "description": ".woocommerce-product-details__short-description",
    "categories": ".woocommerce-breadcrumb a",
    "images": ".woocommerce-product-gallery img[data-large_image]",
}


class StoreConfig:
    """Auto-derived store config from a URL."""

    def __init__(self, base_url: str) -> None:
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        self.base_url = base_url.rstrip("/")

        parsed = urlparse(self.base_url)
        domain = (parsed.hostname or base_url).removeprefix("www.")

        self.id = domain.split(".")[0]
        self.name = self.id.capitalize()
        self.sitemap_url: str = ""  # auto-discovered
        self.currency = "ILS"
        self.rate_limit_seconds = 0.5
        self.timeout_seconds = 30.0
        self.product_url_pattern = "/product/"
        self.selectors = DEFAULT_SELECTORS


def load_stores(config_path: Path | None = None) -> list[StoreConfig]:
    """Load stores from YAML. Just a list of URLs."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "stores.yaml"

    with open(config_path) as f:
        data = yaml.safe_load(f)

    return [StoreConfig(url) for url in data.get("stores", [])]
