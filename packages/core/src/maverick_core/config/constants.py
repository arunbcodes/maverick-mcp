"""
Constants for the Maverick configuration system.

This module provides default configuration values that can be overridden
by environment variables.
"""

from __future__ import annotations

from typing import Any

from maverick_core.config.base import clean_env_var, get_env_bool, get_env_int

# Configuration with defaults
CONFIG: dict[str, Any] = {
    "redis": {
        "host": clean_env_var("REDIS_HOST", "localhost"),
        "port": get_env_int("REDIS_PORT", 6379),
        "db": get_env_int("REDIS_DB", 0),
        "username": clean_env_var("REDIS_USERNAME"),
        "password": clean_env_var("REDIS_PASSWORD"),
        "ssl": get_env_bool("REDIS_SSL", False),
    },
    "cache": {
        "ttl": get_env_int("CACHE_TTL_SECONDS", 604800),  # 7 days default
        "enabled": get_env_bool("CACHE_ENABLED", True),
    },
    "yfinance": {
        "timeout": get_env_int("YFINANCE_TIMEOUT_SECONDS", 30),
    },
    "database": {
        "pool_size": get_env_int("DB_POOL_SIZE", 20),
        "max_overflow": get_env_int("DB_POOL_MAX_OVERFLOW", 10),
        "timeout": get_env_int("DB_POOL_TIMEOUT", 30),
    },
    "api": {
        "timeout": get_env_int("API_REQUEST_TIMEOUT", 120),
        "rate_limit": get_env_int("API_RATE_LIMIT_PER_MINUTE", 60),
    },
}

# Convenience constants
CACHE_TTL = CONFIG["cache"]["ttl"]
REDIS_HOST = CONFIG["redis"]["host"]
REDIS_PORT = CONFIG["redis"]["port"]

__all__ = [
    "CONFIG",
    "CACHE_TTL",
    "REDIS_HOST",
    "REDIS_PORT",
]

