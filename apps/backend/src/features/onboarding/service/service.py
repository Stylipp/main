"""Onboarding service: orchestrates photo upload, calibration, and user vector computation.

Handles the three-step onboarding flow:
1. Photo upload with quality validation and embedding generation
2. Calibration item selection via cold-start service
3. Calibration completion with user vector and price profile computation
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from io import BytesIO
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings
from src.core.profile_state import compute_profile_confidence
from src.features.ai.service.embedding_service import EmbeddingService
from src.features.ai.service.quality_gate import QualityGateService
from src.features.clustering.service.cold_start_service import ColdStartService
from src.features.onboarding.schemas.schemas import (
    CalibrationCompleteRequest,
    CalibrationCompleteResponse,
    CalibrationItem,
    CalibrationItemsResponse,
    PhotoUploadResponse,
)
from src.features.onboarding.service.user_vector import (
    compute_user_vector,
    initialize_price_profile,
)
from src.features.storage.service.service import S3StorageService
from src.models.product import Product
from src.models.user import User

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
        qdrant_client: AsyncQdrantClient,
        settings: Settings,
    ) -> None:
        self._embedding_service = embedding_service
        self._quality_gate = quality_gate
        self._storage_service = storage_service
        self._cold_start_service = cold_start_service
        self._qdrant = qdrant_client
        self._settings = settings

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

    async def complete_calibration(
        self,
        user_id: UUID,
        request: CalibrationCompleteRequest,
        session: AsyncSession,
    ) -> CalibrationCompleteResponse:
        """Complete calibration: compute user vector, price profile, store results.

        Fetches liked/disliked product embeddings from Qdrant, computes the
        user style vector via Modified Rocchio, initializes the price profile
        from liked item prices, stores the user vector in Qdrant's
        user_profiles collection, and updates the User record in PostgreSQL.

        Args:
            user_id: Authenticated user's ID.
            request: Calibration completion request with photo embeddings
                     and liked/disliked product IDs.
            session: Async SQLAlchemy session.

        Returns:
            CalibrationCompleteResponse with success status and price profile.

        Raises:
            HTTPException: 422 if validation fails, 404 if user not found.
        """
        # Validate photo embeddings
        for i, emb in enumerate(request.photo_embeddings):
            if len(emb) != _EMBEDDING_DIM:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Photo embedding at index {i} has {len(emb)} dimensions, "
                        f"expected {_EMBEDDING_DIM}."
                    ),
                )

        # Fetch liked product embeddings from Qdrant
        liked_points = await self._qdrant.retrieve(
            collection_name=self._settings.qdrant_collection,
            ids=request.liked_product_ids,
            with_vectors=True,
            with_payload=True,
        )
        if not liked_points:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No liked product embeddings found in Qdrant.",
            )

        liked_embeddings = [
            point.vector for point in liked_points if point.vector is not None
        ]

        # Fetch disliked product embeddings from Qdrant
        disliked_embeddings: list[list[float]] = []
        if request.disliked_product_ids:
            disliked_points = await self._qdrant.retrieve(
                collection_name=self._settings.qdrant_collection,
                ids=request.disliked_product_ids,
                with_vectors=True,
                with_payload=False,
            )
            disliked_embeddings = [
                point.vector for point in disliked_points if point.vector is not None
            ]

        # Compute user style vector via Modified Rocchio
        user_vector = compute_user_vector(
            photo_embeddings=request.photo_embeddings,
            liked_embeddings=liked_embeddings,
            disliked_embeddings=disliked_embeddings,
        )

        # Compute price profile from liked items' prices (from PostgreSQL)
        liked_uuids = []
        for pid in request.liked_product_ids:
            try:
                liked_uuids.append(UUID(pid))
            except ValueError:
                continue

        stmt = select(Product.price).where(Product.id.in_(liked_uuids))
        result = await session.execute(stmt)
        liked_prices = [float(row[0]) for row in result.all()]

        price_profile = initialize_price_profile(liked_prices)

        # Store user vector in Qdrant user_profiles collection
        await self._qdrant.upsert(
            collection_name=self._settings.user_profiles_collection,
            points=[
                PointStruct(
                    id=str(user_id),
                    vector=user_vector,
                    payload={
                        "user_id": str(user_id),
                        "photo_count": len(request.photo_embeddings),
                        "liked_count": len(request.liked_product_ids),
                        "disliked_count": len(request.disliked_product_ids),
                    },
                )
            ],
        )

        # Update User in PostgreSQL
        stmt_user = select(User).where(User.id == user_id)
        user_result = await session.execute(stmt_user)
        user = user_result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        user.onboarding_completed = True
        user.price_profile = price_profile
        calibration_interaction_count = len(request.liked_product_ids) + len(
            request.disliked_product_ids
        )
        user.interaction_count = max(
            user.interaction_count, calibration_interaction_count
        )
        user.profile_version += 1
        user.last_profile_update_at = datetime.now(timezone.utc)
        user.profile_confidence = compute_profile_confidence(user.interaction_count)
        if user.profile_source is None:
            user.profile_source = "onboarding"
        await session.commit()

        logger.info(
            "Calibration completed for user %s: vector_dim=%d, "
            "liked=%d, disliked=%d, price_profile=%s",
            user_id,
            len(user_vector),
            len(request.liked_product_ids),
            len(request.disliked_product_ids),
            price_profile,
        )

        return CalibrationCompleteResponse(
            success=True,
            onboarding_completed=True,
            cluster_count=len(liked_embeddings),
            price_profile=price_profile,
        )
