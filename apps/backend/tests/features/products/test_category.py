from src.features.products.utils.category import (
    ProductCategory,
    normalize_raw_categories,
    normalize_woocommerce_categories,
)


def test_normalize_woocommerce_categories_maps_known_categories() -> None:
    category, raw_categories = normalize_woocommerce_categories(
        [
            {"name": "Women's Shoes", "slug": "womens-shoes"},
            {"name": "Sneakers", "slug": "sneakers"},
        ]
    )

    assert category is ProductCategory.SHOES
    assert raw_categories == ["women's shoes", "womens-shoes", "sneakers"]


def test_normalize_woocommerce_categories_falls_back_to_other() -> None:
    category, raw_categories = normalize_woocommerce_categories(
        [{"name": "Gift Ideas", "slug": "gift-ideas"}]
    )

    assert category is ProductCategory.OTHER
    assert raw_categories == ["gift ideas", "gift-ideas"]


def test_normalize_woocommerce_categories_handles_missing_data() -> None:
    category, raw_categories = normalize_woocommerce_categories(None)

    assert category is ProductCategory.OTHER
    assert raw_categories == []


def test_normalize_raw_categories_maps_hebrew_labels() -> None:
    category, raw_categories = normalize_raw_categories(
        ["מטפחות", "נעליים", "uncategorized"]
    )

    assert category is ProductCategory.SHOES
    assert raw_categories == ["מטפחות", "נעליים", "uncategorized"]


def test_normalize_raw_categories_decodes_percent_encoded_values() -> None:
    category, raw_categories = normalize_raw_categories(
        ["%D7%9E%D7%98%D7%A4%D7%97%D7%95%D7%AA"]
    )

    assert category is ProductCategory.ACCESSORIES
    assert raw_categories == ["מטפחות"]


def test_normalize_raw_categories_ignores_junk_values_for_mapping() -> None:
    category, raw_categories = normalize_raw_categories(["mini me", "כללי"])

    assert category is ProductCategory.OTHER
    assert raw_categories == ["mini me", "כללי"]
