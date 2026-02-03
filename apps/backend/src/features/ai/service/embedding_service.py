"""FashionSigLIP embedding service for generating 768-dimensional fashion image embeddings.

This service loads the Marqo/marqo-fashionSigLIP model at startup and provides
async methods for generating embeddings from PIL images. A semaphore limits
concurrent inference to prevent memory issues.

Model details:
    - Model: Marqo/marqo-fashionSigLIP
    - Output: 768-dimensional vectors, normalized for cosine similarity
    - License: Apache 2.0
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Async service for generating fashion image embeddings using FashionSigLIP.

    The model is loaded once at startup via load_model(). All inference calls
    are routed through a semaphore to limit concurrent processing.

    Attributes:
        model: The loaded FashionSigLIP model.
        processor: The model's image processor.
    """

    MODEL_NAME = "Marqo/marqo-fashionSigLIP"
    EMBEDDING_DIM = 768

    def __init__(self, max_concurrent: int = 4) -> None:
        """Initialize the embedding service.

        Args:
            max_concurrent: Maximum number of concurrent inference operations.
                            Defaults to 4 to balance throughput and memory usage.
        """
        self.model = None
        self.processor = None
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._loaded = False

    def load_model(self) -> None:
        """Load the FashionSigLIP model and processor.

        This should be called once during application startup. On first run,
        it will download the model (~600MB) from Hugging Face.

        Raises:
            RuntimeError: If model loading fails.
        """
        from transformers import AutoModel, AutoProcessor

        logger.info("Loading FashionSigLIP model: %s", self.MODEL_NAME)

        try:
            self.model = AutoModel.from_pretrained(
                self.MODEL_NAME,
                trust_remote_code=True,
            )
            self.processor = AutoProcessor.from_pretrained(
                self.MODEL_NAME,
                trust_remote_code=True,
            )
            self.model.eval()
            self._loaded = True
            logger.info("FashionSigLIP model loaded successfully")
        except Exception as e:
            logger.exception("Failed to load FashionSigLIP model")
            raise RuntimeError(f"Model loading failed: {e}") from e

    async def get_embedding(self, image: Image.Image) -> list[float]:
        """Generate a 768-dimensional embedding from a PIL Image.

        Args:
            image: A PIL Image object to embed.

        Returns:
            A list of 768 floats representing the image embedding,
            normalized for cosine similarity.

        Raises:
            RuntimeError: If the model has not been loaded.
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        async with self._semaphore:
            return await asyncio.to_thread(self._inference, image)

    async def get_embeddings_batch(
        self, images: list[Image.Image], batch_size: int = 8
    ) -> list[list[float]]:
        """Generate embeddings for multiple images.

        Processes images in batches for memory efficiency.

        Args:
            images: List of PIL Image objects to embed.
            batch_size: Number of images to process per batch. Defaults to 8.

        Returns:
            List of embeddings, one per input image.

        Raises:
            RuntimeError: If the model has not been loaded.
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        results: list[list[float]] = []

        for i in range(0, len(images), batch_size):
            batch = images[i : i + batch_size]
            async with self._semaphore:
                batch_embeddings = await asyncio.to_thread(self._inference_batch, batch)
                results.extend(batch_embeddings)

        return results

    def _inference(self, image: Image.Image) -> list[float]:
        """Perform single-image inference (runs in thread pool).

        Args:
            image: A PIL Image to embed.

        Returns:
            768-dimensional embedding as a list of floats.
        """
        import torch

        with torch.no_grad():
            inputs = self.processor(images=[image], return_tensors="pt")
            features = self.model.get_image_features(
                inputs["pixel_values"],
                normalize=True,
            )
            return features[0].tolist()

    def _inference_batch(self, images: list[Image.Image]) -> list[list[float]]:
        """Perform batch inference (runs in thread pool).

        Args:
            images: List of PIL Images to embed.

        Returns:
            List of 768-dimensional embeddings.
        """
        import torch

        with torch.no_grad():
            inputs = self.processor(images=images, return_tensors="pt")
            features = self.model.get_image_features(
                inputs["pixel_values"],
                normalize=True,
            )
            return features.tolist()

    @property
    def is_loaded(self) -> bool:
        """Return True if the model has been loaded."""
        return self._loaded
