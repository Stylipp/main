"""FeedbackService: Records user interactions with products.

Handles the persistence of like/dislike/save actions, looking up
products by external_id (Qdrant point ID) to obtain the UUID FK.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.product import Product
from src.models.user_interaction import UserInteraction

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for recording user feedback on products."""

    async def record_feedback(
        self,
        user_id: UUID,
        product_id_external: str,
        action: str,
        session: AsyncSession,
    ) -> UserInteraction:
        """Record a user interaction (like/dislike/save) with a product.

        Args:
            user_id: The authenticated user's UUID.
            product_id_external: The product's external_id (Qdrant point ID).
            action: The feedback action string (like, dislike, save).
            session: Async SQLAlchemy database session.

        Returns:
            The created UserInteraction record.

        Raises:
            ValueError: If no product is found with the given external_id.
        """
        # Lookup product by external_id to get the UUID for FK
        stmt = select(Product).where(Product.external_id == product_id_external)
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()

        if product is None:
            raise ValueError(
                f"Product not found with external_id: {product_id_external}"
            )

        # Create interaction record (no uniqueness constraint — users can
        # interact with the same product multiple times)
        interaction = UserInteraction(
            user_id=user_id,
            product_id=product.id,
            action=action,
        )
        session.add(interaction)
        await session.commit()
        await session.refresh(interaction)

        logger.info(
            "Recorded feedback: user=%s product=%s action=%s",
            user_id,
            product_id_external,
            action,
        )

        return interaction
