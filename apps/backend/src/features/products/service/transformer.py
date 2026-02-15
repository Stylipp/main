from decimal import Decimal, InvalidOperation

from ..schemas.schemas import ProductCreate
from .woocommerce_client import WooProduct


class ProductTransformer:
    """Transforms WooCommerce products into our internal ProductCreate format."""

    def __init__(self, store_id: str, default_currency: str = "USD"):
        self.store_id = store_id
        self.default_currency = default_currency

    def transform(self, woo_product: WooProduct) -> ProductCreate | None:
        """Transform a WooCommerce product to our format.

        Returns None if the product is invalid (no images, invalid/zero price).
        """
        # Skip products without images
        if not woo_product.images:
            return None

        # Parse price
        try:
            price = Decimal(woo_product.price) if woo_product.price else Decimal("0")
            if price <= 0:
                return None
        except InvalidOperation:
            return None

        # Get first image URL
        image_url = woo_product.images[0].get("src", "")
        if not image_url:
            return None

        return ProductCreate(
            external_id=str(woo_product.id),
            store_id=self.store_id,
            title=woo_product.name,
            description=(
                woo_product.description[:1000] if woo_product.description else None
            ),
            price=price,
            currency=self.default_currency,
            image_url=image_url,
            product_url=woo_product.permalink,
        )
