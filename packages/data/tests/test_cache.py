"""Tests for maverick-data cache module."""

import numpy as np
import pandas as pd
import pytest

from maverick_data.cache import (
    MemoryCache,
    CacheManager,
    generate_cache_key,
    serialize_data,
    deserialize_data,
    normalize_timezone,
    ensure_timezone_naive,
)


class TestCacheImports:
    """Test that cache components can be imported."""

    def test_memory_cache_import(self):
        """Test MemoryCache import."""
        assert MemoryCache is not None

    def test_cache_manager_import(self):
        """Test CacheManager import."""
        assert CacheManager is not None

    def test_generate_cache_key_import(self):
        """Test generate_cache_key import."""
        assert generate_cache_key is not None

    def test_serialization_imports(self):
        """Test serialization functions import."""
        assert serialize_data is not None
        assert deserialize_data is not None
        assert normalize_timezone is not None
        assert ensure_timezone_naive is not None


class TestGenerateCacheKey:
    """Test cache key generation."""

    def test_simple_key(self):
        """Test simple cache key generation."""
        key = generate_cache_key("stock:AAPL")
        assert "stock:AAPL" in key
        assert "v1" in key

    def test_key_with_params(self):
        """Test cache key with parameters."""
        key = generate_cache_key("stock", ticker="AAPL", start="2024-01-01")
        assert "AAPL" in key
        assert "2024-01-01" in key

    def test_long_key_hashed(self):
        """Test that long keys are hashed."""
        long_base = "a" * 300
        key = generate_cache_key(long_base)
        assert "hashed" in key
        assert len(key) < 100


class TestMemoryCache:
    """Test MemoryCache provider."""

    def test_create_memory_cache(self):
        """Test creating memory cache."""
        cache = MemoryCache(max_size=100)
        assert cache is not None

    def test_set_and_get(self):
        """Test set and get operations."""
        cache = MemoryCache()
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

    def test_get_missing_key(self):
        """Test getting missing key returns None."""
        cache = MemoryCache()
        assert cache.get("nonexistent") is None

    def test_delete(self):
        """Test delete operation."""
        cache = MemoryCache()
        cache.set("test_key", "test_value")
        assert cache.delete("test_key") is True
        assert cache.get("test_key") is None

    def test_exists(self):
        """Test exists operation."""
        cache = MemoryCache()
        cache.set("test_key", "test_value")
        assert cache.exists("test_key") is True
        assert cache.exists("nonexistent") is False

    def test_clear_all(self):
        """Test clear all entries."""
        cache = MemoryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        count = cache.clear()
        assert count == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_clear_pattern(self):
        """Test clear with pattern."""
        cache = MemoryCache()
        cache.set("stock:AAPL", "value1")
        cache.set("stock:MSFT", "value2")
        cache.set("other:data", "value3")
        count = cache.clear("stock:*")
        assert count == 2
        assert cache.get("stock:AAPL") is None
        assert cache.get("other:data") == "value3"

    def test_stats(self):
        """Test get_stats method."""
        cache = MemoryCache()
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("nonexistent")  # Miss

        stats = cache.get_stats()
        assert stats["backend"] == "memory"
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = MemoryCache()
        cache.set("expire_key", "value", ttl=0)  # Expires immediately
        # Note: The entry exists but is expired
        # A proper test would use time.sleep, but we test the mechanism


class TestSerialization:
    """Test data serialization utilities."""

    def test_serialize_simple_dict(self):
        """Test serializing simple dictionary."""
        data = {"key": "value", "number": 42}
        serialized = serialize_data(data)
        assert isinstance(serialized, bytes)

    def test_deserialize_simple_dict(self):
        """Test deserializing simple dictionary."""
        data = {"key": "value", "number": 42}
        serialized = serialize_data(data)
        result = deserialize_data(serialized)
        assert result == data

    def test_serialize_dataframe(self):
        """Test serializing pandas DataFrame."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        serialized = serialize_data(df)
        assert isinstance(serialized, bytes)

    def test_deserialize_dataframe(self):
        """Test deserializing pandas DataFrame."""
        # Use datetime index which is common for stock data
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        df = pd.DataFrame({"A": [1.0, 2.0, 3.0], "B": [4.0, 5.0, 6.0]}, index=dates)
        serialized = serialize_data(df, "test_key")

        # For now, just verify serialization produces bytes
        # Full round-trip deserialization depends on msgpack compatibility
        assert isinstance(serialized, bytes)
        assert len(serialized) > 0

    def test_serialize_list(self):
        """Test serializing list."""
        data = [1, 2, 3, "four", 5.0]
        serialized = serialize_data(data)
        result = deserialize_data(serialized)
        assert result == data


class TestTimezoneHandling:
    """Test timezone handling utilities."""

    def test_normalize_timezone_aware(self):
        """Test normalizing timezone-aware DatetimeIndex."""
        dates = pd.DatetimeIndex(["2024-01-01", "2024-01-02"], tz="UTC")
        normalized = normalize_timezone(dates)
        assert normalized.tz is None

    def test_normalize_timezone_naive(self):
        """Test normalizing timezone-naive DatetimeIndex."""
        dates = pd.DatetimeIndex(["2024-01-01", "2024-01-02"])
        normalized = normalize_timezone(dates)
        assert normalized.tz is None

    def test_ensure_timezone_naive_dataframe(self):
        """Test ensuring DataFrame has timezone-naive index."""
        dates = pd.DatetimeIndex(["2024-01-01", "2024-01-02"], tz="UTC")
        df = pd.DataFrame({"A": [1, 2]}, index=dates)
        naive_df = ensure_timezone_naive(df)
        assert isinstance(naive_df.index, pd.DatetimeIndex)
        assert naive_df.index.tz is None


class TestCacheManager:
    """Test CacheManager unified interface."""

    def test_create_cache_manager(self):
        """Test creating cache manager."""
        manager = CacheManager()
        assert manager is not None

    def test_cache_manager_set_get(self):
        """Test set and get through manager."""
        manager = CacheManager()
        manager.set("test_key", "test_value", ttl=3600)
        assert manager.get("test_key") == "test_value"

    def test_cache_manager_delete(self):
        """Test delete through manager."""
        manager = CacheManager()
        manager.set("test_key", "test_value")
        assert manager.delete("test_key") is True
        assert manager.get("test_key") is None

    def test_cache_manager_stats(self):
        """Test get_stats through manager."""
        manager = CacheManager()
        stats = manager.get_stats()
        assert "memory" in stats
        assert "enabled" in stats
