"""Pydantic models for clustering and cold-start API contracts.

Defines request/response schemas for:
- Cluster stats and info
- Cold-start matching (user photo embeddings → product recommendations)
- Cluster rebuild results
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ClusterInfo(BaseModel):
    """Metadata for a single style cluster."""

    cluster_index: int
    product_count: int
    prior_probability: float


class ClusterStatsResponse(BaseModel):
    """Aggregated statistics across all style clusters."""

    total_clusters: int
    total_products: int
    clusters: list[ClusterInfo]
    silhouette_score: float | None = None


class ColdStartRequest(BaseModel):
    """Request body for cold-start matching.

    Contains 1-2 photo embeddings from user uploads during onboarding.
    """

    embeddings: list[list[float]] = Field(
        ...,
        min_length=1,
        max_length=2,
        description="1-2 photo embeddings (768-dim each) from user uploads",
    )


class ColdStartMatch(BaseModel):
    """A single product match in the cold-start feed."""

    product_id: str
    score: float
    cluster_index: int
    is_diversity: bool = Field(
        default=False,
        description="True if this item is from an adjacent diversity cluster",
    )


class ColdStartResponse(BaseModel):
    """Response from the cold-start feed endpoint."""

    matches: list[ColdStartMatch]
    primary_clusters: list[int]
    diversity_clusters: list[int]
    total_matches: int


class RebuildResponse(BaseModel):
    """Response after a cluster rebuild operation."""

    k: int
    silhouette_score: float
    product_count: int
    cluster_sizes: dict[int, int]
