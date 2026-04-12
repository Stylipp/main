"""Canonical product category mapping for catalog filtering."""

from __future__ import annotations

import re
from enum import Enum


class ProductCategory(str, Enum):
    SHOES = "shoes"
    TOPS = "tops"
    PANTS = "pants"
    DRESSES = "dresses"
    JACKETS = "jackets"
    BAGS = "bags"
    ACCESSORIES = "accessories"
    OTHER = "other"


_TOKEN_SPLIT_RE = re.compile(r"[\s\-/&,_]+")
_CATEGORY_KEYWORDS: list[tuple[ProductCategory, set[str]]] = [
    (
        ProductCategory.SHOES,
        {
            "shoe",
            "shoes",
            "sneaker",
            "sneakers",
            "boot",
            "boots",
            "heel",
            "heels",
            "sandals",
            "loafer",
            "loafers",
            "flats",
            "mules",
            "clogs",
            "slippers",
        },
    ),
    (
        ProductCategory.DRESSES,
        {"dress", "dresses", "gown", "gowns", "maxi", "midi", "mini"},
    ),
    (
        ProductCategory.JACKETS,
        {
            "jacket",
            "jackets",
            "coat",
            "coats",
            "outerwear",
            "blazer",
            "blazers",
            "cardigan",
            "cardigans",
        },
    ),
    (
        ProductCategory.BAGS,
        {
            "bag",
            "bags",
            "handbag",
            "handbags",
            "tote",
            "totes",
            "backpack",
            "backpacks",
            "purse",
            "purses",
            "wallet",
            "wallets",
            "crossbody",
            "satchel",
        },
    ),
    (
        ProductCategory.ACCESSORIES,
        {
            "accessories",
            "accessory",
            "jewelry",
            "jewellery",
            "necklace",
            "necklaces",
            "bracelet",
            "bracelets",
            "ring",
            "rings",
            "earring",
            "earrings",
            "hat",
            "hats",
            "belt",
            "belts",
            "scarf",
            "scarves",
            "sunglasses",
        },
    ),
    (
        ProductCategory.PANTS,
        {
            "pants",
            "trousers",
            "jeans",
            "denim",
            "shorts",
            "skirt",
            "skirts",
            "leggings",
            "joggers",
        },
    ),
    (
        ProductCategory.TOPS,
        {
            "tops",
            "top",
            "shirt",
            "shirts",
            "tee",
            "tees",
            "tshirt",
            "tshirts",
            "blouse",
            "blouses",
            "sweater",
            "sweaters",
            "hoodie",
            "hoodies",
            "knitwear",
            "tank",
            "tanks",
        },
    ),
]


def normalize_woocommerce_categories(
    categories: list[dict] | None,
) -> tuple[ProductCategory, list[str]]:
    """Map raw WooCommerce categories to a small canonical category set."""
    if not categories:
        return ProductCategory.OTHER, []

    raw_categories: list[str] = []
    tokens: set[str] = set()

    for category in categories:
        for key in ("name", "slug"):
            value = category.get(key)
            if not value:
                continue

            normalized = str(value).strip().lower()
            if not normalized:
                continue

            if normalized not in raw_categories:
                raw_categories.append(normalized)

            tokens.update(token for token in _TOKEN_SPLIT_RE.split(normalized) if token)

    for canonical_category, keywords in _CATEGORY_KEYWORDS:
        if tokens & keywords:
            return canonical_category, raw_categories

    return ProductCategory.OTHER, raw_categories
