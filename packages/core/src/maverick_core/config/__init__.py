"""
Maverick Core Configuration Module.

Provides a modular, extensible configuration system that can be used across all
maverick packages. Supports environment variables, defaults, and environment-specific
overrides.

Key Components:
    - Settings: Main application settings container
    - BaseConfigModel: Base class for configuration models with env var support
    - get_settings: Factory function for getting configured settings
    - CONFIG: Constants dictionary for common configuration values

Usage:
    >>> from maverick_core.config import get_settings, Settings
    >>> settings = get_settings()
    >>> print(settings.environment)
    >>> print(settings.database.url)

Environment Variables:
    - MAVERICK_ENVIRONMENT: Set environment (development, staging, production)
    - DATABASE_URL: Database connection string
    - REDIS_HOST, REDIS_PORT: Redis connection settings
    - CACHE_TTL_SECONDS: Default cache TTL
"""

from maverick_core.config.base import (
    BaseConfigModel,
    clean_env_var,
    get_env_bool,
    get_env_float,
    get_env_int,
    get_env_list,
)
from maverick_core.config.constants import CACHE_TTL, CONFIG
from maverick_core.config.settings import (
    AgentSettings,
    APISettings,
    CacheSettings,
    DatabaseSettings,
    FinancialSettings,
    PerformanceSettings,
    ProviderSettings,
    RedisSettings,
    ResearchSettings,
    Settings,
    UISettings,
    ValidationSettings,
    get_settings,
    load_settings_from_environment,
)

__all__ = [
    # Base utilities
    "BaseConfigModel",
    "clean_env_var",
    "get_env_int",
    "get_env_float",
    "get_env_bool",
    "get_env_list",
    # Constants
    "CONFIG",
    "CACHE_TTL",
    # Settings classes
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
    # Factory functions
    "get_settings",
    "load_settings_from_environment",
]

