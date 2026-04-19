"""Canonical product category mapping for catalog filtering."""

from __future__ import annotations

import re
from enum import Enum
from urllib.parse import unquote_plus


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
            "נעל",
            "נעלים",
            "נעליים",
            "סניקרס",
            "סניקר",
            "מגף",
            "מגפיים",
            "סנדל",
            "סנדלים",
            "כפכף",
            "כפכפים",
            "עקב",
            "עקבים",
        },
    ),
    (
        ProductCategory.DRESSES,
        {
            "dress",
            "dresses",
            "gown",
            "gowns",
            "שמלה",
            "שמלות",
        },
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
            "זקט",
            "ז'קט",
            "בלייזר",
            "בלייזרים",
            "מעיל",
            "מעילים",
            "עליונית",
            "עליוניות",
            "קרדיגן",
            "קרדיגנים",
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
            "תיק",
            "תיקים",
            "ארנק",
            "ארנקים",
            "קלאץ",
            "קלאץ'",
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
            "אקססוריז",
            "אביזרים",
            "אביזר",
            "תכשיט",
            "תכשיטים",
            "שרשרת",
            "שרשראות",
            "עגיל",
            "עגילים",
            "צמיד",
            "צמידים",
            "כובע",
            "כובעים",
            "חגורה",
            "חגורות",
            "צעיף",
            "צעיפים",
            "מטפחת",
            "מטפחות",
            "משקפיים",
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
            "מכנס",
            "מכנסיים",
            "גינס",
            "ג'ינס",
            "ג׳ינס",
            "חצאית",
            "חצאיות",
            "טייץ",
            "טייצים",
            "שורט",
            "שורטים",
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
            "חולצה",
            "חולצות",
            "טופ",
            "טופים",
            "סריג",
            "סריגים",
            "סוודר",
            "סוודרים",
            "קפוצון",
            "קפוצ'ון",
            "קפוצ׳ון",
            "קפוצונים",
        },
    ),
]

_IGNORED_CATEGORY_VALUES = {
    "all",
    "general",
    "gift ideas",
    "mini me",
    "mini-me",
    "new",
    "new in",
    "new-in",
    "sale",
    "sales",
    "uncategorized",
    "כללי",
}


def _normalize_category_value(value: str) -> str:
    decoded = unquote_plus(str(value)).strip().lower()
    return re.sub(r"\s+", " ", decoded)


def _append_normalized_category(
    raw_categories: list[str], seen: set[str], value: str | None
) -> None:
    if not value:
        return

    normalized = _normalize_category_value(value)
    if not normalized or normalized in seen:
        return

    raw_categories.append(normalized)
    seen.add(normalized)


def normalize_raw_categories(
    categories: list[str] | None,
) -> tuple[ProductCategory, list[str]]:
    """Map raw category strings to the canonical category set."""
    if not categories:
        return ProductCategory.OTHER, []

    raw_categories: list[str] = []
    seen: set[str] = set()
    tokens: set[str] = set()

    for category in categories:
        _append_normalized_category(raw_categories, seen, category)

    for raw_category in raw_categories:
        if raw_category in _IGNORED_CATEGORY_VALUES:
            continue

        tokens.update(token for token in _TOKEN_SPLIT_RE.split(raw_category) if token)

    for canonical_category, keywords in _CATEGORY_KEYWORDS:
        if tokens & keywords:
            return canonical_category, raw_categories

    return ProductCategory.OTHER, raw_categories


def normalize_woocommerce_categories(
    categories: list[dict] | None,
) -> tuple[ProductCategory, list[str]]:
    """Map raw WooCommerce categories to a small canonical category set."""
    if not categories:
        return ProductCategory.OTHER, []

    raw_categories: list[str] = []
    seen: set[str] = set()
    for category in categories:
        for key in ("name", "slug"):
            _append_normalized_category(raw_categories, seen, category.get(key))

    return normalize_raw_categories(raw_categories)
