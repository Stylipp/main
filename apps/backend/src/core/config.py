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

    # Hetzner Object Storage (S3-compatible)
    s3_endpoint_url: str = "https://hel1.your-objectstorage.com"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_name: str = "station11-bucket"
    s3_region: str = "hel1"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
