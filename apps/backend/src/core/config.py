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

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
