"""Add exposure_logs table.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-04-19 00:02:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exposure_logs",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("feed_mode", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("shown_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=True),
        sa.Column("action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dwell_ms", sa.Integer(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "product_id",
            "session_id",
            name="uq_exposure_logs_user_product_session",
        ),
    )
    op.create_index(
        op.f("ix_exposure_logs_product_id"),
        "exposure_logs",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_exposure_logs_session",
        "exposure_logs",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "ix_exposure_logs_user_shown_at",
        "exposure_logs",
        ["user_id", "shown_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_exposure_logs_user_id"),
        "exposure_logs",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_exposure_logs_user_id"), table_name="exposure_logs")
    op.drop_index("ix_exposure_logs_user_shown_at", table_name="exposure_logs")
    op.drop_index("ix_exposure_logs_session", table_name="exposure_logs")
    op.drop_index(op.f("ix_exposure_logs_product_id"), table_name="exposure_logs")
    op.drop_table("exposure_logs")
