from uuid import UUID

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        Index("ix_user_interactions_user_product", "user_id", "product_id"),
        Index(
            "ix_user_interactions_user_action_time",
            "user_id",
            "action",
            "created_at",
        ),
    )
