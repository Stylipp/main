"""Expand user model with onboarding fields.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-02 00:01:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("display_name", sa.String(100), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    op.add_column(
        "users",
        sa.Column("price_profile", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "price_profile")
    op.drop_column("users", "onboarding_completed")
    op.drop_column("users", "display_name")
