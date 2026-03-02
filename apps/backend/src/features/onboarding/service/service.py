"""Onboarding service: orchestrates photo upload, calibration, and user vector computation.

Handles the three-step onboarding flow:
1. Photo upload with quality validation and embedding generation
2. Calibration item selection via cold-start service
3. Calibration completion with user vector and price profile computation
"""

from __future__ import annotations

import logging
from io import BytesIO
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.ai.service.embedding_service import EmbeddingService
from src.features.ai.service.quality_gate import QualityGateService
from src.features.clustering.service.cold_start_service import ColdStartService
from src.features.onboarding.schemas.schemas import (
    CalibrationItem,
    CalibrationItemsResponse,
    PhotoUploadResponse,
)
from src.features.storage.service.service import S3StorageService
from src.models.product import Product

logger = logging.getLogger(__name__)

# Embedding dimension expected by the model
_EMBEDDING_DIM = 768


class OnboardingService:
    """Service orchestrating the onboarding flow.

    Args:
        embedding_service: Loaded FashionSigLIP embedding service.
        quality_gate: Image quality validation service.
        storage_service: S3-compatible storage service.
        cold_start_service: Cold-start feed service for calibration items.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        quality_gate: QualityGateService,
        storage_service: S3StorageService,
        cold_start_service: ColdStartService,
    ) -> None:
        self._embedding_service = embedding_service
        self._quality_gate = quality_gate
        self._storage_service = storage_service
        self._cold_start_service = cold_start_service

    async def upload_and_embed_photo(
        self, file: UploadFile, user_id: UUID
    ) -> PhotoUploadResponse:
        """Upload a photo, validate quality, store in S3, and generate embedding.

        Args:
            file: Uploaded image file from the user.
            user_id: Authenticated user's ID.

        Returns:
            PhotoUploadResponse with S3 key, URL, and 768-dim embedding.

        Raises:
            HTTPException: 422 if image fails quality validation.
        """
        # Read file bytes and create PIL Image
        file_bytes = await file.read()
        try:
            image = Image.open(BytesIO(file_bytes))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid image file. Could not open as an image.",
            )

        # Validate image quality
        quality_result = self._quality_gate.validate_image(
            image, file_size_bytes=len(file_bytes)
        )
        if not quality_result.passed:
            issues = [issue.value for issue in quality_result.issues]
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Image failed quality validation",
                    "issues": issues,
                    "blur_score": quality_result.blur_score,
                    "width": quality_result.width,
                    "height": quality_result.height,
                },
            )

        # Upload to S3
        s3_key = f"user_photos/{user_id}/{uuid4()}.jpg"

        # Reset file position for S3 upload
        await file.seek(0)
        url = await self._storage_service.upload_file(
            file=file,
            key=s3_key,
            content_type="image/jpeg",
        )

        # Generate embedding via FashionSigLIP
        embedding = await self._embedding_service.get_embedding(image)

        logger.info(
            "Photo uploaded and embedded for user %s: key=%s, embedding_dim=%d",
            user_id,
            s3_key,
            len(embedding),
        )

        return PhotoUploadResponse(
            key=s3_key,
            url=url,
            embedding=embedding,
        )

    async def get_calibration_items(
        self,
        embeddings: list[list[float]],
        session: AsyncSession,
        feed_size: int = 15,
    ) -> CalibrationItemsResponse:
        """Get calibration items from the cold-start service.

        Validates embedding dimensions, calls the cold-start service for
        product recommendations with diversity injection, then enriches
        each match with product details from PostgreSQL.

        Args:
            embeddings: 1-2 photo embedding vectors (768-dim each).
            session: Async SQLAlchemy session for product lookup.
            feed_size: Number of calibration items to return. Defaults to 15.

        Returns:
            CalibrationItemsResponse with calibration items and total count.

        Raises:
            HTTPException: 422 if embedding dimensions are incorrect.
        """
        # Validate embedding dimensions
        for i, embedding in enumerate(embeddings):
            if len(embedding) != _EMBEDDING_DIM:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Embedding at index {i} has {len(embedding)} dimensions, "
                        f"expected {_EMBEDDING_DIM}."
                    ),
                )

        # Get cold-start feed with diversity injection
        cold_start_response = await self._cold_start_service.get_cold_start_feed(
            embeddings=embeddings,
            feed_size=feed_size,
        )

        if not cold_start_response.matches:
            return CalibrationItemsResponse(items=[], total=0)

        # Collect product IDs and their diversity flags
        product_ids = [match.product_id for match in cold_start_response.matches]
        diversity_map = {
            match.product_id: match.is_diversity
            for match in cold_start_response.matches
        }

        # Look up product details from PostgreSQL
        product_uuids = []
        for pid in product_ids:
            try:
                product_uuids.append(UUID(pid))
            except ValueError:
                logger.warning("Invalid product UUID from cold-start: %s", pid)
                continue

        stmt = select(Product).where(Product.id.in_(product_uuids))
        result = await session.execute(stmt)
        products_by_id = {str(p.id): p for p in result.scalars().all()}

        # Transform matches into CalibrationItem list, preserving order
        items: list[CalibrationItem] = []
        for pid in product_ids:
            product = products_by_id.get(pid)
            if product is None:
                logger.warning("Product %s not found in PostgreSQL, skipping", pid)
                continue
            items.append(
                CalibrationItem(
                    product_id=pid,
                    title=product.title,
                    price=float(product.price),
                    currency=product.currency,
                    image_url=product.image_url,
                    is_diversity=diversity_map.get(pid, False),
                )
            )

        logger.info(
            "Retrieved %d calibration items (%d diversity)",
            len(items),
            sum(1 for item in items if item.is_diversity),
        )

        return CalibrationItemsResponse(
            items=items,
            total=len(items),
        )
