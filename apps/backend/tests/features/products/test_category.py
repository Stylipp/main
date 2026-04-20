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


def test_navigation_labels_ignored_when_real_category_present() -> None:
    """Navigation labels like 'new collection' should not prevent matching a real category."""
    category, raw = normalize_raw_categories(
        ["new collection", "sale", "shoes"]
    )
    assert category is ProductCategory.SHOES

    category, raw = normalize_raw_categories(
        ["shop", "women", "חולצות"]
    )
    assert category is ProductCategory.TOPS


def test_junk_only_categories_fall_back_to_other() -> None:
    """Category lists with only navigation/merchandising labels fall back to OTHER."""
    category, raw = normalize_raw_categories(
        ["new collection", "sale", "shop", "women"]
    )
    assert category is ProductCategory.OTHER

    category, raw = normalize_raw_categories(
        ["עמוד הבית", "חנות", "חדש", "קולקציה"]
    )
    assert category is ProductCategory.OTHER


def test_hebrew_apostrophe_variants_map_correctly() -> None:
    """Different Hebrew apostrophe characters should all normalize to the same token."""
    # geresh ׳
    cat1, _ = normalize_raw_categories(["ג׳ינס"])
    assert cat1 is ProductCategory.PANTS

    # right single quote '
    cat2, _ = normalize_raw_categories(["ג\u2019ינס"])
    assert cat2 is ProductCategory.PANTS

    # ASCII apostrophe
    cat3, _ = normalize_raw_categories(["ג'ינס"])
    assert cat3 is ProductCategory.PANTS

    # Hebrew geresh U+05F3
    cat4, _ = normalize_raw_categories(["ג\u05f3ינס"])
    assert cat4 is ProductCategory.PANTS


def test_new_collection_does_not_override_concrete_category() -> None:
    """'new collection' must not shadow concrete categories like 'pants' or 'shoes'."""
    category, _ = normalize_raw_categories(
        ["new collection", "מכנסיים"]
    )
    assert category is ProductCategory.PANTS

    category, _ = normalize_raw_categories(
        ["homepage", "new arrivals", "סנדלים"]
    )
    assert category is ProductCategory.SHOES


def test_hebrew_navigation_breadcrumbs_ignored() -> None:
    """Hebrew navigation-only breadcrumbs should be ignored."""
    category, _ = normalize_raw_categories(
        ["עמוד הבית", "חנות", "בנות", "שמלות"]
    )
    assert category is ProductCategory.DRESSES

    category, _ = normalize_raw_categories(
        ["דף הבית", "נשים", "תיקים"]
    )
    assert category is ProductCategory.BAGS


def test_english_gender_and_store_labels_ignored() -> None:
    """Gender labels like 'women', 'men' and store labels like 'shop' are ignored."""
    category, _ = normalize_raw_categories(
        ["women", "store", "earrings"]
    )
    assert category is ProductCategory.ACCESSORIES

    category, _ = normalize_raw_categories(
        ["men", "boys", "kids"]
    )
    assert category is ProductCategory.OTHER
