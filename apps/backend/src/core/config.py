from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/stylipp"
    secret_key: str = "change-me"
    debug: bool = False
    cors_origins: list[str] = [
        "http://localhost:5173",
        "https://stylipp.com",
    ]

    # Qdrant vector database
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "products"

    # Hetzner Object Storage (S3-compatible)
    s3_endpoint_url: str = "https://hel1.your-objectstorage.com"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_name: str = "station11-bucket"
    s3_region: str = "hel1"

    # Clustering
    cluster_collection: str = "style_clusters"
    min_clusters: int = 10
    max_clusters: int = 200

    # User profiles
    user_profiles_collection: str = "user_profiles"
    feed_hybrid_confidence_threshold: float = 0.6
    feed_hybrid_personalized_ratio: float = 0.6
    feed_personalized_discovery_count: int = 2
    profile_update_lr_new: float = 0.15
    profile_update_lr_mid: float = 0.08
    profile_update_lr_mature: float = 0.03
    profile_update_lr_mid_confidence: float = 0.3
    profile_update_lr_mature_confidence: float = 0.7
    profile_update_dislike_gamma: float = 0.05
    profile_update_max_delta: float = 0.15
    profile_update_price_alpha: float = 0.1
    profile_update_save_price_alpha: float = 0.15
    profile_update_dislike_burst_count: int = 10
    profile_update_dislike_burst_gamma_scale: float = 0.5

    # WooCommerce partner store (optional - for future partner integration)
    woo_store_url: str | None = None
    woo_consumer_key: str | None = None
    woo_consumer_secret: str | None = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
