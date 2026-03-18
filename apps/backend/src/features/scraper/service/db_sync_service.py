"""Database sync service for upserting scraped products into PostgreSQL.

Coordinates product creation, updates, and removal tracking after the
change detection engine identifies new or changed products.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from ...products.schemas.schemas import ProductCreate
from ...products.service.product_repository import ProductRepository
from ....models.product import Product
from ..schemas.schemas import ScrapedProduct

logger = logging.getLogger(__name__)


class DbSyncService:
    """Syncs scraped product changes to PostgreSQL.

    Args:
        session: An async SQLAlchemy session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._repo = ProductRepository(session)

    async def sync_new_products(
        self, products: list[ScrapedProduct], woo_store_id: str
    ) -> list[Product]:
        """Create new products in PostgreSQL.

        Converts each ScrapedProduct to a ProductCreate and persists it.
        Products without images are skipped because embeddings cannot be
        generated without them.

        Args:
            products: List of newly discovered scraped products.
            woo_store_id: The store identifier used as ``store_id``.

        Returns:
            List of created Product ORM instances.
        """
        created: list[Product] = []

        for sp in products:
            if not sp.image_urls:
                logger.debug(
                    "Skipping product %s — no images available", sp.external_id
                )
                continue

            product_data = ProductCreate(
                external_id=sp.external_id,
                store_id=woo_store_id,
                title=sp.title,
                description=sp.description,
                price=sp.price if sp.price is not None else Decimal("0"),
                currency=sp.currency,
                image_url=sp.image_urls[0],
                product_url=sp.url,
            )
            product = await self._repo.create(product_data)
            created.append(product)

        logger.info("%d new products synced to PostgreSQL", len(created))
        return created

    async def sync_changed_products(
        self, products: list[ScrapedProduct], woo_store_id: str
    ) -> list[Product]:
        """Update changed products in PostgreSQL.

        Builds an update dict from ScrapedProduct fields and delegates
        to ``ProductRepository.update``.

        Args:
            products: List of changed scraped products.
            woo_store_id: The store identifier used as ``store_id``.

        Returns:
            List of updated Product ORM instances.
        """
        updated: list[Product] = []

        for sp in products:
            update_dict: dict = {
                "title": sp.title,
                "description": sp.description,
                "price": sp.price if sp.price is not None else Decimal("0"),
                "product_url": sp.url,
            }
            if sp.image_urls:
                update_dict["image_url"] = sp.image_urls[0]

            product = await self._repo.update(
                external_id=sp.external_id,
                store_id=woo_store_id,
                data=update_dict,
            )
            if product is not None:
                updated.append(product)

        logger.info("%d changed products updated in PostgreSQL", len(updated))
        return updated

    async def remove_products(self, external_ids: list[str], store_id: str) -> int:
        """Log removed products but retain them in PostgreSQL.

        Products may still be referenced by user interactions (swipes,
        saves, collections) so we do not delete them.  Actual deletion
        or archival is a future concern.

        Args:
            external_ids: External IDs of products no longer in the sitemap.
            store_id: The store the products belong to.

        Returns:
            Count of products flagged as removed.
        """
        count = len(external_ids)
        if count:
            logger.warning(
                "%d products removed from store %s sitemap but retained in database",
                count,
                store_id,
            )
        return count
