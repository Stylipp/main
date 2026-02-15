"""Product ingestion pipeline that orchestrates quality validation, embedding generation, and storage.

This service coordinates the full ingestion flow:
1. Duplicate detection via ProductRepository
2. Image fetching from URL
3. Quality validation via QualityGateService
4. Embedding generation via EmbeddingService (FashionSigLIP)
5. Storage in PostgreSQL (metadata) and Qdrant (embeddings)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from io import BytesIO
from typing import TYPE_CHECKING
from uuid import UUID

import httpx
from PIL import Image
from qdrant_client.models import PointStruct

if TYPE_CHECKING:
    from qdrant_client import AsyncQdrantClient

    from ...ai.service.embedding_service import EmbeddingService
    from ...ai.service.quality_gate import QualityGateService
    from ..schemas.schemas import ProductCreate
    from .product_repository import ProductRepository

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Result of a single product ingestion attempt.

    Attributes:
        success: Whether the product was successfully ingested.
        product_id: The UUID of the created product (if successful).
        error: Human-readable error message (if failed).
        quality_issues: List of quality issue codes (if quality check failed).
    """

    success: bool
    product_id: UUID | None = None
    error: str | None = None
    quality_issues: list[str] = field(default_factory=list)


class IngestionService:
    """Orchestrates the full product ingestion pipeline.

    Coordinates image fetching, quality validation, embedding generation,
    and storage across PostgreSQL and Qdrant.

    Args:
        repository: ProductRepository for database operations.
        embedding_service: EmbeddingService for generating image embeddings.
        quality_gate: QualityGateService for image validation.
        qdrant_client: AsyncQdrantClient for vector storage.
        collection_name: Qdrant collection name. Defaults to "products".
    """

    def __init__(
        self,
        repository: ProductRepository,
        embedding_service: EmbeddingService,
        quality_gate: QualityGateService,
        qdrant_client: AsyncQdrantClient,
        collection_name: str = "products",
    ) -> None:
        self.repository = repository
        self.embedding_service = embedding_service
        self.quality_gate = quality_gate
        self.qdrant = qdrant_client
        self.collection_name = collection_name

    async def ingest_product(self, product_data: ProductCreate) -> IngestionResult:
        """Run the full ingestion pipeline for a single product.

        Pipeline steps:
        1. Check if product already exists (duplicate detection)
        2. Fetch image from URL
        3. Validate image quality
        4. Generate embedding via FashionSigLIP
        5. Store metadata in PostgreSQL
        6. Store embedding in Qdrant

        Args:
            product_data: Product data including image URL.

        Returns:
            IngestionResult with success status and product ID or error details.
        """
        # 1. Check for duplicate
        if await self.repository.exists(
            product_data.external_id, product_data.store_id
        ):
            return IngestionResult(success=False, error="Product already exists")

        # 2. Fetch image
        try:
            image, file_size = await self._fetch_image(product_data.image_url)
        except Exception as e:
            logger.warning("Failed to fetch image %s: %s", product_data.image_url, e)
            return IngestionResult(success=False, error=f"Image fetch failed: {e!s}")

        # 3. Validate quality
        quality_result = self.quality_gate.validate_image(image, file_size)
        if not quality_result.passed:
            return IngestionResult(
                success=False,
                error="Quality check failed",
                quality_issues=[issue.value for issue in quality_result.issues],
            )

        # 4. Generate embedding
        try:
            embedding = await self.embedding_service.get_embedding(image)
        except Exception as e:
            logger.error("Embedding generation failed: %s", e)
            return IngestionResult(success=False, error=f"Embedding failed: {e!s}")

        # 5. Store in PostgreSQL
        product = await self.repository.create(product_data)

        # 6. Store embedding in Qdrant
        await self.qdrant.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=str(product.id),
                    vector=embedding,
                    payload={
                        "product_id": str(product.id),
                        "store_id": product.store_id,
                        "price": float(product.price),
                        "created_at": product.created_at.isoformat(),
                    },
                )
            ],
        )

        return IngestionResult(success=True, product_id=product.id)

    async def _fetch_image(self, url: str) -> tuple[Image.Image, int]:
        """Fetch image from URL, return PIL Image and file size in bytes.

        Args:
            url: Image URL to fetch.

        Returns:
            Tuple of (PIL Image, file size in bytes).

        Raises:
            httpx.HTTPStatusError: If the HTTP request fails.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.content
            return Image.open(BytesIO(data)), len(data)
