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

    from ....models.product import Product
    from ...ai.service.embedding_service import EmbeddingService
    from ...ai.service.quality_gate import QualityGateService
    from ..schemas.schemas import ProductCreate
    from .product_repository import ProductRepository

from ..utils.category import normalize_raw_categories

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Result of a single product ingestion attempt.

    Attributes:
        success: Whether the product was successfully ingested.
        product_id: The UUID of the created product (if successful).
        error: Human-readable error message (if failed).
        quality_issues: List of quality issue codes (if quality check failed).
        updated: Whether this was an update of an existing product (vs new creation).
    """

    success: bool
    product_id: UUID | None = None
    error: str | None = None
    quality_issues: list[str] = field(default_factory=list)
    updated: bool = False


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

    def _canonicalize_product_data(self, product_data: ProductCreate) -> ProductCreate:
        """Normalize raw categories and derive the canonical category server-side."""
        if not product_data.raw_categories:
            return product_data

        category, raw_categories = normalize_raw_categories(product_data.raw_categories)
        return product_data.model_copy(
            update={"category": category, "raw_categories": raw_categories}
        )

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
        product_data = self._canonicalize_product_data(product_data)

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
                        "category": product.category,
                        "created_at": product.created_at.isoformat(),
                    },
                )
            ],
        )

        return IngestionResult(success=True, product_id=product.id)

    async def ingest_or_update_product(
        self, product_data: ProductCreate
    ) -> IngestionResult:
        """Ingest a new product or update an existing one.

        Looks up the product by external_id + store_id. If it doesn't exist,
        runs the full ingestion pipeline. If it does exist, updates metadata
        and re-embeds only when the image URL has changed.

        Args:
            product_data: Product data from the scraper.

        Returns:
            IngestionResult with success status, product ID, and updated flag.
        """
        product_data = self._canonicalize_product_data(product_data)
        existing = await self.repository.get_by_external_id(
            product_data.external_id, product_data.store_id
        )
        if existing is None:
            return await self._ingest_new(product_data)
        return await self._update_existing(existing, product_data)

    async def _ingest_new(self, product_data: ProductCreate) -> IngestionResult:
        """Run the full ingestion pipeline for a new product (no duplicate check).

        Args:
            product_data: Product data to ingest.

        Returns:
            IngestionResult with success status and product ID or error details.
        """
        # 1. Fetch image
        try:
            image, file_size = await self._fetch_image(product_data.image_url)
        except Exception as e:
            logger.warning("Failed to fetch image %s: %s", product_data.image_url, e)
            return IngestionResult(success=False, error=f"Image fetch failed: {e!s}")

        # 2. Validate quality
        quality_result = self.quality_gate.validate_image(image, file_size)
        if not quality_result.passed:
            return IngestionResult(
                success=False,
                error="Quality check failed",
                quality_issues=[issue.value for issue in quality_result.issues],
            )

        # 3. Generate embedding
        try:
            embedding = await self.embedding_service.get_embedding(image)
        except Exception as e:
            logger.error("Embedding generation failed: %s", e)
            return IngestionResult(success=False, error=f"Embedding failed: {e!s}")

        # 4. Store in PostgreSQL
        product = await self.repository.create(product_data)

        # 5. Store embedding in Qdrant
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
                        "category": product.category,
                        "created_at": product.created_at.isoformat(),
                    },
                )
            ],
        )

        return IngestionResult(success=True, product_id=product.id)

    async def _update_existing(
        self, existing: Product, product_data: ProductCreate
    ) -> IngestionResult:
        """Update an existing product's metadata, re-embedding if image changed.

        Args:
            existing: The existing Product record from the database.
            product_data: New product data from the scraper.

        Returns:
            IngestionResult with success status and updated flag set to True.
        """
        image_changed = existing.image_url != product_data.image_url

        # 1. Update metadata in PostgreSQL
        update_fields = {
            "title": product_data.title,
            "description": product_data.description,
            "price": product_data.price,
            "currency": product_data.currency,
            "image_url": product_data.image_url,
            "product_url": product_data.product_url,
            "category": product_data.category.value,
            "raw_categories": product_data.raw_categories,
        }
        await self.repository.update(
            product_data.external_id, product_data.store_id, update_fields
        )

        payload = {
            "product_id": str(existing.id),
            "store_id": existing.store_id,
            "price": float(product_data.price),
            "category": product_data.category.value,
            "created_at": existing.created_at.isoformat(),
        }

        # 2. If image changed, re-fetch, validate, embed, and update Qdrant
        if image_changed:
            try:
                image, file_size = await self._fetch_image(product_data.image_url)
            except Exception as e:
                logger.warning(
                    "Failed to fetch updated image %s: %s",
                    product_data.image_url,
                    e,
                )
                return IngestionResult(
                    success=False, error=f"Image fetch failed: {e!s}"
                )

            quality_result = self.quality_gate.validate_image(image, file_size)
            if not quality_result.passed:
                return IngestionResult(
                    success=False,
                    error="Quality check failed",
                    quality_issues=[issue.value for issue in quality_result.issues],
                )

            try:
                embedding = await self.embedding_service.get_embedding(image)
            except Exception as e:
                logger.error("Embedding generation failed on update: %s", e)
                return IngestionResult(success=False, error=f"Embedding failed: {e!s}")

            await self.qdrant.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=str(existing.id),
                        vector=embedding,
                        payload=payload,
                    )
                ],
            )
        else:
            await self.qdrant.set_payload(
                collection_name=self.collection_name,
                payload=payload,
                points=[str(existing.id)],
            )

        return IngestionResult(success=True, product_id=existing.id, updated=True)

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
