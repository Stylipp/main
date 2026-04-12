from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    interaction_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    profile_version: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    last_profile_update_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    profile_confidence: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0", nullable=False
    )
    profile_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    price_profile: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
