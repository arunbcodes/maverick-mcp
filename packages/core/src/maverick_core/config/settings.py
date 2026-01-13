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
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, EnvSettingsSource


from maverick_core.config.constants import CONFIG

logger = logging.getLogger(__name__)

# This contron what prefix is expected in front of ENV variables
PREFIX = "MAVERICK_"


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix=f"{PREFIX}DB_",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    username: str = Field(default="postgres", description="Database username")
    password: str = Field(default="postgres", description="Database password")
    database: Optional[str] = Field(default="maverick_mcp", description="Database name")
    max_connections: Optional[int] = Field(default=10, description="DB Maximum number of connections")
    pool_size: Optional[int] = Field(default=20, description="DB Connection pool size")
    pool_max_overflow: Optional[int] = Field(default=10, description="Maximum overflow connections")
    pool_timeout: Optional[int] = Field(default=30, description="DB Pool connection timeout in seconds")
    # Below - Extracted DB config options from maveric_data.session.factory
    pool_recycle: Optional[int] = Field(default=3600, description="DB Pool recycle")
    pool_pre_ping: Optional[bool] = Field(default=True, description="DB pool pre ping")
    echo: Optional[bool] = Field(default=False, description="DB pool echo")
    use_pooling: Optional[bool] = Field(default=True, description="DB Use pooling boolean")
    statement_timeout: Optional[int] = Field(default=30000, description="DB Statement timeout")

    # Support declaring a full Postgres connection in one line. Take precedence over individual settings.
    database_url: Optional[str] | None = Field(default="", description="Postgres database url")
    postgres_url: Optional[str] | None = Field(default="", description="Postgres database url")


    @property
    def url(self) -> str:
        """Get database URL string."""
        # Check for environment variable first
        env_url = self.database_url or self.postgres_url
        if env_url:
            return env_url
        if self.host and self.port and self.username and self.password and self.database:
            auth = f"{self.username}:{self.password}@"
            return f"postgresql://{auth}{self.host}:{self.port}/{self.database}"
        # Default to SQLite for development
        return "sqlite:///maverick_mcp.db"


