"""Add archived_at to products.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-04-19 00:01:00
"""

from alembic import op
import sqlalchemy as sa


revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_products_archived_at", "products", ["archived_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_products_archived_at", table_name="products")
    op.drop_column("products", "archived_at")
