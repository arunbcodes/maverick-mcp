"""
Cache Backend Implementations.

Single Responsibility: Each backend handles one storage mechanism.
Open/Closed: Add new backends without modifying existing ones.
Liskov Substitution: All backends implement ICacheBackend interface.
Interface Segregation: Minimal interface with only essential operations.
Dependency Inversion: Services depend on ICacheBackend abstraction.

This module provides pluggable cache backends that can be swapped or deployed
independently, supporting future microservice architecture.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class ICacheBackend(ABC):
    """
    Abstract interface for cache backends.

    Defines the contract that all cache implementations must follow.
    This abstraction enables:
        - Swappable implementations (Redis, Memcached, DynamoDB, etc.)
        - Testing with mock backends
        - Gradual migration between cache systems
        - Independent deployment of cache services

    Design Philosophy:
        - Minimal interface: Only essential operations
        - Async-first: All operations are async for scalability
        - Type-safe: Strong typing for reliability
        - Error-tolerant: Never crashes the calling service

    All methods should be idempotent and fail gracefully.
    """

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """
        Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and valid, None otherwise

        Note:
            Must handle deserialization internally.
            Must return None on errors (never raise).
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> bool:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be serializable)
            ttl_seconds: Time-to-live in seconds (None = no expiration)

        Returns:
            True if stored successfully, False otherwise

        Note:
            Must handle serialization internally.
            Must return False on errors (never raise).
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Remove value from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted, False if not found or error

        Note:
            Must be idempotent (deleting non-existent key returns False).
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise

        Note:
            Must return False on errors (never raise).
        """
        pass

    @abstractmethod
    async def clear_namespace(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "concall:transcript:v1:*")

        Returns:
            Number of keys deleted

        Note:
            Used for namespace-based cache invalidation.
            Must handle errors gracefully.
        """
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """
        Get cache backend statistics.

        Returns:
            Dictionary with stats (implementation-specific)

        Note:
            Useful for monitoring and debugging.
            Should include: hits, misses, size, etc.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if cache backend is healthy.

        Returns:
            True if backend is operational, False otherwise

        Note:
            Used for readiness/liveness probes in deployment.
            Must never raise exceptions.
        """
        pass


class RedisCacheBackend(ICacheBackend):
    """
    Production Redis cache backend.

    Features:
        - Connection pooling for efficiency
        - Automatic reconnection on failure
        - JSON serialization for complex types
        - TTL support for automatic expiration
        - Namespace-based invalidation
        - Comprehensive error handling

    Design Benefits:
        - Production-ready with connection pooling
        - Scalable to handle high throughput
        - Resilient to Redis temporary failures
        - Supports distributed deployment

    Example:
        >>> backend = RedisCacheBackend(
        ...     host="localhost",
        ...     port=6379,
        ...     db=0
        ... )
        >>> await backend.set("key", {"data": "value"}, ttl_seconds=3600)
        True
        >>> await backend.get("key")
        {'data': 'value'}
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int = 0,
        password: str | None = None,
        max_connections: int = 10,
        socket_timeout: float = 5.0,
    ):
        """
        Initialize Redis backend.

        Args:
            host: Redis host (default: from REDIS_HOST env or localhost)
            port: Redis port (default: from REDIS_PORT env or 6379)
            db: Redis database number (default: 0)
            password: Redis password (default: from REDIS_PASSWORD env)
            max_connections: Maximum connection pool size
            socket_timeout: Socket timeout in seconds
        """
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db
        self.password = password or os.getenv("REDIS_PASSWORD")
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout

        self._client: redis.Redis | None = None
        self._pool: redis.ConnectionPool | None = None
        self._connected = False

        # Stats tracking
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
        }

    async def _ensure_connection(self) -> redis.Redis | None:
        """
        Ensure Redis connection is established.

        Returns:
            Redis client or None if connection fails

        Note:
            Lazy connection establishment for efficiency.
            Handles connection failures gracefully.
        """
        if self._connected and self._client:
            return self._client

        try:
            # Create connection pool if not exists
            if not self._pool:
                self._pool = redis.ConnectionPool(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password if self.password else None,
                    max_connections=self.max_connections,
                    socket_timeout=self.socket_timeout,
                    decode_responses=False,  # We'll handle decoding
                )

            # Create client from pool
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            return self._client

        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self._connected = False
            self._client = None
            return None

    async def get(self, key: str) -> Any | None:
        """Retrieve value from Redis cache."""
        try:
            client = await self._ensure_connection()
            if not client:
                self._stats["misses"] += 1
                return None

            value = await client.get(key)
            if value is None:
                self._stats["misses"] += 1
                return None

            # Deserialize JSON
            deserialized = json.loads(value.decode("utf-8"))
            self._stats["hits"] += 1
            return deserialized

        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            self._stats["errors"] += 1
            self._stats["misses"] += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> bool:
        """Store value in Redis cache."""
        try:
            client = await self._ensure_connection()
            if not client:
                return False

            # Serialize to JSON
            serialized = json.dumps(value, default=str).encode("utf-8")

            # Set with optional TTL
            if ttl_seconds:
                await client.setex(key, ttl_seconds, serialized)
            else:
                await client.set(key, serialized)

            self._stats["sets"] += 1
            return True

        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            self._stats["errors"] += 1
            return False

    async def delete(self, key: str) -> bool:
        """Remove value from Redis cache."""
        try:
            client = await self._ensure_connection()
            if not client:
                return False

            result = await client.delete(key)
            self._stats["deletes"] += 1
            return result > 0

        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            self._stats["errors"] += 1
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            client = await self._ensure_connection()
            if not client:
                return False

            result = await client.exists(key)
            return result > 0

        except Exception as e:
            logger.warning(f"Cache exists error for key {key}: {e}")
            self._stats["errors"] += 1
            return False

    async def clear_namespace(self, pattern: str) -> int:
        """Clear all keys matching pattern in Redis."""
        try:
            client = await self._ensure_connection()
            if not client:
                return 0

            # Use SCAN for safe iteration (doesn't block Redis)
            count = 0
            cursor = "0"
            while cursor != 0:
                cursor, keys = await client.scan(
                    cursor=cursor if isinstance(cursor, int) else int(cursor),
                    match=pattern,
                    count=100,
                )
                if keys:
                    await client.delete(*keys)
                    count += len(keys)

            logger.info(f"Cleared {count} keys matching pattern: {pattern}")
            return count

        except Exception as e:
            logger.warning(f"Cache clear_namespace error for pattern {pattern}: {e}")
            self._stats["errors"] += 1
            return 0

    async def get_stats(self) -> dict[str, Any]:
        """Get Redis cache statistics."""
        try:
            client = await self._ensure_connection()
            if not client:
                return {**self._stats, "connected": False}

            # Get Redis INFO stats
            info = await client.info("stats")
            return {
                **self._stats,
                "connected": True,
                "redis_hits": info.get("keyspace_hits", 0),
                "redis_misses": info.get("keyspace_misses", 0),
                "redis_keys": await client.dbsize(),
            }

        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {**self._stats, "connected": False, "error": str(e)}

    async def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            client = await self._ensure_connection()
            if not client:
                return False

            await client.ping()
            return True

        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection and cleanup resources."""
        try:
            if self._client:
                await self._client.close()
            if self._pool:
                await self._pool.disconnect()
            self._connected = False
            logger.info("Redis connection closed")

        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")