class APISettings(BaseSettings):
    """API configuration settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix=f"{PREFIX}API_",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    debug: Optional[bool] = Field(default=False, description="Debug mode")
    cache_timeout: Optional[int] = Field(default=300, description="Cache timeout in seconds")
    request_timeout: Optional[int] = Field(default=120, description="Default API request timeout in seconds")
    log_level: Optional[str] = Field(default="INFO", description="Log level setting for API")


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix=f"{PREFIX}REDIS_",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379,description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    username: Optional[str] | None = Field(default=None, description="Redis username")
    password: Optional[str] | None = Field(default=None, description="Redis password")
    ssl: Optional[bool] | None = Field(default=False, description="Use SSL for Redis connection")
    max_connections: Optional[int] = Field(default=50, description="Maximum Redis connections in pool")
    socket_timeout: Optional[int] = Field(default=5, description="Redis socket timeout in seconds")

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


class CacheSettings(BaseSettings):
    """Cache configuration settings."""

    enabled: Optional[bool] = Field(validation_alias=f"{PREFIX}CACHE_ENABLED", default = True, description="Enable caching")
    ttl_seconds: Optional[int] = Field(
        validation_alias=f"{PREFIX}TTL_SECONDS", default=604800, description="Default cache TTL in seconds (7 days)")
    quick_ttl: Optional[int] = Field(validation_alias=f"{PREFIX}QUICK_CACHE_TTL", default=300, description="Quick cache TTL in seconds (5 minutes)")
    max_size_mb: Optional[int] = Field(validation_alias=f"{PREFIX}MAX_CACHE_SIZE_MB", default=500, description="Maximum cache size in MB")


class ProviderSettings(BaseSettings):
    """Data provider configuration settings."""
    yfinance_timeout: Optional[int] = Field(default=30, description="yfinance API timeout in seconds")
    yfinance_rate_limit: Optional[int] = Field(default=120, description="yfinance requests per minute")
    external_data_timeout: Optional[int] = Field(default=120, description="External data API timeout in seconds")
    max_symbols_per_batch: Optional[int] = Field(default=100, description="Maximum symbols per batch request")


class PerformanceSettings(BaseSettings):
    """Performance settings for timeouts, retries, and batch sizes."""
    api_timeout: Optional[int] = Field(validation_alias=f"{PREFIX}API_REQUEST_TIMEOUT", default=120, description="Default API request timeout in seconds")
    max_retry_attempts: Optional[int] = Field(default=3, description="Maximum retry attempts for failed operations")
    retry_backoff_factor: Optional[float] = Field(default=2.0, description="Exponential backoff factor for retries")
    default_batch_size: Optional[int] = Field(default=50, description="Default batch size for processing operations")
    parallel_workers: Optional[int] = Field(default=4, description="Number of parallel workers")


class AgentSettings(BaseSettings):
    """Agent and AI workflow configuration settings."""
    cache_ttl: Optional[int] = Field(validation_alias=f"{PREFIX}AGENT_CACHE_TTL_SECONDS", default=300, description="Agent cache TTL in seconds")
    max_iterations: Optional[int] = Field(validation_alias=f"{PREFIX}MAX_AGENT_ITERATIONS", default=10, description="Maximum agent workflow iterations")
    max_parallel_agents: Optional[int] = Field(default=5, description="Maximum parallel agents in orchestration")
    max_execution_time: Optional[int] = Field(validation_alias=f"{PREFIX}MAX_AGENT_EXECUTION_TIME_SECONDS", default=720, description="Maximum agent execution time in seconds")
    circuit_breaker_threshold: Optional[int] = Field(default=5, description="Circuit breaker threshold")
    circuit_breaker_recovery: int = Field(validation_alias=f"{PREFIX}CIRCUIT_BREAKER_RECOVERY_TIMEOUT", default=60, description="Seconds to wait before testing recovery")


class FinancialSettings(BaseSettings):
    """Financial calculations and portfolio management settings."""
    default_account_size: Optional[Decimal] = Field(default=Decimal("100000"), description="Default account size for calculations (USD)")
    max_position_size_conservative: Optional[float] = Field(default=0.05, description="Maximum position size for conservative investors (5%)")
    max_position_size_moderate: Optional[float] = Field(default=0.10, description="Maximum position size for moderate investors (10%)")
    max_position_size_aggressive: Optional[float] = Field(default=0.20, description="Maximum position size for aggressive investors (20%)")


class UISettings(BaseSettings):
    """UI and pagination configuration settings."""
    default_page_size: Optional[int] = Field(default=20, description="Default number of items per page")
    max_page_size: Optional[int] = Field(default=100, description="Maximum number of items per page")
    default_screening_limit: Optional[int] = Field(default=20, description="Default number of stocks in screening results")
    max_screening_limit: Optional[int] = Field(default=100, description="Maximum stocks in screening results")
    default_history_days: Optional[int] = Field(default=365, description="Default number of days of historical data")


class ValidationSettings(BaseSettings):
    """Input validation configuration settings."""
    """Input validation configuration settings."""
    min_symbol_length: Optional[int] = Field(default=1, description="Minimum stock symbol length")
    max_symbol_length: Optional[int] = Field(default=10, description="Maximum stock symbol length")
    max_text_field_length: Optional[int] = Field(default=100, description="Maximum text field length")
    max_description_length: Optional[int] = Field(default=500, description="Maximum length for description fields")


class ResearchSettings(BaseSettings):
    """Research and web search configuration settings."""
    default_max_sources: Optional[int] = Field(default=50, description="Default max sources per research")
    default_depth: Optional[str] = Field(default="comprehensive", description="Default research depth")
    cache_ttl_hours: Optional[int] = Field(default=4, description="Research cache TTL in hours")
    max_content_length: Optional[int] = Field(default=50000, description="Maximum content length for research")
    trusted_domains: Optional[list[str]] = Field(default=[
        "reuters.com",
        "bloomberg.com",
        "wsj.com",
        "ft.com",
        "marketwatch.com",
        "cnbc.com",
        "yahoo.com",
        "seekingalpha.com",
    ], description="List of trusted domains for research")


class AiConfig(BaseSettings):
    """Data provider configuration settings."""
    ollama_model: Optional[str] = Field(default="gpt-oss-20b", description="OLLAMA model") # Used in ollama.py
    ollama_base_url: Optional[str] = Field(default="http://localhost:11434", description="OLLAMA base url") # used in ollama.py
    ollama_base_url_with_version: Optional[str] = Field(default=f"{ollama_base_url}/v1", description="OLLAMA base url") # used in ollama.py


class Sentry(BaseSettings):
    """Data provider configuration settings."""
    sentry_dsn: Optional[str] = Field(default="", description="Sentry DSN") # Used in sentry.py
    sentry_release_version: Optional[str] = Field(default="", description="Sentry release version") # Used in sentry.py


class Server(BaseSettings): # Name McpServer??
    """MCP Server configuration settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix=f"{PREFIX}MCP_",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    server_name: Optional[str] = Field(default="MaverickMCP", description="Name of MCP server") # Used by Server
    server_host: Optional[str] = Field(default="0.0.0.0", description="Server listener IP address") # Used by Server
    server_port: Optional[int] = Field(default=8000, description="Server listener TCP port") # Used by Server
    server_transport: Optional[str] = Field(default="sse", description="Server MCP transport (SSE, Streaminghttp, STDIO)") # Used by Server
    seed_demodata: Optional[bool] = Field(default=False, description="Seed demo data on first startup") # Used by Server

