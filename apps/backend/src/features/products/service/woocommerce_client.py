import httpx
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class WooProduct:
    """Raw product data from WooCommerce API."""

    id: int
    name: str
    description: str
    price: str  # WooCommerce returns price as string
    regular_price: str
    sale_price: str
    images: list[dict] = field(default_factory=list)  # [{"src": "url", "alt": "..."}]
    permalink: str = ""
    status: str = ""
    stock_status: str = ""
    categories: list[dict] = field(default_factory=list)


class WooCommerceClient:
    """Async client for fetching products from WooCommerce REST API v3."""

    def __init__(
        self,
        store_url: str,
        consumer_key: str,
        consumer_secret: str,
        timeout: float = 30.0,
    ):
        self.store_url = store_url.rstrip("/")
        self.api_url = f"{self.store_url}/wp-json/wc/v3"
        self._auth = (consumer_key, consumer_secret)
        self.timeout = timeout

    async def get_products(
        self,
        page: int = 1,
        per_page: int = 100,
        status: str = "publish",
        stock_status: str = "instock",
    ) -> list[WooProduct]:
        """Fetch a page of products from WooCommerce store."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/products",
                auth=self._auth,
                params={
                    "page": page,
                    "per_page": per_page,
                    "status": status,
                    "stock_status": stock_status,
                },
            )
            response.raise_for_status()

            products = []
            for item in response.json():
                products.append(
                    WooProduct(
                        id=item["id"],
                        name=item["name"],
                        description=item.get("description", ""),
                        price=item.get("price", "0"),
                        regular_price=item.get("regular_price", "0"),
                        sale_price=item.get("sale_price", ""),
                        images=item.get("images", []),
                        permalink=item.get("permalink", ""),
                        status=item.get("status", ""),
                        stock_status=item.get("stock_status", ""),
                        categories=item.get("categories", []),
                    )
                )
            return products

    async def get_all_products(
        self,
        per_page: int = 100,
        max_pages: int | None = None,
    ) -> AsyncIterator[WooProduct]:
        """Iterate through all products with automatic pagination."""
        page = 1
        while True:
            if max_pages and page > max_pages:
                break

            products = await self.get_products(page=page, per_page=per_page)
            if not products:
                break

            for product in products:
                yield product

            if len(products) < per_page:
                break

            page += 1

    async def get_product_count(self) -> int:
        """Get total number of published products using X-WP-Total header."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/products",
                auth=self._auth,
                params={"per_page": 1, "status": "publish"},
            )
            response.raise_for_status()
            return int(response.headers.get("X-WP-Total", 0))

    async def health_check(self) -> bool:
        """Check if the WooCommerce store API is accessible."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_url}/products",
                    auth=self._auth,
                    params={"per_page": 1},
                )
                return response.status_code == 200
        except Exception:
            return False
