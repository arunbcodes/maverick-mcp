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
from maverick_core.config import Settings, get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

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
        redis_db: int | None = None,
        memory_max_size: int = 1000,
        memory_limit_mb: int = 100,
    ):
        """
        Initialize cache manager.

        Args:
            redis_host: Redis host (optional, uses env var)
            redis_port: Redis port (optional, uses env var)
            redis_port: Redis db (optional, uses env var)
            memory_max_size: Maximum entries for memory cache
            memory_limit_mb: Maximum memory for memory cache in MB
        """
        self._redis_cache: RedisCache | None = None
        self._memory_cache: MemoryCache = MemoryCache(
            max_size=memory_max_size, memory_limit_mb=memory_limit_mb
        )
        self._redis_host = redis_host
        self._redis_port = redis_port
        self._redis_db = redis_db
        self._initialized = False

    def _ensure_initialized(self) -> ICacheProvider:
        """Ensure cache provider is initialized and return primary provider."""
        if not self._initialized:
            if CACHE_ENABLED:
                try:
                    logger.info(f"Initializing cache manager with Redis host: {self._redis_host}, port: {self._redis_port}, db: {self._redis_db}")
                    self._redis_cache = RedisCache(
                        host=self._redis_host,
                        port=self._redis_port,
                        db=self._redis_db,
                    )
                    logger.info("Redis cache provider initialized (connection will be tested on first use)")
                except Exception as e:
                    logger.warning(f"Redis initialization failed: {e}")
                    self._redis_cache = None
            else:
                logger.warning(f"Cache disabled, using memory cache")
                self._redis_cache = None

            self._initialized = True

        # Always return a valid cache provider
        if self._redis_cache:
            return self._redis_cache
        return self._memory_cache

    async def get(self, key: str) -> Any:
        """Get value from cache."""
        if not CACHE_ENABLED:
            return None

        self._ensure_initialized()

        # Try Redis first
        if self._redis_cache:
            try:
                value = await self._redis_cache.get(key)
                if value is not None:
                    return value
            except Exception as e:
                logger.warning(f"Redis get failed, falling back to memory: {e}")

        # Fall back to memory
        return await self._memory_cache.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache with optional TTL."""
        if not CACHE_ENABLED:
            return False

        resolved_ttl = ttl if ttl is not None else DEFAULT_TTL_SECONDS
        self._ensure_initialized()

        # Try Redis first
        if self._redis_cache:
            try:
                if await self._redis_cache.set(key, value, resolved_ttl):
                    return True
            except Exception as e:
                logger.warning(f"Redis set failed, falling back to memory: {e}")

        # Fall back to memory
        return await self._memory_cache.set(key, value, resolved_ttl)

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not CACHE_ENABLED:
            return False

        self._ensure_initialized()
        deleted = False

        if self._redis_cache:
            try:
                deleted = await self._redis_cache.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")

        deleted = await self._memory_cache.delete(key) or deleted
        return deleted

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not CACHE_ENABLED:
            return False

        self._ensure_initialized()

        if self._redis_cache:
            try:
                if await self._redis_cache.exists(key):
                    return True
            except Exception as e:
                logger.warning(f"Redis exists check failed: {e}")

        return await self._memory_cache.exists(key)

    async def clear(self, pattern: str | None = None) -> int:
        """Clear cache entries matching pattern."""
        self._ensure_initialized()
        count = 0

        if self._redis_cache:
            try:
                count += await self._redis_cache.clear(pattern)
            except Exception as e:
                logger.warning(f"Redis clear failed: {e}")

        count += await self._memory_cache.clear(pattern)
        return count

    async def get_stats(self) -> dict[str, Any]:
        """Get combined cache statistics."""
        self._ensure_initialized()

        stats: dict[str, Any] = {
            "enabled": CACHE_ENABLED,
            "version": CACHE_VERSION,
            "default_ttl_seconds": DEFAULT_TTL_SECONDS,
        }

        if self._redis_cache:
            try:
                stats["redis"] = await self._redis_cache.get_stats()
            except Exception as e:
                logger.warning(f"Failed to get Redis stats: {e}")
                stats["redis"] = {"error": str(e)}

        stats["memory"] = await self._memory_cache.get_stats()

        return stats

    async def close(self) -> None:
        """Close all cache providers."""
        if self._redis_cache:
            await self._redis_cache.close()
        await self._memory_cache.close()
        self._initialized = False

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values asynchronously using concurrent execution.

        Uses asyncio.gather for parallel fetching instead of sequential.
        """
        if not keys:
            return {}

        # Use gather for concurrent execution
        tasks = [self.get(key) for key in keys]
        values = await asyncio.gather(*tasks, return_exceptions=True)

        results: dict[str, Any] = {}
        for key, value in zip(keys, values):
            if value is not None and not isinstance(value, Exception):
                results[key] = value

        return results

    async def set_many(
        self, items: list[tuple[str, Any, int | None]]
    ) -> int:
        """
        Save multiple items asynchronously using concurrent execution.

        Uses asyncio.gather for parallel saving instead of sequential.
        """
        if not items:
            return 0

        # Use gather for concurrent execution
        tasks = [self.set(key, data, ttl) for key, data, ttl in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful saves
        return sum(1 for r in results if r is True)

    async def clear_pattern(self, pattern: str) -> int:
        """Clear cache entries matching pattern (alias for clear with pattern)."""
        return await self.clear(pattern)

    async def clear_all(self) -> int:
        """Clear all cache entries (alias for clear without pattern)."""
        return await self.clear(None)


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
            _cache_manager = CacheManager(redis_host = settings.redis.host,
                                          redis_port = settings.redis.port,
                                          redis_db = settings.redis.db)

    return _cache_manager


async def reset_cache_manager() -> None:
    """Reset the global cache manager (for testing)."""
    global _cache_manager

    with _cache_manager_lock:
        if _cache_manager is not None:
            await _cache_manager.close()
            _cache_manager = None
