from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "OpenIntel"
    ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "info"
    SECRET_KEY: str = "openintel-dev-secret-key-at-least-32-chars-long"

    # Server binding (Localhost only)
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Security & Guardrails
    ALLOW_PRIVATE_TARGETS: bool = False
    ADAPTER_TIMEOUT_MS: int = 30_000
    MAX_RESULTS_PER_ADAPTER: int = 500

    # Persistence & Queues
    DATABASE_URL: str = (
        "sqlite:///./openintel.db"  # Defaults to local SQLite, overridable to Postgres
    )
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    # File storage
    EXPORTS_DIR: Path = Path("./data/exports")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
