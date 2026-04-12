"""Add profile-state fields to users.

Revision ID: d4e5f6a7b8c9
Revises: 045c715cd7fc
Create Date: 2026-04-12 00:01:00
"""

from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a7b8c9"
down_revision = "045c715cd7fc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("interaction_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("profile_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("last_profile_update_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("profile_confidence", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("profile_source", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "profile_source")
    op.drop_column("users", "profile_confidence")
    op.drop_column("users", "last_profile_update_at")
    op.drop_column("users", "profile_version")
    op.drop_column("users", "interaction_count")
