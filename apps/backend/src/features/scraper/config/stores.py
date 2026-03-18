from pathlib import Path

import yaml
from pydantic import BaseModel


class StoreSelectors(BaseModel):
    """CSS selectors for product data extraction from store pages."""

    title: str
    price_regular: str
    price_sale: str
    price_single: str
    description: str
    categories: str
    images: str
    stock_in: str
    stock_out: str


class StoreConfig(BaseModel):
    """Configuration for a single store to scrape."""

    id: str
    name: str
    enabled: bool = True
    sitemap_url: str
    base_url: str
    currency: str = "ILS"
    rate_limit_seconds: float = 0.5
    timeout_seconds: float = 30.0
    product_url_pattern: str = "/product/"
    woo_store_id: str
    selectors: StoreSelectors


class ScraperConfig(BaseModel):
    """Top-level scraper configuration containing all store definitions."""

    stores: list[StoreConfig]

    def get_enabled_stores(self) -> list[StoreConfig]:
        """Return only enabled store configurations."""
        return [s for s in self.stores if s.enabled]


def load_store_configs(config_path: Path | None = None) -> ScraperConfig:
    """Load store configurations from YAML file.

    Args:
        config_path: Path to the YAML config file. Defaults to stores.yaml
                     in the same directory as this module.

    Returns:
        ScraperConfig with all store definitions loaded.
    """
    if config_path is None:
        config_path = Path(__file__).parent / "stores.yaml"

    with open(config_path) as f:
        data = yaml.safe_load(f)

    return ScraperConfig(**data)
