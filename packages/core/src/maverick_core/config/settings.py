"""
Configuration settings for Maverick packages.

This module provides configuration settings that can be customized
through environment variables. It's designed to be modular and extensible,
allowing each package to define its own settings classes.
"""

from __future__ import annotations

import logging
import os
from decimal import Decimal
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field

from maverick_core.config.base import (
    BaseConfigModel,
    clean_env_var,
    get_env_bool,
    get_env_float,
    get_env_int,
    get_env_list,
)
from maverick_core.config.constants import CONFIG

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseConfigModel):
    """Database configuration settings."""

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    username: str = Field(default="postgres", description="Database username")
    password: str = Field(default="", description="Database password")
    database: str = Field(default="maverick_mcp", description="Database name")
    max_connections: int = Field(
        default=10, description="Maximum number of connections"
    )
    pool_size: int = Field(
        default_factory=lambda: get_env_int("DB_POOL_SIZE", 20),
        description="Connection pool size",
    )
    pool_max_overflow: int = Field(
        default_factory=lambda: get_env_int("DB_POOL_MAX_OVERFLOW", 10),
        description="Maximum overflow connections",
    )
    pool_timeout: int = Field(
        default_factory=lambda: get_env_int("DB_POOL_TIMEOUT", 30),
        description="Pool connection timeout in seconds",
    )

    @property
    def url(self) -> str:
        """Get database URL string."""
        # Check for environment variable first
        env_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
        if env_url:
            return env_url
        # Default to SQLite for development
        return "sqlite:///maverick_mcp.db"


class APISettings(BaseConfigModel):
    """API configuration settings."""

    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="info", description="Log level")
    cache_timeout: int = Field(default=300, description="Cache timeout in seconds")
    cors_origins: list[str] = Field(
        default_factory=lambda: get_env_list(
            "CORS_ORIGINS", ["http://localhost:3000", "http://localhost:3001"]
        ),
        description="CORS allowed origins",
    )
    request_timeout: int = Field(
        default_factory=lambda: get_env_int("API_REQUEST_TIMEOUT", 120),
        description="Default API request timeout in seconds",
    )


class RedisSettings(BaseConfigModel):
    """Redis configuration settings."""

    host: str = Field(
        default_factory=lambda: CONFIG["redis"]["host"], description="Redis host"
    )
    port: int = Field(
        default_factory=lambda: CONFIG["redis"]["port"], description="Redis port"
    )
    db: int = Field(
        default_factory=lambda: CONFIG["redis"]["db"],
        description="Redis database number",
    )
    username: str | None = Field(
        default_factory=lambda: CONFIG["redis"]["username"],
        description="Redis username",
    )
    password: str | None = Field(
        default_factory=lambda: CONFIG["redis"]["password"],
        description="Redis password",
    )
    ssl: bool = Field(
        default_factory=lambda: CONFIG["redis"]["ssl"],
        description="Use SSL for Redis connection",
    )
    max_connections: int = Field(
        default_factory=lambda: get_env_int("REDIS_MAX_CONNECTIONS", 50),
        description="Maximum Redis connections in pool",
    )
    socket_timeout: int = Field(
        default_factory=lambda: get_env_int("REDIS_SOCKET_TIMEOUT", 5),
        description="Redis socket timeout in seconds",
    )

    @property
    def url(self) -> str:
        """Get Redis URL string."""
        scheme = "rediss" if self.ssl else "redis"
        auth = ""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        elif self.password:
            auth = f":{self.password}@"
        return f"{scheme}://{auth}{self.host}:{self.port}/{self.db}"


class CacheSettings(BaseConfigModel):
    """Cache configuration settings."""

    enabled: bool = Field(
        default_factory=lambda: get_env_bool("CACHE_ENABLED", True),
        description="Enable caching",
    )
    ttl_seconds: int = Field(
        default_factory=lambda: get_env_int("CACHE_TTL_SECONDS", 604800),
        description="Default cache TTL in seconds (7 days)",
    )
    quick_ttl: int = Field(
        default_factory=lambda: get_env_int("QUICK_CACHE_TTL", 300),
        description="Quick cache TTL in seconds (5 minutes)",
    )
    max_size_mb: int = Field(
        default_factory=lambda: get_env_int("MAX_CACHE_SIZE_MB", 500),
        description="Maximum cache size in MB",
    )