class InMemoryCacheBackend(ICacheBackend):
    """
    In-memory cache backend for development and testing.

    Features:
        - No external dependencies
        - Fast for local development
        - TTL support with background cleanup
        - Thread-safe operations
        - Memory-efficient with size limits

    Design Benefits:
        - Zero setup required
        - Deterministic testing
        - Quick iteration during development
        - Fallback when Redis unavailable

    Limitations:
        - Not shared across processes
        - Lost on restart
        - Limited to single machine

    Example:
        >>> backend = InMemoryCacheBackend(max_size=1000)
        >>> await backend.set("key", "value", ttl_seconds=60)
        True
        >>> await backend.get("key")
        'value'
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize in-memory cache.

        Args:
            max_size: Maximum number of keys to cache (LRU eviction)
        """
        self.max_size = max_size
        self._cache: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

        # Stats tracking
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
        }

    async def get(self, key: str) -> Any | None:
        """Retrieve value from memory cache."""
        async with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[key]

            # Check TTL
            if entry["expires_at"]:
                if datetime.now() > entry["expires_at"]:
                    # Expired
                    del self._cache[key]
                    self._stats["misses"] += 1
                    return None

            self._stats["hits"] += 1
            # Update access time for LRU
            entry["accessed_at"] = datetime.now()
            return entry["value"]

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> bool:
        """Store value in memory cache."""
        async with self._lock:
            # Check size limit
            if len(self._cache) >= self.max_size and key not in self._cache:
                # Evict LRU entry
                await self._evict_lru()

            # Calculate expiration
            expires_at = None
            if ttl_seconds:
                expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

            # Store entry
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "accessed_at": datetime.now(),
            }

            self._stats["sets"] += 1
            return True

    async def delete(self, key: str) -> bool:
        """Remove value from memory cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats["deletes"] += 1
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        async with self._lock:
            if key not in self._cache:
                return False

            entry = self._cache[key]

            # Check TTL
            if entry["expires_at"]:
                if datetime.now() > entry["expires_at"]:
                    del self._cache[key]
                    return False

            return True

    async def clear_namespace(self, pattern: str) -> int:
        """Clear all keys matching pattern in memory cache."""
        async with self._lock:
            # Convert Redis-style pattern to Python pattern
            import re

            regex_pattern = pattern.replace("*", ".*").replace("?", ".")
            regex = re.compile(f"^{regex_pattern}$")

            # Find matching keys
            keys_to_delete = [key for key in self._cache if regex.match(key)]

            # Delete them
            for key in keys_to_delete:
                del self._cache[key]

            return len(keys_to_delete)

    async def get_stats(self) -> dict[str, Any]:
        """Get memory cache statistics."""
        async with self._lock:
            return {
                **self._stats,
                "size": len(self._cache),
                "max_size": self.max_size,
                "utilization": len(self._cache) / self.max_size,
            }

    async def health_check(self) -> bool:
        """Check if memory cache is healthy (always true)."""
        return True

    async def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]["accessed_at"],
        )

        del self._cache[lru_key]
        self._stats["evictions"] += 1
        logger.debug(f"Evicted LRU key: {lru_key}")

    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed

        Note:
            Should be called periodically for memory efficiency.
        """
        async with self._lock:
            now = datetime.now()
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if entry["expires_at"] and now > entry["expires_at"]
            ]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired entries")

            return len(expired_keys)
