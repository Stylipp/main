import json

from bs4 import BeautifulSoup

from apps.scraper.scraper.product_scraper import _extract_stable_id, _merge_product_data


def test_merge_product_data_keeps_html_categories_when_jsonld_has_none() -> None:
    merged = _merge_product_data(
        {
            "title": "Tailored coat",
            "description": "Structured wool coat",
            "price": None,
            "sale_price": None,
            "image_urls": ["https://cdn.example.com/jsonld.jpg"],
            "categories": [],
        },
        {
            "title": "Tailored coat fallback",
            "description": "HTML fallback description",
            "price": 249,
            "sale_price": 199,
            "image_urls": ["https://cdn.example.com/html.jpg"],
            "categories": ["מעילים", "sale"],
        },
    )

    assert merged == {
        "title": "Tailored coat",
        "description": "Structured wool coat",
        "price": 249,
        "sale_price": 199,
        "image_urls": [
            "https://cdn.example.com/jsonld.jpg",
            "https://cdn.example.com/html.jpg",
        ],
        "categories": ["מעילים", "sale"],
    }


def test_merge_product_data_deduplicates_categories_and_images() -> None:
    merged = _merge_product_data(
        {
            "title": "Satin top",
            "description": None,
            "price": 120,
            "sale_price": None,
            "image_urls": ["https://cdn.example.com/1.jpg"],
            "categories": ["tops"],
        },
        {
            "title": "Satin top html",
            "description": "fallback",
            "price": 120,
            "sale_price": None,
            "image_urls": [
                "https://cdn.example.com/1.jpg",
                "https://cdn.example.com/2.jpg",
            ],
            "categories": ["tops", "new"],
        },
    )

    assert merged["image_urls"] == [
        "https://cdn.example.com/1.jpg",
        "https://cdn.example.com/2.jpg",
    ]
    assert merged["categories"] == ["tops", "new"]


# --- Stable ID extraction tests ---


def _make_store_config():
    from apps.scraper.scraper.config import StoreConfig

    return StoreConfig("https://store.example.com")


def _soup_with_jsonld(sku: str | None = None, group_id: str | None = None) -> tuple:
    """Build a BeautifulSoup with optional JSON-LD sku or productGroupID."""
    node = {"@type": "Product", "name": "Test Product"}
    if sku is not None:
        node["sku"] = sku
    if group_id is not None:
        node["productGroupID"] = group_id

    html = f'<html><head><script type="application/ld+json">{json.dumps(node)}</script></head><body></body></html>'
    soup = BeautifulSoup(html, "html.parser")
    return soup, node


def test_stable_id_prefers_jsonld_sku() -> None:
    """JSON-LD sku is the highest priority stable ID."""
    soup, node = _soup_with_jsonld(sku="SKU-12345")
    store = _make_store_config()
    result = _extract_stable_id(soup, node, store)
    assert result == "SKU-12345"


def test_stable_id_uses_woocommerce_data_product_id() -> None:
    """WooCommerce data-product_id is used when sku is absent."""
    html = '<html><body><button data-product_id="7890">Add to cart</button></body></html>'
    soup = BeautifulSoup(html, "html.parser")
    store = _make_store_config()
    result = _extract_stable_id(soup, None, store)
    assert result == "7890"


def test_stable_id_uses_shopify_product_group_id() -> None:
    """Shopify productGroupID is used when sku and data-product_id are absent."""
    soup, node = _soup_with_jsonld(group_id="shopify-group-42")
    store = _make_store_config()
    result = _extract_stable_id(soup, node, store)
    assert result == "shopify-group-42"


def test_stable_id_falls_back_to_none() -> None:
    """When no stable source ID exists, returns None (caller uses md5 fallback)."""
    html = "<html><body><h1>Product</h1></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    store = _make_store_config()
    result = _extract_stable_id(soup, None, store)
    assert result is None


def test_stable_id_sku_over_product_group_id() -> None:
    """When both sku and productGroupID exist, sku wins."""
    soup, node = _soup_with_jsonld(sku="SKU-1", group_id="GROUP-2")
    store = _make_store_config()
    result = _extract_stable_id(soup, node, store)
    assert result == "SKU-1"
