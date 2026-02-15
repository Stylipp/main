"""Product repository for PostgreSQL CRUD operations.

Provides async database operations for the Product model including
create, lookup by external ID, and existence checks.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....models.product import Product
from ..schemas.schemas import ProductCreate


class ProductRepository:
    """Repository for Product database operations.

    Args:
        session: An async SQLAlchemy session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: ProductCreate) -> Product:
        """Create a new product in PostgreSQL.

        Args:
            data: Product creation data.

        Returns:
            The newly created Product instance with generated ID.
        """
        product = Product(
            external_id=data.external_id,
            store_id=data.store_id,
            title=data.title,
            description=data.description,
            price=data.price,
            currency=data.currency,
            image_url=data.image_url,
            product_url=data.product_url,
        )
        self.session.add(product)
        await self.session.flush()
        return product

    async def get_by_external_id(
        self, external_id: str, store_id: str
    ) -> Product | None:
        """Look up a product by its external ID and store ID.

        Args:
            external_id: The product's external identifier.
            store_id: The store the product belongs to.

        Returns:
            The Product if found, None otherwise.
        """
        result = await self.session.execute(
            select(Product).where(
                Product.external_id == external_id,
                Product.store_id == store_id,
            )
        )
        return result.scalar_one_or_none()

    async def exists(self, external_id: str, store_id: str) -> bool:
        """Check if a product exists (faster than full get).

        Args:
            external_id: The product's external identifier.
            store_id: The store the product belongs to.

        Returns:
            True if the product exists.
        """
        result = await self.session.execute(
            select(Product.id)
            .where(
                Product.external_id == external_id,
                Product.store_id == store_id,
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
