from apps.scraper.scraper.product_scraper import _merge_product_data


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
