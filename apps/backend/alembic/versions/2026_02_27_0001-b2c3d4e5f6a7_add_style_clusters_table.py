"""Add style_clusters table.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-27 00:01:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "style_clusters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_index", sa.Integer(), nullable=False, unique=True),
        sa.Column("product_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prior_probability", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
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
    )
    op.create_index(
        "ix_style_clusters_cluster_index", "style_clusters", ["cluster_index"]
    )


def downgrade() -> None:
    op.drop_index("ix_style_clusters_cluster_index", table_name="style_clusters")
    op.drop_table("style_clusters")
