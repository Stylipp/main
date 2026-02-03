"""Pydantic schemas for the AI/embedding feature.

These schemas define the request/response models for the embedding
service endpoints.
"""

from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    """Request schema for generating an image embedding."""

    image_url: str = Field(..., description="URL of image to embed")


class EmbeddingResponse(BaseModel):
    """Response schema containing the generated embedding."""

    embedding: list[float] = Field(
        ..., description="768-dimensional embedding vector"
    )
    dimension: int = Field(default=768, description="Embedding dimension")


class EmbeddingHealthResponse(BaseModel):
    """Response schema for the AI health check endpoint."""

    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether the model is loaded")
    model_name: str = Field(
        default="Marqo/marqo-fashionSigLIP",
        description="Name of the loaded model",
    )
    embedding_dimension: int = Field(
        default=768, description="Output embedding dimension"
    )
