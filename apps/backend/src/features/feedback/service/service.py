"""FeedbackService: Records user interactions with products.

Handles the persistence of like/dislike/save actions, looking up
products by external_id (Qdrant point ID) to obtain the UUID FK.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.profile_state import compute_profile_confidence
from src.models.product import Product
from src.models.user import User
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
            product_id_external: The product's UUID (primary key) as returned
                by the feed endpoint.
            action: The feedback action string (like, dislike, save).
            session: Async SQLAlchemy database session.

        Returns:
            The created UserInteraction record.

        Raises:
            ValueError: If no product is found with the given id.
        """
        # Lookup product by primary key UUID (the feed endpoint returns Product.id)
        try:
            product_uuid = UUID(product_id_external)
        except ValueError:
            raise ValueError(f"Invalid product id: {product_id_external}")

        stmt = select(Product).where(Product.id == product_uuid)
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()

        if product is None:
            raise ValueError(f"Product not found with id: {product_id_external}")

        # Create interaction record (no uniqueness constraint — users can
        # interact with the same product multiple times)
        interaction = UserInteraction(
            user_id=user_id,
            product_id=product.id,
            action=action,
        )
        session.add(interaction)

        stmt_user = select(User).where(User.id == user_id)
        user_result = await session.execute(stmt_user)
        user = user_result.scalar_one_or_none()
        if user is not None:
            user.interaction_count += 1
            user.profile_confidence = compute_profile_confidence(
                user.interaction_count
            )

        await session.commit()
        await session.refresh(interaction)

        logger.info(
            "Recorded feedback: user=%s product=%s action=%s",
            user_id,
            product_id_external,
            action,
        )

        return interaction
