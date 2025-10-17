"""
Configuration utilities for Maverick-MCP.
"""

from .constants import CACHE_TTL, CONFIG, clean_env_var
from .database import (
    DatabasePoolConfig,
    create_engine_with_enhanced_config,
    get_default_pool_config,
    get_development_pool_config,
    get_high_concurrency_pool_config,
    get_pool_config_from_settings,
    validate_production_config,
)
from .markets import (
    Market,
    MarketConfig,
    MARKET_CONFIGS,
    get_all_markets,
    get_market_config,
    get_market_from_symbol,
    get_markets_by_country,
    is_indian_market,
    is_us_market,
)

__all__ = [
    "CONFIG",
    "CACHE_TTL",
    "clean_env_var",
    "DatabasePoolConfig",
    "get_default_pool_config",
    "get_development_pool_config",
    "get_high_concurrency_pool_config",
    "get_pool_config_from_settings",
    "create_engine_with_enhanced_config",
    "validate_production_config",
    # Multi-market support
    "Market",
    "MarketConfig",
    "MARKET_CONFIGS",
    "get_market_from_symbol",
    "get_market_config",
    "get_all_markets",
    "get_markets_by_country",
    "is_indian_market",
    "is_us_market",
]
