"""Tests for maverick-data providers."""

import pytest

from maverick_data.providers import (
    BaseStockProvider,
    YFinanceProvider,
    MarketDataProvider,
    MacroDataProvider,
    MARKET_INDICES,
    SECTOR_ETFS,
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


class TestMarketDataProviderImports:
    """Test MarketDataProvider imports and constants."""

    def test_market_data_provider_import(self):
        """Test MarketDataProvider import."""
        assert MarketDataProvider is not None

    def test_market_indices_constant(self):
        """Test MARKET_INDICES constant."""
        assert isinstance(MARKET_INDICES, dict)
        assert "^GSPC" in MARKET_INDICES
        assert "^DJI" in MARKET_INDICES
        assert "^IXIC" in MARKET_INDICES
        assert "^VIX" in MARKET_INDICES

    def test_sector_etfs_constant(self):
        """Test SECTOR_ETFS constant."""
        assert isinstance(SECTOR_ETFS, dict)
        assert "Technology" in SECTOR_ETFS
        assert "Healthcare" in SECTOR_ETFS
        assert "Financials" in SECTOR_ETFS
        assert "Energy" in SECTOR_ETFS


class TestMarketDataProvider:
    """Test MarketDataProvider class."""

    def test_create_market_data_provider(self):
        """Test creating MarketDataProvider."""
        provider = MarketDataProvider()
        assert provider is not None

    def test_provider_has_session(self):
        """Test provider has HTTP session."""
        provider = MarketDataProvider()
        assert hasattr(provider, "session")
        assert provider.session is not None

    def test_provider_has_required_methods(self):
        """Test provider has all required methods."""
        provider = MarketDataProvider()

        # Sync methods
        assert hasattr(provider, "get_market_summary")
        assert hasattr(provider, "get_top_gainers")
        assert hasattr(provider, "get_top_losers")
        assert hasattr(provider, "get_most_active")
        assert hasattr(provider, "get_sector_performance")
        assert hasattr(provider, "get_earnings_calendar")
        assert hasattr(provider, "get_market_overview")

        # Async methods
        assert hasattr(provider, "get_market_summary_async")
        assert hasattr(provider, "get_top_gainers_async")
        assert hasattr(provider, "get_top_losers_async")
        assert hasattr(provider, "get_most_active_async")
        assert hasattr(provider, "get_sector_performance_async")
        assert hasattr(provider, "get_market_overview_async")

    def test_methods_are_callable(self):
        """Test provider methods are callable."""
        provider = MarketDataProvider()

        assert callable(provider.get_market_summary)
        assert callable(provider.get_top_gainers)
        assert callable(provider.get_top_losers)
        assert callable(provider.get_most_active)
        assert callable(provider.get_sector_performance)


class TestMacroDataProviderImports:
    """Test MacroDataProvider imports."""

    def test_macro_data_provider_import(self):
        """Test MacroDataProvider import."""
        assert MacroDataProvider is not None


class TestMacroDataProvider:
    """Test MacroDataProvider class."""

    def test_create_macro_data_provider(self):
        """Test creating MacroDataProvider."""
        provider = MacroDataProvider()
        assert provider is not None

    def test_provider_default_settings(self):
        """Test provider has correct default settings."""
        provider = MacroDataProvider()
        assert provider.window_days == MacroDataProvider.MAX_WINDOW_DAYS
        assert provider.lookback_days == 30

    def test_provider_custom_window(self):
        """Test provider accepts custom window."""
        provider = MacroDataProvider(window_days=180)
        assert provider.window_days == 180

    def test_provider_has_weights(self):
        """Test provider has sentiment weights."""
        provider = MacroDataProvider()
        assert hasattr(provider, "weights")
        assert isinstance(provider.weights, dict)

        # Check weight keys
        assert "vix" in provider.weights
        assert "sp500_momentum" in provider.weights
        assert "nasdaq_momentum" in provider.weights
        assert "usd_momentum" in provider.weights
        assert "inflation_rate" in provider.weights
        assert "gdp_growth_rate" in provider.weights
        assert "unemployment_rate" in provider.weights

    def test_weights_sum_to_one(self):
        """Test sentiment weights sum to approximately 1.0."""
        provider = MacroDataProvider()
        total_weight = sum(provider.weights.values())
        assert abs(total_weight - 1.0) < 0.01  # Allow small floating point error

    def test_provider_has_required_methods(self):
        """Test provider has all required methods."""
        provider = MacroDataProvider()

        # Core data methods
        assert hasattr(provider, "get_gdp_growth_rate")
        assert hasattr(provider, "get_unemployment_rate")
        assert hasattr(provider, "get_inflation_rate")
        assert hasattr(provider, "get_vix")

        # Momentum methods
        assert hasattr(provider, "get_sp500_momentum")
        assert hasattr(provider, "get_nasdaq_momentum")
        assert hasattr(provider, "get_usd_momentum")

        # Performance methods
        assert hasattr(provider, "get_sp500_performance")
        assert hasattr(provider, "get_nasdaq_performance")

        # Aggregate methods
        assert hasattr(provider, "get_macro_statistics")
        assert hasattr(provider, "get_historical_data")

        # Utility methods
        assert hasattr(provider, "normalize_indicators")
        assert hasattr(provider, "update_historical_bounds")
        assert hasattr(provider, "default_bounds")

    def test_default_bounds_structure(self):
        """Test default bounds have correct structure."""
        provider = MacroDataProvider()

        for key in ["vix", "sp500_momentum", "nasdaq_momentum", "usd_momentum",
                    "inflation_rate", "gdp_growth_rate", "unemployment_rate"]:
            bounds = provider.default_bounds(key)
            assert isinstance(bounds, dict)
            assert "min" in bounds
            assert "max" in bounds
            assert isinstance(bounds["min"], (int, float))
            assert isinstance(bounds["max"], (int, float))
            assert bounds["min"] < bounds["max"]

    def test_normalize_indicators_handles_none(self):
        """Test normalize_indicators handles None values."""
        provider = MacroDataProvider()
        indicators = {"vix": None, "sp500_momentum": None}
        normalized = provider.normalize_indicators(indicators)

        assert "vix" in normalized
        assert "sp500_momentum" in normalized
        assert normalized["vix"] == 0.5  # Default for None
        assert normalized["sp500_momentum"] == 0.5

    def test_normalize_indicators_clamps_values(self):
        """Test normalize_indicators clamps to [0, 1]."""
        provider = MacroDataProvider()
        # Use extreme values
        indicators = {"vix": 100.0, "sp500_momentum": -100.0}
        normalized = provider.normalize_indicators(indicators)

        for value in normalized.values():
            assert 0.0 <= value <= 1.0
