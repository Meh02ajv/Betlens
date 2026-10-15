from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core
    app_env: Literal["development", "test", "staging", "production"] = "development"
    database_url: str = "postgresql+psycopg://betlens:betlens@localhost:5433/betlens"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-to-a-long-random-string"
    frontend_url: str = "http://localhost:3000"

    # Auth
    google_client_id: str = ""
    google_client_secret: str = ""
    jwt_access_ttl_min: int = 15
    jwt_refresh_ttl_days: int = 30

    # Data providers
    football_provider: str = "mock"
    football_api_key: str = ""
    nba_provider: Literal["mock", "balldontlie", "sportradar"] = "mock"
    nba_api_key: str = ""
    odds_provider: Literal["mock", "the_odds_api"] = "mock"
    odds_api_key: str = ""

    # AI assistant
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"
    assistant_free_daily_limit: int = 10
    assistant_pro_daily_limit: int = 200

    # Billing
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_pro_price_id: str = ""

    # Email
    resend_api_key: str = ""

    # Web Push
    vapid_public_key: str = ""
    vapid_private_key: str = ""

    # Monitoring
    sentry_dsn: str = ""

    @field_validator("database_url")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        if info.data.get("app_env") == "production" and (
            v == "change-me-to-a-long-random-string" or len(v) < 32
        ):
            raise ValueError("SECRET_KEY must be a strong secret in production")
        return v

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origins(self) -> list[str]:
        if self.is_production:
            return [self.frontend_url]
        return [self.frontend_url, "http://localhost:3000", "http://localhost:3001"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()