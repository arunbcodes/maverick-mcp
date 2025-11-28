"""Tests for maverick-data providers."""

import pytest

from maverick_data.providers import (
    BaseStockProvider,
    YFinanceProvider,
)


class TestProviderImports:
    """Test that provider components can be imported."""

    def test_base_provider_import(self):
        """Test BaseStockProvider import."""
        assert BaseStockProvider is not None

    def test_yfinance_provider_import(self):
        """Test YFinanceProvider import."""
        assert YFinanceProvider is not None


class TestYFinanceProvider:
    """Test YFinanceProvider class."""

    def test_create_yfinance_provider(self):
        """Test creating YFinance provider."""
        provider = YFinanceProvider()
        assert provider is not None

    def test_provider_default_settings(self):
        """Test provider has correct default settings."""
        provider = YFinanceProvider()
        assert provider.timeout == 30
        assert provider.max_retries == 3

    def test_provider_custom_settings(self):
        """Test provider accepts custom settings."""
        provider = YFinanceProvider(timeout=60, max_retries=5)
        assert provider.timeout == 60
        assert provider.max_retries == 5

    def test_provider_has_required_methods(self):
        """Test provider has all required interface methods."""
        provider = YFinanceProvider()

        # IStockDataFetcher methods
        assert hasattr(provider, "get_stock_data")
        assert hasattr(provider, "get_stock_info")
        assert hasattr(provider, "get_realtime_quote")
        assert hasattr(provider, "get_multiple_stocks_data")
        assert hasattr(provider, "is_market_open")

    def test_additional_methods(self):
        """Test additional utility methods."""
        provider = YFinanceProvider()

        assert hasattr(provider, "get_news")
        assert hasattr(provider, "get_recommendations")
        assert hasattr(provider, "get_earnings")
        assert hasattr(provider, "is_etf")
        assert hasattr(provider, "clear_cache")

    def test_ticker_cache_initialized(self):
        """Test ticker cache is initialized."""
        provider = YFinanceProvider()
        assert hasattr(provider, "_ticker_cache")
        assert isinstance(provider._ticker_cache, dict)

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        provider = YFinanceProvider()
        # Should not raise
        provider.clear_cache()
        provider.clear_cache("AAPL")
