"""S3-compatible storage service using aioboto3 for async operations.

Key patterns:
    - User photos:    user_photos/{user_id}/{uuid}.jpg
    - Product images: products/{product_id}/{uuid}.jpg
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import aioboto3
from botocore.exceptions import ClientError

from src.core.config import get_settings

if TYPE_CHECKING:
    from fastapi import UploadFile

logger = logging.getLogger(__name__)


class S3StorageService:
    """Async S3-compatible storage service for Hetzner Object Storage."""

    def __init__(self) -> None:
        settings = get_settings()
        self._endpoint_url = settings.s3_endpoint_url
        self._access_key = settings.s3_access_key
        self._secret_key = settings.s3_secret_key
        self._bucket = settings.s3_bucket_name
        self._region = settings.s3_region
        self._session = aioboto3.Session()

    def _client(self):
        """Return an async context-manager S3 client."""
        return self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            region_name=self._region,
        )

    async def upload_file(
        self,
        file: UploadFile,
        key: str,
        content_type: str | None = None,
    ) -> str:
        """Upload a file to S3 and return its public URL.

        Args:
            file: FastAPI UploadFile instance.
            key: Object key, e.g. ``user_photos/{user_id}/{uuid}.jpg``.
            content_type: Optional MIME type override.

        Returns:
            The public URL of the uploaded object.
        """
        body = await file.read()
        extra: dict[str, str] = {}
        if content_type or file.content_type:
            extra["ContentType"] = content_type or file.content_type  # type: ignore[assignment]

        async with self._client() as client:
            await client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=body,
                **extra,
            )

        return f"{self._endpoint_url}/{self._bucket}/{key}"

    async def download_file(self, key: str) -> bytes:
        """Download a file from S3 and return its bytes.

        Args:
            key: Object key to download.

        Returns:
            Raw file bytes.
        """
        async with self._client() as client:
            response = await client.get_object(Bucket=self._bucket, Key=key)
            return await response["Body"].read()

    async def delete_file(self, key: str) -> bool:
        """Delete a file from S3.

        Args:
            key: Object key to delete.

        Returns:
            True if deletion succeeded, False on error.
        """
        try:
            async with self._client() as client:
                await client.delete_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            logger.exception("Failed to delete %s", key)
            return False

    async def file_exists(self, key: str) -> bool:
        """Check whether a file exists in S3.

        Args:
            key: Object key to check.

        Returns:
            True if the object exists, False otherwise.
        """
        try:
            async with self._client() as client:
                await client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            return False
