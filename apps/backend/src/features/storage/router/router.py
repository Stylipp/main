import logging

import aioboto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, status

from src.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/storage", tags=["Storage"])


@router.get("/health")
async def storage_health() -> dict[str, str]:
    """Check connectivity to the S3-compatible object storage bucket.

    Returns 200 with connection status on success, or 503 if the bucket
    is unreachable.
    """
    settings = get_settings()
    session = aioboto3.Session()

    try:
        async with session.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        ) as client:
            await client.head_bucket(Bucket=settings.s3_bucket_name)
    except ClientError:
        logger.exception("S3 health check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Object storage unavailable",
        )

    return {"status": "connected", "bucket": settings.s3_bucket_name}
