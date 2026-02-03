"""Add Product model with uuid-ossp extension.

Revision ID: a1b2c3d4e5f6
Revises: 8c1d2f1f0a9b
Create Date: 2026-02-03 14:00:00
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "8c1d2f1f0a9b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create uuid-ossp extension for UUID generation
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create products table
    op.create_table(
        "products",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("store_id", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("image_url", sa.String(2048), nullable=False),
        sa.Column("product_url", sa.String(2048), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("ix_products_external_id", "products", ["external_id"])
    op.create_index("ix_products_store_id", "products", ["store_id"])
    op.create_index("ix_products_created_at", "products", ["created_at"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_products_created_at", table_name="products")
    op.drop_index("ix_products_store_id", table_name="products")
    op.drop_index("ix_products_external_id", table_name="products")

    # Drop products table
    op.drop_table("products")

    # Note: Not dropping uuid-ossp extension as other tables may depend on it