class Settings(BaseSettings):
    """Main application settings container."""

    model_config = SettingsConfigDict(
        #env_file=".env",
        env_prefix="MAVERICK_",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="MaverickMCP", description="Application name")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="development", description="Environment (development, staging, production)")

    # Sub-settings
    api: APISettings = Field(default_factory=APISettings, description="API settings")
    database: DatabaseSettings = Field(default_factory=DatabaseSettings, description="Database settings")
    redis: RedisSettings = Field(default_factory=RedisSettings, description="Redis settings")
    cache: CacheSettings = Field(default_factory=CacheSettings, description="Cache settings")
    provider: ProviderSettings = Field(default_factory=ProviderSettings, description="Provider settings")
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings, description="Performance settings")
    agent: AgentSettings = Field(default_factory=AgentSettings, description="Agent settings")
    financial: FinancialSettings = Field(default_factory=FinancialSettings, description="Financial settings")
    ui: UISettings = Field(default_factory=UISettings, description="UI settings")
    validation: ValidationSettings = Field(default_factory=ValidationSettings, description="Validation settings")
    research: ResearchSettings = Field(default_factory=ResearchSettings, description="Research settings")
    server: Server = Field(default_factory=Server, description="MCP server settings")

    # Authentication - JWT
    jwt_secret: Optional[str] = Field(default="change-me-in-production-use-openssl-rand-hex-32")
    jwt_algorithm: Optional[str] = Field(default="HS256")
    jwt_access_token_expire_minutes: Optional[int] = Field(default=15)
    jwt_refresh_token_expire_days: Optional[int] = Field(default=30)

    # Authentication - API Keys
    api_key_prefix: Optional[str] = Field(default="mav_")

    # CORS
    cors_origins: Optional[list[str]] = Field(default=[
        "http://localhost:3000",
        "http://localhost:5173"])
    cors_allow_credentials: Optional[bool] = Field(default=True)

    # Rate Limiting
    rate_limit_enabled: Optional[bool] = Field(default=True)
    rate_limit_free_rpm: Optional[int] = Field(default=100)  # Requests per minute
    rate_limit_pro_rpm: Optional[int] = Field(default=1000)
    rate_limit_enterprise_rpm: Optional[int] = Field(default=10000)

    # LLM Token Budgets
    token_budget_free_daily: Optional[int] = Field(default=10_000)
    token_budget_pro_daily: Optional[int] = Field(default=100_000)
    token_budget_enterprise_daily: Optional[int] = Field(default=1_000_000)

    # Logging
    log_level: Optional[str] = Field(default="INFO")
    log_format: Optional[str] = Field(default="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    request_log_format: Optional[str] = Field(default="%(asctime)s [%(request_id)s] %(levelname)s %(name)s: %(message)s")

    # External APIs (optional)
    tiingo_api_key: Optional[str] = Field(default=None, description="Tiingo API key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    fred_api_key: Optional[str] = Field(default=None, description="Federal Reserve Economic Data API key")
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key")
    exa_api_key: Optional[str] = Field(default=None, description="EXA API key")

    # CI/CD - Extracted from maverick_data.session.factory
    github_actions: Optional[bool] = Field(default=False)
    ci: Optional[bool] = Field(default=False)

    # Feature settings
    enable_redis: Optional[bool] = Field(default=True, description="Enable Redis for Server")
    enable_research: Optional[bool] = Field(default=True, description="Enable Research for Server")
    enable_india: Optional[bool] = Field(default=True, description="Enable India stock market")
    enable_backtesting: Optional[bool] = Field(default=True, description="Enable Backtesting")

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log_level is always uppercase."""
        return v.upper() if isinstance(v, str) else v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

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
        settings.log_level = "warning"
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