class ProviderSettings(BaseConfigModel):
    """Data provider configuration settings."""

    yfinance_timeout: int = Field(
        default_factory=lambda: get_env_int("YFINANCE_TIMEOUT_SECONDS", 30),
        description="yfinance API timeout in seconds",
    )
    yfinance_rate_limit: int = Field(
        default_factory=lambda: get_env_int("YFINANCE_REQUESTS_PER_MINUTE", 120),
        description="yfinance requests per minute",
    )
    external_data_timeout: int = Field(
        default_factory=lambda: get_env_int("EXTERNAL_DATA_TIMEOUT", 120),
        description="External data API timeout in seconds",
    )
    max_symbols_per_batch: int = Field(
        default_factory=lambda: get_env_int("MAX_SYMBOLS_PER_BATCH", 100),
        description="Maximum symbols per batch request",
    )


class PerformanceSettings(BaseConfigModel):
    """Performance settings for timeouts, retries, and batch sizes."""

    api_timeout: int = Field(
        default_factory=lambda: get_env_int("API_REQUEST_TIMEOUT", 120),
        description="Default API request timeout in seconds",
    )
    max_retry_attempts: int = Field(
        default_factory=lambda: get_env_int("MAX_RETRY_ATTEMPTS", 3),
        description="Maximum retry attempts for failed operations",
    )
    retry_backoff_factor: float = Field(
        default_factory=lambda: get_env_float("RETRY_BACKOFF_FACTOR", 2.0),
        description="Exponential backoff factor for retries",
    )
    default_batch_size: int = Field(
        default_factory=lambda: get_env_int("DEFAULT_BATCH_SIZE", 50),
        description="Default batch size for processing operations",
    )
    parallel_workers: int = Field(
        default_factory=lambda: get_env_int("PARALLEL_SCREENING_WORKERS", 4),
        description="Number of parallel workers",
    )


class AgentSettings(BaseConfigModel):
    """Agent and AI workflow configuration settings."""

    cache_ttl: int = Field(
        default_factory=lambda: get_env_int("AGENT_CACHE_TTL_SECONDS", 300),
        description="Agent cache TTL in seconds",
    )
    max_iterations: int = Field(
        default_factory=lambda: get_env_int("MAX_AGENT_ITERATIONS", 10),
        description="Maximum agent workflow iterations",
    )
    max_parallel_agents: int = Field(
        default_factory=lambda: get_env_int("MAX_PARALLEL_AGENTS", 5),
        description="Maximum parallel agents in orchestration",
    )
    max_execution_time: int = Field(
        default_factory=lambda: get_env_int("MAX_AGENT_EXECUTION_TIME_SECONDS", 720),
        description="Maximum agent execution time in seconds",
    )
    circuit_breaker_threshold: int = Field(
        default_factory=lambda: get_env_int("CIRCUIT_BREAKER_FAILURE_THRESHOLD", 5),
        description="Failures before opening circuit",
    )
    circuit_breaker_recovery: int = Field(
        default_factory=lambda: get_env_int("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", 60),
        description="Seconds to wait before testing recovery",
    )


class FinancialSettings(BaseConfigModel):
    """Financial calculations and portfolio management settings."""

    default_account_size: Decimal = Field(
        default_factory=lambda: Decimal(os.getenv("DEFAULT_ACCOUNT_SIZE", "100000")),
        description="Default account size for calculations (USD)",
    )
    max_position_size_conservative: float = Field(
        default_factory=lambda: get_env_float("MAX_POSITION_SIZE_CONSERVATIVE", 0.05),
        description="Maximum position size for conservative investors (5%)",
    )
    max_position_size_moderate: float = Field(
        default_factory=lambda: get_env_float("MAX_POSITION_SIZE_MODERATE", 0.10),
        description="Maximum position size for moderate investors (10%)",
    )
    max_position_size_aggressive: float = Field(
        default_factory=lambda: get_env_float("MAX_POSITION_SIZE_AGGRESSIVE", 0.20),
        description="Maximum position size for aggressive investors (20%)",
    )


class UISettings(BaseConfigModel):
    """UI and pagination configuration settings."""

    default_page_size: int = Field(
        default_factory=lambda: get_env_int("DEFAULT_PAGE_SIZE", 20),
        description="Default number of items per page",
    )
    max_page_size: int = Field(
        default_factory=lambda: get_env_int("MAX_PAGE_SIZE", 100),
        description="Maximum number of items per page",
    )
    default_screening_limit: int = Field(
        default_factory=lambda: get_env_int("DEFAULT_SCREENING_LIMIT", 20),
        description="Default number of stocks in screening results",
    )
    max_screening_limit: int = Field(
        default_factory=lambda: get_env_int("MAX_STOCKS_PER_SCREENING", 100),
        description="Maximum stocks in screening results",
    )
    default_history_days: int = Field(
        default_factory=lambda: get_env_int("DEFAULT_HISTORY_DAYS", 365),
        description="Default number of days of historical data",
    )


