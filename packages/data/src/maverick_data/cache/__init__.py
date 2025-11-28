"""
Maverick Data Cache.

Cache providers and utilities for data caching.
"""

from maverick_data.cache.manager import (
    CACHE_VERSION,
    DEFAULT_TTL_SECONDS,
    CacheManager,
    generate_cache_key,
    get_cache_manager,
    reset_cache_manager,
)
from maverick_data.cache.memory_cache import MemoryCache
from maverick_data.cache.redis_cache import RedisCache
from maverick_data.cache.serialization import (
    deserialize_data,
    ensure_timezone_naive,
    get_serialization_stats,
    normalize_timezone,
    reset_serialization_stats,
    serialize_data,
)

__all__ = [
    # Cache providers
    "RedisCache",
    "MemoryCache",
    "CacheManager",
    # Manager utilities
    "get_cache_manager",
    "reset_cache_manager",
    "generate_cache_key",
    # Configuration
    "CACHE_VERSION",
    "DEFAULT_TTL_SECONDS",
    # Serialization
    "serialize_data",
    "deserialize_data",
    "normalize_timezone",
    "ensure_timezone_naive",
    "get_serialization_stats",
    "reset_serialization_stats",
]
