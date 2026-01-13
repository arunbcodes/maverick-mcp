"""
API configuration using pydantic-settings.

Environment variables are loaded from .env file and environment.
All settings can be overridden via environment variables with MAVERICK_ prefix.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from maverick_core.config.settings import Settings


class Settings1(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MAVERICK_",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="MaverickMCP API")
    app_version: str = Field(default="1.0.0")
    environment: Literal["development", "staging", "production"] = Field(
        default="development"
    )
    debug: bool = Field(default=False)

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:55432/maverick_mcp"
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:56379")

    # Authentication - JWT
    jwt_secret: str = Field(default="change-me-in-production-use-openssl-rand-hex-32")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=15)
    jwt_refresh_token_expire_days: int = Field(default=30)

    # Authentication - API Keys
    api_key_prefix: str = Field(default="mav_")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )
    cors_allow_credentials: bool = Field(default=True)

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_free_rpm: int = Field(default=100)  # Requests per minute
    rate_limit_pro_rpm: int = Field(default=1000)
    rate_limit_enterprise_rpm: int = Field(default=10000)

    # LLM Token Budgets
    token_budget_free_daily: int = Field(default=10_000)
    token_budget_pro_daily: int = Field(default=100_000)
    token_budget_enterprise_daily: int = Field(default=1_000_000)

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(
        default="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    request_log_format: str = Field(
        default="%(asctime)s [%(request_id)s] %(levelname)s %(name)s: %(message)s"
    )

    # External APIs (optional)
    tiingo_api_key: str | None = Field(default=None)
    openai_api_key: str | None = Field(default=None)
    anthropic_api_key: str | None = Field(default=None)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            if not v.strip():
                return None  # Use default when empty
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience instance
settings = get_settings()


__all__ = ["Settings", "get_settings", "settings"]

