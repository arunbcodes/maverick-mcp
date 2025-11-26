"""
Cache provider interfaces.

This module defines abstract interfaces for caching operations.
Supports both Redis and in-memory implementations.
"""

from datetime import timedelta
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ICacheProvider(Protocol):
    """
    Interface for caching operations.

    This interface defines the contract for cache storage and retrieval.
    Implementations should handle serialization/deserialization internally.

    Implemented by: maverick-data (RedisCacheBackend, MemoryCacheBackend)
    """

    async def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        ...

    async def set(
        self,
        key: str,
        value: Any,
        ttl: timedelta | int | None = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be serializable)
            ttl: Time-to-live in seconds or as timedelta.
                 None means no expiration.

        Returns:
            True if successful, False otherwise
        """
        ...

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False if not found
        """
        ...

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists and not expired
        """
        ...

    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.

        Args:
            pattern: Glob pattern (e.g., "stock:*", "screening:*")

        Returns:
            Number of keys deleted
        """
        ...

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values efficiently.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values.
            Missing keys are not included in result.
        """
        ...

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: timedelta | int | None = None,
    ) -> bool:
        """
        Set multiple values efficiently.

        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time-to-live for all keys

        Returns:
            True if all values were set successfully
        """
        ...

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter in cache.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment
        """
        ...

    async def get_ttl(self, key: str) -> int | None:
        """
        Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds, None if no expiration or key not found
        """
        ...


@runtime_checkable
class ICacheKeyGenerator(Protocol):
    """
    Interface for generating consistent cache keys.

    This ensures all packages use the same key format for cache entries.

    Implemented by: maverick-data (CacheKeyGenerator)
    """

    def stock_data_key(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> str:
        """
        Generate key for stock data cache.

        Args:
            symbol: Stock ticker
            start_date: Start date
            end_date: End date
            interval: Data interval

        Returns:
            Cache key string
        """
        ...

    def stock_info_key(self, symbol: str) -> str:
        """
        Generate key for stock info cache.

        Args:
            symbol: Stock ticker

        Returns:
            Cache key string
        """
        ...

    def screening_key(
        self,
        strategy: str,
        params_hash: str,
    ) -> str:
        """
        Generate key for screening results cache.

        Args:
            strategy: Screening strategy name
            params_hash: Hash of screening parameters

        Returns:
            Cache key string
        """
        ...

    def research_key(
        self,
        query_hash: str,
        scope: str,
    ) -> str:
        """
        Generate key for research results cache.

        Args:
            query_hash: Hash of research query
            scope: Research scope (basic, standard, comprehensive)

        Returns:
            Cache key string
        """
        ...

    def technical_analysis_key(
        self,
        symbol: str,
        days: int,
    ) -> str:
        """
        Generate key for technical analysis cache.

        Args:
            symbol: Stock ticker
            days: Number of days of data

        Returns:
            Cache key string
        """
        ...
