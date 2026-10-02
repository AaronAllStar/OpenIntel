from functools import lru_cache
from pathlib import Path
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "OpenIntel"
    ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "info"
    SECRET_KEY: str = "openintel-dev-secret-key-at-least-32-chars-long"

    # Server binding (Strict localhost only)
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Security & Guardrails
    ALLOW_PRIVATE_TARGETS: bool = False
    ADAPTER_TIMEOUT_MS: int = 30_000
    MAX_RESULTS_PER_ADAPTER: int = 500
    RATE_LIMIT_ENABLED: bool = True
    AUTH_ENABLED: bool = False
    ADMIN_API_KEY: str = "openintel-admin-secret-key-prod-32chars"
    ANALYST_API_KEY: str = "openintel-analyst-secret-key-prod-32chars"

    # Persistence & Queues (PostgreSQL only)
    DATABASE_URL: str = (
        "postgresql+psycopg://openintel:openintel_secure_pass@127.0.0.1:5432/openintel"
    )
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    # Rust Core Engine Feature Flags
    USE_RUST_ID_VALIDATOR: bool = True

    # File storage
    EXPORTS_DIR: Path = Path("./data/exports")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.ENV in ("production", "prod"):
            if self.DEBUG:
                raise ValueError("Security violation: DEBUG must be False in production environment")
            if "openintel-dev" in self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError("Security violation: Default or insecure SECRET_KEY cannot be used in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
