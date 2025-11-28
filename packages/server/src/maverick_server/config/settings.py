"""
Environment-based settings for maverick-server.

All configuration is read from environment variables with sensible defaults.
No file-based configuration to keep things simple for personal use.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    """Server configuration from environment variables.

    All settings have sensible defaults for local development.
    Set environment variables to override.
    """

    # Server settings
    server_name: str = field(default_factory=lambda: os.getenv("MAVERICK_SERVER_NAME", "maverick-mcp"))
    server_host: str = field(default_factory=lambda: os.getenv("MAVERICK_HOST", "localhost"))
    server_port: int = field(default_factory=lambda: int(os.getenv("MAVERICK_PORT", "8003")))
    transport: str = field(default_factory=lambda: os.getenv("MAVERICK_TRANSPORT", "sse"))

    # Database settings
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "sqlite:///./maverick.db"
        )
    )

    # Redis settings (optional)
    redis_host: str | None = field(default_factory=lambda: os.getenv("REDIS_HOST"))
    redis_port: int = field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))
    redis_db: int = field(default_factory=lambda: int(os.getenv("REDIS_DB", "0")))

    # API keys
    tiingo_api_key: str | None = field(default_factory=lambda: os.getenv("TIINGO_API_KEY"))
    openrouter_api_key: str | None = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY"))
    exa_api_key: str | None = field(default_factory=lambda: os.getenv("EXA_API_KEY"))
    fred_api_key: str | None = field(default_factory=lambda: os.getenv("FRED_API_KEY"))

    # Feature flags
    enable_redis: bool = field(
        default_factory=lambda: os.getenv("MAVERICK_ENABLE_REDIS", "").lower() in ("true", "1", "yes")
    )
    enable_research: bool = field(
        default_factory=lambda: os.getenv("MAVERICK_ENABLE_RESEARCH", "true").lower() in ("true", "1", "yes")
    )
    enable_backtesting: bool = field(
        default_factory=lambda: os.getenv("MAVERICK_ENABLE_BACKTESTING", "true").lower() in ("true", "1", "yes")
    )
    enable_india: bool = field(
        default_factory=lambda: os.getenv("MAVERICK_ENABLE_INDIA", "true").lower() in ("true", "1", "yes")
    )

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("MAVERICK_LOG_LEVEL", "INFO"))

    @property
    def redis_url(self) -> str | None:
        """Get Redis URL if Redis is configured."""
        if self.redis_host:
            return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return None

    @property
    def has_tiingo(self) -> bool:
        """Check if Tiingo API is configured."""
        return bool(self.tiingo_api_key)

    @property
    def has_openrouter(self) -> bool:
        """Check if OpenRouter API is configured."""
        return bool(self.openrouter_api_key)

    @property
    def has_exa(self) -> bool:
        """Check if Exa API is configured."""
        return bool(self.exa_api_key)

    def validate(self) -> list[str]:
        """Validate settings and return list of warnings."""
        warnings = []

        if not self.tiingo_api_key:
            warnings.append("TIINGO_API_KEY not set - stock data features will be limited")

        if not self.openrouter_api_key and self.enable_research:
            warnings.append("OPENROUTER_API_KEY not set - research features will be disabled")

        if not self.exa_api_key and self.enable_research:
            warnings.append("EXA_API_KEY not set - web search in research will be limited")

        return warnings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance.

    Settings are read once and cached. Call this function to access
    configuration throughout the application.

    Returns:
        Cached Settings instance
    """
    return Settings()


def reset_settings_cache() -> None:
    """Reset settings cache. Useful for testing."""
    get_settings.cache_clear()