class ValidationSettings(BaseConfigModel):
    """Input validation configuration settings."""

    min_symbol_length: int = Field(
        default_factory=lambda: get_env_int("MIN_SYMBOL_LENGTH", 1),
        description="Minimum stock symbol length",
    )
    max_symbol_length: int = Field(
        default_factory=lambda: get_env_int("MAX_SYMBOL_LENGTH", 10),
        description="Maximum stock symbol length",
    )
    max_text_field_length: int = Field(
        default_factory=lambda: get_env_int("MAX_TEXT_FIELD_LENGTH", 100),
        description="Maximum length for general text fields",
    )
    max_description_length: int = Field(
        default_factory=lambda: get_env_int("MAX_DESCRIPTION_LENGTH", 500),
        description="Maximum length for description fields",
    )


class ResearchSettings(BaseConfigModel):
    """Research and web search configuration settings."""

    default_max_sources: int = Field(
        default_factory=lambda: get_env_int("DEFAULT_MAX_SOURCES", 50),
        description="Default max sources per research",
    )
    default_depth: str = Field(
        default="comprehensive",
        description="Default research depth",
    )
    cache_ttl_hours: int = Field(
        default_factory=lambda: get_env_int("RESEARCH_CACHE_TTL_HOURS", 4),
        description="Research cache TTL in hours",
    )
    max_content_length: int = Field(
        default_factory=lambda: get_env_int("RESEARCH_MAX_CONTENT_LENGTH", 2000),
        description="Max content length per source",
    )
    trusted_domains: list[str] = Field(
        default=[
            "reuters.com",
            "bloomberg.com",
            "wsj.com",
            "ft.com",
            "marketwatch.com",
            "cnbc.com",
            "yahoo.com",
            "seekingalpha.com",
        ],
        description="Trusted news domains for research",
    )


class Settings(BaseModel):
    """Main application settings container."""

    app_name: str = Field(default="MaverickMCP", description="Application name")
    environment: str = Field(
        default_factory=lambda: clean_env_var("MAVERICK_ENVIRONMENT", "development"),
        description="Environment (development, staging, production)",
    )

    # Sub-settings
    api: APISettings = Field(default_factory=APISettings, description="API settings")
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings, description="Database settings"
    )
    redis: RedisSettings = Field(
        default_factory=RedisSettings, description="Redis settings"
    )
    cache: CacheSettings = Field(
        default_factory=CacheSettings, description="Cache settings"
    )
    provider: ProviderSettings = Field(
        default_factory=ProviderSettings, description="Provider settings"
    )
    performance: PerformanceSettings = Field(
        default_factory=PerformanceSettings, description="Performance settings"
    )
    agent: AgentSettings = Field(
        default_factory=AgentSettings, description="Agent settings"
    )
    financial: FinancialSettings = Field(
        default_factory=FinancialSettings, description="Financial settings"
    )
    ui: UISettings = Field(default_factory=UISettings, description="UI settings")
    validation: ValidationSettings = Field(
        default_factory=ValidationSettings, description="Validation settings"
    )
    research: ResearchSettings = Field(
        default_factory=ResearchSettings, description="Research settings"
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ("development", "dev")

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary."""
        return self.model_dump()


def load_settings_from_environment() -> Settings:
    """
    Load settings from environment variables.

    Returns:
        Settings object with values loaded from environment
    """
    return Settings()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get application settings (cached singleton).

    This function loads settings from environment variables and
    applies any environment-specific overrides.

    Returns:
        Settings object with all configured values
    """
    settings = load_settings_from_environment()

    # Override with environment-specific settings if needed
    if settings.is_production:
        # Apply production-specific settings
        settings.api.debug = False
        settings.api.log_level = "warning"

    logger.debug(f"Settings loaded for environment: {settings.environment}")
    return settings


__all__ = [
    "Settings",
    "APISettings",
    "DatabaseSettings",
    "RedisSettings",
    "CacheSettings",
    "ProviderSettings",
    "PerformanceSettings",
    "AgentSettings",
    "FinancialSettings",
    "UISettings",
    "ValidationSettings",
    "ResearchSettings",
    "get_settings",
    "load_settings_from_environment",
]

