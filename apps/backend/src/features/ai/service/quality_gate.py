"""Image quality gate service for validating product images before embedding generation.

This service validates images for minimum quality requirements including:
- Dimension checks (minimum 400px on smallest side)
- File size checks (50KB - 10MB)
- Blur detection using Laplacian variance

Purpose: Block blurry, too-small, or invalid images that would pollute style
vectors and degrade recommendation quality.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class QualityIssue(str, Enum):
    """Types of image quality issues that can be detected."""

    TOO_SMALL = "too_small"
    TOO_LARGE = "too_large"
    TOO_BLURRY = "too_blurry"
    INVALID_FORMAT = "invalid_format"


@dataclass
class QualityResult:
    """Result of an image quality validation check.

    Attributes:
        passed: Whether the image passed all quality checks.
        issues: List of quality issues found.
        blur_score: Laplacian variance score (higher = sharper).
        width: Image width in pixels.
        height: Image height in pixels.
        file_size_bytes: File size in bytes.
    """

    passed: bool
    issues: list[QualityIssue]
    blur_score: float | None = None
    width: int | None = None
    height: int | None = None
    file_size_bytes: int | None = None


class QualityGateService:
    """Service for validating image quality before embedding generation.

    Uses configurable thresholds for dimension, file size, and blur detection.
    Blur detection uses the Laplacian variance method via OpenCV.

    Args:
        min_dimension: Minimum pixel size for the smallest side. Defaults to 400.
        min_file_size: Minimum file size in bytes. Defaults to 50KB.
        max_file_size: Maximum file size in bytes. Defaults to 10MB.
        blur_threshold: Laplacian variance threshold. Below this = blurry.
            Defaults to 100.0.
        normalize_size: Normalize images to this size for consistent blur
            scoring. Defaults to 500.
    """

    def __init__(
        self,
        min_dimension: int = 400,
        min_file_size: int = 50 * 1024,  # 50KB
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        blur_threshold: float = 100.0,
        normalize_size: int = 500,
    ) -> None:
        self.min_dimension = min_dimension
        self.min_file_size = min_file_size
        self.max_file_size = max_file_size
        self.blur_threshold = blur_threshold
        self.normalize_size = normalize_size

    def validate_image(
        self, image: Image.Image, file_size_bytes: int | None = None
    ) -> QualityResult:
        """Validate image quality against configured thresholds.

        Args:
            image: A PIL Image object to validate.
            file_size_bytes: Optional file size in bytes for size validation.

        Returns:
            QualityResult with pass/fail status and any issues found.
        """
        issues: list[QualityIssue] = []
        width, height = image.size

        # Dimension check
        min_side = min(width, height)
        if min_side < self.min_dimension:
            issues.append(QualityIssue.TOO_SMALL)

        # File size check (if provided)
        if file_size_bytes is not None:
            if file_size_bytes < self.min_file_size:
                issues.append(QualityIssue.TOO_SMALL)
            elif file_size_bytes > self.max_file_size:
                issues.append(QualityIssue.TOO_LARGE)

        # Blur detection
        blur_score = self._calculate_blur_score(image)
        if blur_score < self.blur_threshold:
            issues.append(QualityIssue.TOO_BLURRY)

        return QualityResult(
            passed=len(issues) == 0,
            issues=issues,
            blur_score=blur_score,
            width=width,
            height=height,
            file_size_bytes=file_size_bytes,
        )

    def _calculate_blur_score(self, image: Image.Image) -> float:
        """Calculate Laplacian variance as blur score.

        Higher values indicate sharper images. Images are normalized to a
        consistent size before scoring for comparable results across
        different resolutions.

        Args:
            image: A PIL Image object.

        Returns:
            Laplacian variance score as a float.
        """
        # Convert to grayscale
        gray = image.convert("L")

        # Normalize size for consistent scoring
        if max(gray.size) > self.normalize_size:
            ratio = self.normalize_size / max(gray.size)
            new_size = (int(gray.width * ratio), int(gray.height * ratio))
            gray = gray.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to numpy and calculate Laplacian variance
        img_array = np.array(gray)
        laplacian = cv2.Laplacian(img_array, cv2.CV_64F)
        return float(laplacian.var())

    async def validate_from_url(self, image_url: str) -> QualityResult:
        """Fetch an image from a URL and validate its quality.

        Args:
            image_url: URL of the image to validate.

        Returns:
            QualityResult with pass/fail status and any issues found.

        Raises:
            httpx.HTTPError: If the image cannot be fetched.
            PIL.UnidentifiedImageError: If the fetched data is not a valid image.
        """
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(image_url, timeout=30.0)
            response.raise_for_status()

            from io import BytesIO

            image_data = response.content
            image = Image.open(BytesIO(image_data))

            return self.validate_image(image, file_size_bytes=len(image_data))
