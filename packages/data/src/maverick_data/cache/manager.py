"""
Cache manager providing unified access to cache providers.

Automatically selects Redis or memory cache based on availability.
Thread-safe singleton implementation with optimized async operations.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import threading
from typing import Any

from maverick_core import ICacheProvider
from maverick_data.cache.memory_cache import MemoryCache
from maverick_data.cache.redis_cache import RedisCache

logger = logging.getLogger("maverick_data.cache.manager")

# Default cache configuration
DEFAULT_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
CACHE_VERSION = os.getenv("CACHE_VERSION", "v1")
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"


def generate_cache_key(base_key: str, **kwargs: Any) -> str:
    """
    Generate versioned cache key with consistent hashing.

    Args:
        base_key: Base cache key
        **kwargs: Additional parameters to include in key

    Returns:
        Versioned and hashed cache key
    """
    key_parts = [CACHE_VERSION, base_key]

    if kwargs:
        sorted_params = sorted(kwargs.items())
        param_str = ":".join(f"{k}={v}" for k, v in sorted_params)
        key_parts.append(param_str)

    full_key = ":".join(str(part) for part in key_parts)

    # Hash long keys to prevent key length limits (using SHA-256 for security)
    if len(full_key) > 250:
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()[:32]
        return f"{CACHE_VERSION}:hashed:{key_hash}"

    return full_key


class CacheManager:
    """
    Unified cache manager with automatic provider selection.

    Attempts to use Redis first, falls back to in-memory cache.
    Provides both sync and async access methods.
    """

    def __init__(
        self,
        redis_host: str | None = None,
        redis_port: int | None = None,
        memory_max_size: int = 1000,
        memory_limit_mb: int = 100,
    ):
        """
        Initialize cache manager.

        Args:
            redis_host: Redis host (optional, uses env var)
            redis_port: Redis port (optional, uses env var)
            memory_max_size: Maximum entries for memory cache
            memory_limit_mb: Maximum memory for memory cache in MB
        """
        self._redis_cache: RedisCache | None = None
        self._memory_cache: MemoryCache = MemoryCache(
            max_size=memory_max_size, memory_limit_mb=memory_limit_mb
        )
        self._redis_host = redis_host
        self._redis_port = redis_port
        self._initialized = False

    def _ensure_initialized(self) -> ICacheProvider:
        """Ensure cache provider is initialized and return primary provider."""
        if not self._initialized:
            if CACHE_ENABLED:
                try:
                    self._redis_cache = RedisCache(
                        host=self._redis_host,
                        port=self._redis_port,
                    )
                    # Test connection
                    stats = self._redis_cache.get_stats()
                    if stats.get("connected"):
                        logger.info("Using Redis cache provider")
                    else:
                        logger.info("Redis not available, using memory cache")
                        self._redis_cache = None
                except Exception as e:
                    logger.warning(f"Redis initialization failed: {e}")
                    self._redis_cache = None

            self._initialized = True

        if self._redis_cache:
            return self._redis_cache
        return self._memory_cache

    def get(self, key: str) -> Any:
        """Get value from cache."""
        if not CACHE_ENABLED:
            return None

        provider = self._ensure_initialized()

        # Try Redis first
        if self._redis_cache:
            value = self._redis_cache.get(key)
            if value is not None:
                return value

        # Fall back to memory
        return self._memory_cache.get(key)

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache with optional TTL."""
        if not CACHE_ENABLED:
            return False

        resolved_ttl = ttl if ttl is not None else DEFAULT_TTL_SECONDS
        provider = self._ensure_initialized()

        # Try Redis first
        if self._redis_cache:
            if self._redis_cache.set(key, value, resolved_ttl):
                return True

        # Fall back to memory
        return self._memory_cache.set(key, value, resolved_ttl)

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not CACHE_ENABLED:
            return False

        self._ensure_initialized()
        deleted = False

        if self._redis_cache:
            deleted = self._redis_cache.delete(key)

        deleted = self._memory_cache.delete(key) or deleted
        return deleted

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not CACHE_ENABLED:
            return False

        self._ensure_initialized()

        if self._redis_cache and self._redis_cache.exists(key):
            return True

        return self._memory_cache.exists(key)

    def clear(self, pattern: str | None = None) -> int:
        """Clear cache entries matching pattern."""
        self._ensure_initialized()
        count = 0

        if self._redis_cache:
            count += self._redis_cache.clear(pattern)

        count += self._memory_cache.clear(pattern)
        return count

    def get_stats(self) -> dict[str, Any]:
        """Get combined cache statistics."""
        self._ensure_initialized()

        stats: dict[str, Any] = {
            "enabled": CACHE_ENABLED,
            "version": CACHE_VERSION,
            "default_ttl_seconds": DEFAULT_TTL_SECONDS,
        }

        if self._redis_cache:
            stats["redis"] = self._redis_cache.get_stats()

        stats["memory"] = self._memory_cache.get_stats()

        return stats

    def close(self) -> None:
        """Close all cache providers."""
        if self._redis_cache:
            self._redis_cache.close()
        self._memory_cache.close()
        self._initialized = False

    # Async methods for compatibility

    async def get_async(self, key: str) -> Any:
        """Async wrapper for get."""
        return await asyncio.get_event_loop().run_in_executor(None, self.get, key)

    async def set_async(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Async wrapper for set."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.set, key, value, ttl
        )

    async def delete_async(self, key: str) -> bool:
        """Async wrapper for delete."""
        return await asyncio.get_event_loop().run_in_executor(None, self.delete, key)

    async def get_many_async(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values asynchronously using concurrent execution.

        Uses asyncio.gather for parallel fetching instead of sequential.
        """
        if not keys:
            return {}

        # Use gather for concurrent execution
        tasks = [self.get_async(key) for key in keys]
        values = await asyncio.gather(*tasks, return_exceptions=True)

        results: dict[str, Any] = {}
        for key, value in zip(keys, values):
            if value is not None and not isinstance(value, Exception):
                results[key] = value

        return results

    async def batch_save_async(
        self, items: list[tuple[str, Any, int | None]]
    ) -> int:
        """
        Save multiple items asynchronously using concurrent execution.

        Uses asyncio.gather for parallel saving instead of sequential.
        """
        if not items:
            return 0

        # Use gather for concurrent execution
        tasks = [self.set_async(key, data, ttl) for key, data, ttl in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful saves
        return sum(1 for r in results if r is True)


# Global cache manager instance with thread-safe initialization
_cache_manager: CacheManager | None = None
_cache_manager_lock = threading.Lock()


def get_cache_manager() -> CacheManager:
    """
    Get or create the global cache manager instance.

    Uses double-checked locking pattern for thread-safe lazy initialization.
    """
    global _cache_manager

    # First check without lock (fast path)
    if _cache_manager is not None:
        return _cache_manager

    # Acquire lock for initialization
    with _cache_manager_lock:
        # Double-check after acquiring lock
        if _cache_manager is None:
            _cache_manager = CacheManager()

    return _cache_manager


def reset_cache_manager() -> None:
    """Reset the global cache manager (for testing)."""
    global _cache_manager

    with _cache_manager_lock:
        if _cache_manager is not None:
            _cache_manager.close()
            _cache_manager = None
