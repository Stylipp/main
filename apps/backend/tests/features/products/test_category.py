from src.features.products.utils.category import (
    ProductCategory,
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
