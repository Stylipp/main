from decimal import Decimal
from typing import Optional

from sqlalchemy import Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Product(Base):
    __tablename__ = "products"

    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    store_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    image_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    product_url: Mapped[str] = mapped_column(String(2048), nullable=False)

    __table_args__ = (
        Index("ix_products_external_id", "external_id"),
        Index("ix_products_store_id", "store_id"),
        Index("ix_products_created_at", "created_at"),
    )
