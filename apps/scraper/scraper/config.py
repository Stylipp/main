"""Store configuration — just add a URL and go."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import yaml


# Common sitemap paths to try (WooCommerce + Shopify)
SITEMAP_CANDIDATES = [
    "/product-sitemap.xml",
    "/wp-sitemap-posts-product-1.xml",
    "/sitemap_products_1.xml",          # Shopify
    "/sitemap.xml",
    "/wp-sitemap.xml",
    "/sitemap_index.xml",
]

# WooCommerce CSS selectors (fallback when no JSON-LD)
_WOO_SELECTORS = {
    "title": ".product_title h1, h1.product_title, h1.entry-title",
    "price_regular": ".summary .price del .woocommerce-Price-amount",
    "price_sale": ".summary .price ins .woocommerce-Price-amount",
    "price_single": ".summary .price .woocommerce-Price-amount",
    "description": ".woocommerce-product-details__short-description",
    "categories": ".woocommerce-breadcrumb a",
    "images": ".woocommerce-product-gallery img[data-large_image]",
}

# Shopify CSS selectors (fallback when no JSON-LD)
_SHOPIFY_SELECTORS = {
    "title": "h1.product-single__title, h1.product__title, h1",
    "price_regular": "s.product__price, .price .compare-price, s .money",
    "price_sale": ".product__price .money, .price .money",
    "price_single": ".product__price .money, .price .money, .product-price",
    "description": ".product-single__description, .product__description",
    "categories": "nav.breadcrumb a, .breadcrumbs a",
    "images": ".product-single__photo img, .product__photo img, .product-featured-media img",
}

# Magento CSS selectors (fallback when no JSON-LD)
_MAGENTO_SELECTORS = {
    "title": "h1.page-title span, h1.product-name",
    "price_regular": ".old-price .price, .price-box .price-old .price",
    "price_sale": ".special-price .price, .price-box .special-price .price",
    "price_single": ".price-box .price, [data-price-type='finalPrice'] .price",
    "description": ".product.attribute.description .value, #description .value",
    "categories": ".breadcrumbs a, nav.breadcrumbs a",
    "images": ".gallery-placeholder img, .fotorama__img, .product.media img",
}


def _detect_platform(hostname: str) -> str:
    """Guess platform from domain. Returns 'shopify', 'magento', or 'woocommerce'."""
    if hostname and hostname.endswith(".myshopify.com"):
        return "shopify"
    return "woocommerce"


class StoreConfig:
    """Auto-derived store config from a URL."""

    def __init__(self, base_url: str, platform: str = "") -> None:
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        self.base_url = base_url.rstrip("/")

        parsed = urlparse(self.base_url)
        domain = (parsed.hostname or base_url).removeprefix("www.")

        self.id = domain.split(".")[0]
        self.name = self.id.capitalize()
        self.sitemap_url: str = ""  # auto-discovered
        self.currency = "ILS"
        self.rate_limit_seconds = 1.0
        self.timeout_seconds = 30.0
        self.platform = platform or _detect_platform(parsed.hostname or "")

        if self.platform == "shopify":
            self.product_url_pattern = "/products/"
            self.selectors = _SHOPIFY_SELECTORS
            self.rate_limit_seconds = 2.0  # Shopify/Cloudflare needs slower rate
        elif self.platform == "magento":
            self.product_url_pattern = ""  # no fixed prefix — filter via regex
            self.product_url_regex = r"/m?\d{7,}"
            self.selectors = _MAGENTO_SELECTORS
        else:
            self.product_url_pattern = "/product/"
            self.selectors = _WOO_SELECTORS

        if not hasattr(self, "product_url_regex"):
            self.product_url_regex = ""


def load_stores(config_path: Path | None = None) -> list[StoreConfig]:
    """Load stores from YAML. Each entry is a URL or {url, platform}."""
    if config_path is None:
        # Prefer data volume path (writable by bot), fall back to bundled
        data_path = Path("/app/data/stores.yaml")
        bundled_path = Path(__file__).parent.parent / "stores.yaml"
        config_path = data_path if data_path.exists() else bundled_path

    with open(config_path) as f:
        data = yaml.safe_load(f)

    stores = []
    for entry in data.get("stores", []):
        if isinstance(entry, str):
            stores.append(StoreConfig(entry))
        elif isinstance(entry, dict):
            stores.append(StoreConfig(entry["url"], platform=entry.get("platform", "")))
    return stores
