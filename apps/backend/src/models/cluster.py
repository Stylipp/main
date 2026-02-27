from sqlalchemy import Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class StyleCluster(Base):
    """Style cluster metadata stored in PostgreSQL.

    Centroid vectors are stored in Qdrant only (not duplicated here).
    PostgreSQL stores only metadata: counts, priors, and status.
    """

    __tablename__ = "style_clusters"

    cluster_index: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    product_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prior_probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    __table_args__ = (Index("ix_style_clusters_cluster_index", "cluster_index"),)
