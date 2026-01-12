"""
In-memory cache provider.

Implements ICacheProvider interface with in-memory storage.
Used as fallback when Redis is unavailable.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import pandas as pd

from maverick_core import ICacheProvider

logger = logging.getLogger("maverick_data.cache.memory")


class MemoryCache(ICacheProvider):
    """In-memory cache provider implementing ICacheProvider interface."""

    def __init__(
        self,
        max_size: int = 1000,
        memory_limit_mb: int = 100,
    ):
        """
        Initialize memory cache provider.

        Args:
            max_size: Maximum number of entries
            memory_limit_mb: Maximum memory usage in megabytes
        """
        self._cache: dict[str, dict[str, Any]] = {}
        self._max_size = max_size
        self._memory_limit_bytes = memory_limit_mb * 1024 * 1024
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
        }

    def _cleanup(self) -> None:
        """Clean up expired entries and enforce size limit."""
        current_time = time.time()

        # Remove expired entries
        expired_keys = [
            k
            for k, v in self._cache.items()
            if "expiry" in v and v["expiry"] < current_time
        ]
        for k in expired_keys:
            del self._cache[k]

        # Calculate current memory usage
        current_memory_bytes = self._calculate_memory_usage()

        # Enforce size and memory limits
        if (
            len(self._cache) > self._max_size
            or current_memory_bytes > self._memory_limit_bytes
        ):
            # Sort by expiry time (oldest first)
            sorted_items = sorted(
                self._cache.items(), key=lambda x: x[1].get("expiry", float("inf"))
            )

            # Remove entries until under limits
            while (
                len(self._cache) > self._max_size
                or self._calculate_memory_usage() > self._memory_limit_bytes
            ) and sorted_items:
                key, _ = sorted_items.pop(0)
                if key in self._cache:
                    del self._cache[key]
                    self._stats["evictions"] += 1

    def _calculate_memory_usage(self) -> int:
        """Calculate approximate memory usage of cache."""
        memory_bytes = 0
        for entry in self._cache.values():
            if "data" in entry:
                try:
                    data = entry["data"]
                    if isinstance(data, pd.DataFrame):
                        memory_bytes += data.memory_usage(deep=True).sum()
                    elif hasattr(data, "__sizeof__"):
                        memory_bytes += data.__sizeof__()
                    elif isinstance(data, str | bytes):
                        memory_bytes += len(data)
                except Exception:
                    pass
        return memory_bytes

    async def get(self, key: str) -> Any:
        """Get value from cache."""
        if key in self._cache:
            entry = self._cache[key]
            if "expiry" not in entry or entry["expiry"] > time.time():
                self._stats["hits"] += 1
                return entry["data"]
            else:
                # Clean up expired entry
                del self._cache[key]

        self._stats["misses"] += 1
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache with optional TTL."""
        entry: dict[str, Any] = {"data": value}
        if ttl:
            entry["expiry"] = time.time() + ttl

        self._cache[key] = entry
        self._stats["sets"] += 1

        # Clean up if needed
        if len(self._cache) > self._max_size:
            self._cleanup()

        return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if key in self._cache:
            entry = self._cache[key]
            return "expiry" not in entry or entry["expiry"] > time.time()
        return False

    async def clear(self, pattern: str | None = None) -> int:
        """Clear cache entries matching pattern."""
        if pattern:
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                keys_to_delete = [
                    k for k in self._cache.keys() if k.startswith(prefix)
                ]
            else:
                keys_to_delete = [k for k in self._cache.keys() if k == pattern]

            for k in keys_to_delete:
                del self._cache[k]
            return len(keys_to_delete)
        else:
            count = len(self._cache)
            self._cache.clear()
            return count

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "backend": "memory",
            "size": len(self._cache),
            "max_size": self._max_size,
            "memory_bytes": self._calculate_memory_usage(),
            "memory_mb": self._calculate_memory_usage() / (1024 * 1024),
            "memory_limit_mb": self._memory_limit_bytes / (1024 * 1024),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "sets": self._stats["sets"],
            "evictions": self._stats["evictions"],
            "hit_rate_percent": round(hit_rate, 2),
        }

    async def close(self) -> None:
        """Close cache (clear all entries)."""
        self._cache.clear()
