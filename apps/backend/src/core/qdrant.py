from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from src.core.config import get_settings

_client: AsyncQdrantClient | None = None


async def get_qdrant_client() -> AsyncQdrantClient:
    """Get or create the async Qdrant client singleton."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
    return _client


async def ensure_collection() -> None:
    """Create the products collection if it doesn't exist.

    Collection config:
    - 768-dimensional vectors (FashionSigLIP embeddings)
    - Cosine similarity for distance metric
    - On-disk payload storage for large payloads
    """
    settings = get_settings()
    client = await get_qdrant_client()

    collections = await client.get_collections()
    collection_names = [c.name for c in collections.collections]

    if settings.qdrant_collection not in collection_names:
        await client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=768,  # FashionSigLIP embedding dimension
                distance=Distance.COSINE,
            ),
            on_disk_payload=True,
        )


async def health_check() -> bool:
    """Verify Qdrant connection and collection existence."""
    try:
        settings = get_settings()
        client = await get_qdrant_client()

        # Check if collection exists
        collection_info = await client.get_collection(settings.qdrant_collection)
        return collection_info is not None
    except Exception:
        return False


async def close_client() -> None:
    """Close the Qdrant client connection."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
