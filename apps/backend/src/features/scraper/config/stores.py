"""Store configuration for the scraper.

Stores are configured as simple URLs in stores.yaml. Everything else
(id, name, sitemap, selectors) is auto-derived. Just add a URL and go.
"""

from pathlib import Path
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel


# Default CSS selectors for WooCommerce stores.
# Works on 95%+ of WooCommerce sites without customization.
DEFAULT_SELECTORS = {
    "title": ".product_title h1, h1.product_title, h1.entry-title",
    "price_regular": ".summary .price del .woocommerce-Price-amount",
    "price_sale": ".summary .price ins .woocommerce-Price-amount",
    "price_single": ".summary .price .woocommerce-Price-amount",
    "description": ".woocommerce-product-details__short-description",
    "categories": ".woocommerce-breadcrumb a",
    "images": ".woocommerce-product-gallery img[data-large_image]",
    "stock_in": ".stock.in-stock",
    "stock_out": ".stock.out-of-stock",
}

# Common sitemap paths to try, in order of likelihood for WooCommerce
SITEMAP_CANDIDATES = [
    "/product-sitemap.xml",
    "/wp-sitemap-posts-product-1.xml",
    "/sitemap.xml",
    "/wp-sitemap.xml",
    "/sitemap_index.xml",
]


class StoreSelectors(BaseModel):
    """CSS selectors for product data extraction from store pages."""

    title: str = DEFAULT_SELECTORS["title"]
    price_regular: str = DEFAULT_SELECTORS["price_regular"]
    price_sale: str = DEFAULT_SELECTORS["price_sale"]
    price_single: str = DEFAULT_SELECTORS["price_single"]
    description: str = DEFAULT_SELECTORS["description"]
    categories: str = DEFAULT_SELECTORS["categories"]
    images: str = DEFAULT_SELECTORS["images"]
    stock_in: str = DEFAULT_SELECTORS["stock_in"]
    stock_out: str = DEFAULT_SELECTORS["stock_out"]


class StoreConfig(BaseModel):
    """Configuration for a single store to scrape.

    Only base_url is required. Everything else has sensible defaults.
    """

    id: str = ""
    name: str = ""
    enabled: bool = True
    base_url: str
    sitemap_url: str = ""  # auto-discovered if empty
    currency: str = "ILS"
    rate_limit_seconds: float = 0.5
    timeout_seconds: float = 30.0
    product_url_pattern: str = "/product/"
    woo_store_id: str = "woo-cloudways"
    selectors: StoreSelectors = StoreSelectors()

    def model_post_init(self, __context) -> None:
        """Auto-derive id and name from base_url if not set."""
        parsed = urlparse(self.base_url)
        domain = parsed.hostname or self.base_url

        if not self.id:
            # mekimi.co.il -> mekimi
            self.id = domain.split(".")[0]

        if not self.name:
            # mekimi -> Mekimi
            self.name = self.id.capitalize()

    @classmethod
    def from_url(cls, url: str) -> "StoreConfig":
        """Create a StoreConfig from just a URL string."""
        # Ensure https://
        if not url.startswith("http"):
            url = f"https://{url}"
        # Strip trailing slash
        url = url.rstrip("/")
        return cls(base_url=url)


class ScraperConfig(BaseModel):
    """Top-level scraper configuration containing all store definitions."""

    stores: list[StoreConfig]

    def get_enabled_stores(self) -> list[StoreConfig]:
        """Return only enabled store configurations."""
        return [s for s in self.stores if s.enabled]


def load_store_configs(config_path: Path | None = None) -> ScraperConfig:
    """Load store configurations from YAML file.

    The YAML can be either:
    - Simple: a list of URL strings
    - Detailed: a list of full config objects (for overrides)

    Both formats can be mixed in the same file.
    """
    if config_path is None:
        config_path = Path(__file__).parent / "stores.yaml"

    with open(config_path) as f:
        data = yaml.safe_load(f)

    raw_stores = data.get("stores", [])
    configs: list[StoreConfig] = []

    for entry in raw_stores:
        if isinstance(entry, str):
            # Simple URL string -> auto-derive everything
            configs.append(StoreConfig.from_url(entry))
        elif isinstance(entry, dict):
            # Full or partial config dict
            if "base_url" not in entry and "url" in entry:
                entry["base_url"] = entry.pop("url")
            configs.append(StoreConfig(**entry))

    return ScraperConfig(stores=configs)
