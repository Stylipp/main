from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class ExposureLog(Base):
    __tablename__ = "exposure_logs"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True
    )
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    feed_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    shown_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    action: Mapped[str | None] = mapped_column(String(16), nullable=True)
    action_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dwell_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "product_id",
            "session_id",
            name="uq_exposure_logs_user_product_session",
        ),
        Index(
            "ix_exposure_logs_user_shown_at",
            "user_id",
            "shown_at",
        ),
        Index(
            "ix_exposure_logs_session",
            "session_id",
        ),
    )
