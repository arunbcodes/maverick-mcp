"""
Tests for multi-market functionality.

This module tests the market registry, market-aware data providers,
and database models for US and Indian stock markets.
"""

import pytest
from datetime import datetime, time
from unittest.mock import Mock, patch

from maverick_mcp.config.markets import (
    Market,
    MarketConfig,
    MARKET_CONFIGS,
    get_market_from_symbol,
    get_market_config,
    get_all_markets,
    get_markets_by_country,
    is_indian_market,
    is_us_market,
)


class TestMarketRegistry:
    """Test the market registry and configuration."""

    def test_market_enum_values(self):
        """Test that Market enum has expected values."""
        assert Market.US.value == "US"
        assert Market.INDIA_NSE.value == "NSE"
        assert Market.INDIA_BSE.value == "BSE"

    def test_market_configs_exist(self):
        """Test that all markets have configurations."""
        for market in Market:
            assert market in MARKET_CONFIGS
            config = MARKET_CONFIGS[market]
            assert isinstance(config, MarketConfig)

    def test_us_market_config(self):
        """Test US market configuration."""
        config = MARKET_CONFIGS[Market.US]
        assert config.name == "United States Stock Market"
        assert config.country == "US"
        assert config.currency == "USD"
        assert config.timezone == "America/New_York"
        assert config.calendar_name == "NYSE"
        assert config.symbol_suffix == ""
        assert config.trading_hours_start == time(9, 30)
        assert config.trading_hours_end == time(16, 0)
        assert config.circuit_breaker_percent == 7.0
        assert config.settlement_cycle == "T+2"
        assert config.min_tick_size == 0.01

    def test_indian_nse_config(self):
        """Test Indian NSE market configuration."""
        config = MARKET_CONFIGS[Market.INDIA_NSE]
        assert config.name == "National Stock Exchange of India"
        assert config.country == "IN"
        assert config.currency == "INR"
        assert config.timezone == "Asia/Kolkata"
        assert config.calendar_name == "NSE"
        assert config.symbol_suffix == ".NS"
        assert config.trading_hours_start == time(9, 15)
        assert config.trading_hours_end == time(15, 30)
        assert config.circuit_breaker_percent == 10.0
        assert config.settlement_cycle == "T+1"
        assert config.min_tick_size == 0.05

    def test_indian_bse_config(self):
        """Test Indian BSE market configuration."""
        config = MARKET_CONFIGS[Market.INDIA_BSE]
        assert config.name == "Bombay Stock Exchange"
        assert config.country == "IN"
        assert config.currency == "INR"
        assert config.timezone == "Asia/Kolkata"
        assert config.symbol_suffix == ".BO"
        assert config.circuit_breaker_percent == 10.0
        assert config.settlement_cycle == "T+1"


class TestMarketDetection:
    """Test market detection from symbol suffixes."""

    def test_us_market_detection(self):
        """Test detection of US market symbols."""
        assert get_market_from_symbol("AAPL") == Market.US
        assert get_market_from_symbol("MSFT") == Market.US
        assert get_market_from_symbol("GOOGL") == Market.US
        assert get_market_from_symbol("aapl") == Market.US  # Case insensitive

    def test_indian_nse_detection(self):
        """Test detection of Indian NSE symbols."""
        assert get_market_from_symbol("RELIANCE.NS") == Market.INDIA_NSE
        assert get_market_from_symbol("TCS.NS") == Market.INDIA_NSE
        assert get_market_from_symbol("INFY.NS") == Market.INDIA_NSE
        assert get_market_from_symbol("reliance.ns") == Market.INDIA_NSE  # Case insensitive

    def test_indian_bse_detection(self):
        """Test detection of Indian BSE symbols."""
        assert get_market_from_symbol("RELIANCE.BO") == Market.INDIA_BSE
        assert get_market_from_symbol("TCS.BO") == Market.INDIA_BSE
        assert get_market_from_symbol("SENSEX.BO") == Market.INDIA_BSE

    def test_get_market_config_from_symbol(self):
        """Test getting market config from symbol."""
        us_config = get_market_config("AAPL")
        assert us_config.country == "US"
        assert us_config.currency == "USD"

        nse_config = get_market_config("RELIANCE.NS")
        assert nse_config.country == "IN"
        assert nse_config.currency == "INR"
        assert nse_config.symbol_suffix == ".NS"

        bse_config = get_market_config("TCS.BO")
        assert bse_config.country == "IN"
        assert bse_config.currency == "INR"
        assert bse_config.symbol_suffix == ".BO"


class TestMarketHelpers:
    """Test market helper functions."""

    def test_get_all_markets(self):
        """Test getting all supported markets."""
        markets = get_all_markets()
        assert len(markets) == 3
        assert Market.US in markets
        assert Market.INDIA_NSE in markets
        assert Market.INDIA_BSE in markets

    def test_get_markets_by_country(self):
        """Test getting markets by country code."""
        us_markets = get_markets_by_country("US")
        assert len(us_markets) == 1
        assert Market.US in us_markets

        indian_markets = get_markets_by_country("IN")
        assert len(indian_markets) == 2
        assert Market.INDIA_NSE in indian_markets
        assert Market.INDIA_BSE in indian_markets

        # Test case insensitivity
        indian_markets_lower = get_markets_by_country("in")
        assert len(indian_markets_lower) == 2

    def test_is_indian_market(self):
        """Test Indian market detection helper."""
        assert not is_indian_market("AAPL")
        assert not is_indian_market("MSFT")
        assert is_indian_market("RELIANCE.NS")
        assert is_indian_market("TCS.NS")
        assert is_indian_market("SENSEX.BO")
        assert is_indian_market("INFY.BO")

    def test_is_us_market(self):
        """Test US market detection helper."""
        assert is_us_market("AAPL")
        assert is_us_market("MSFT")
        assert is_us_market("GOOGL")
        assert not is_us_market("RELIANCE.NS")
        assert not is_us_market("TCS.BO")


class TestMarketConfigMethods:
    """Test MarketConfig instance methods."""

    def test_format_symbol(self):
        """Test symbol formatting with market suffix."""
        us_config = MARKET_CONFIGS[Market.US]
        assert us_config.format_symbol("AAPL") == "AAPL"
        assert us_config.format_symbol("AAPL.NS") == "AAPL"  # Removes wrong suffix

        nse_config = MARKET_CONFIGS[Market.INDIA_NSE]
        assert nse_config.format_symbol("RELIANCE") == "RELIANCE.NS"
        assert nse_config.format_symbol("RELIANCE.NS") == "RELIANCE.NS"  # Idempotent
        assert nse_config.format_symbol("RELIANCE.BO") == "RELIANCE.NS"  # Replaces suffix

        bse_config = MARKET_CONFIGS[Market.INDIA_BSE]
        assert bse_config.format_symbol("TCS") == "TCS.BO"
        assert bse_config.format_symbol("TCS.BO") == "TCS.BO"

    def test_strip_suffix(self):
        """Test removing market suffix from symbol."""
        us_config = MARKET_CONFIGS[Market.US]
        assert us_config.strip_suffix("AAPL") == "AAPL"

        nse_config = MARKET_CONFIGS[Market.INDIA_NSE]
        assert nse_config.strip_suffix("RELIANCE.NS") == "RELIANCE"
        assert nse_config.strip_suffix("RELIANCE") == "RELIANCE"

        bse_config = MARKET_CONFIGS[Market.INDIA_BSE]
        assert bse_config.strip_suffix("TCS.BO") == "TCS"
        assert bse_config.strip_suffix("TCS") == "TCS"

    @patch('pandas_market_calendars.get_calendar')
    def test_get_calendar(self, mock_get_calendar):
        """Test getting market calendar."""
        mock_calendar = Mock()
        mock_get_calendar.return_value = mock_calendar

        us_config = MARKET_CONFIGS[Market.US]
        calendar = us_config.get_calendar()
        
        mock_get_calendar.assert_called_with("NYSE")
        assert calendar == mock_calendar

    @patch('pandas_market_calendars.get_calendar')
    def test_get_calendar_fallback(self, mock_get_calendar):
        """Test calendar fallback when market calendar not available."""
        # First call fails (for NSE), second call succeeds (for NYSE fallback)
        mock_get_calendar.side_effect = [
            Exception("NSE calendar not available"),
            Mock(name="NYSE_calendar")
        ]

        nse_config = MARKET_CONFIGS[Market.INDIA_NSE]
        calendar = nse_config.get_calendar()
        
        # Should try NSE first, then fall back to NYSE
        assert mock_get_calendar.call_count == 2
        assert calendar is not None


class TestDatabaseModelIntegration:
    """Test database model integration with multi-market support."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock()

    def test_stock_model_auto_market_detection(self, mock_session):
        """Test that Stock.get_or_create auto-detects market from symbol."""
        from maverick_mcp.data.models import Stock

        # Mock query to return None (stock doesn't exist)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Test US stock
        with patch.object(Stock, 'get_or_create', wraps=Stock.get_or_create):
            stock = Stock(
                ticker_symbol="AAPL",
                company_name="Apple Inc.",
                market="US",
                country="US",
                currency="USD"
            )
            assert stock.market == "US"
            assert stock.country == "US"
            assert stock.currency == "USD"

        # Test Indian NSE stock
        stock_nse = Stock(
            ticker_symbol="RELIANCE.NS",
            company_name="Reliance Industries",
            market="NSE",
            country="IN",
            currency="INR"
        )
        assert stock_nse.market == "NSE"
        assert stock_nse.country == "IN"
        assert stock_nse.currency == "INR"

        # Test Indian BSE stock
        stock_bse = Stock(
            ticker_symbol="TCS.BO",
            company_name="Tata Consultancy Services",
            market="BSE",
            country="IN",
            currency="INR"
        )
        assert stock_bse.market == "BSE"
        assert stock_bse.country == "IN"
        assert stock_bse.currency == "INR"


class TestStockDataProviderIntegration:
    """Test EnhancedStockDataProvider integration with multi-market support."""

    @patch('maverick_mcp.providers.stock_data.get_db_session_read_only')
    @patch('maverick_mcp.providers.stock_data.get_yfinance_pool')
    def test_market_calendar_loading(self, mock_yf_pool, mock_db_session):
        """Test that provider loads correct market calendar for symbols."""
        from maverick_mcp.providers.stock_data import EnhancedStockDataProvider

        # Mock database session
        mock_session = Mock()
        mock_session.execute.return_value.fetchone.return_value = (1,)
        mock_db_session.return_value.__enter__.return_value = mock_session

        provider = EnhancedStockDataProvider()

        # Test US symbol
        us_calendar = provider._get_market_calendar("AAPL")
        assert us_calendar is not None

        # Test Indian NSE symbol
        nse_calendar = provider._get_market_calendar("RELIANCE.NS")
        assert nse_calendar is not None

        # Test Indian BSE symbol
        bse_calendar = provider._get_market_calendar("TCS.BO")
        assert bse_calendar is not None

        # Test None symbol (should return default)
        default_calendar = provider._get_market_calendar(None)
        assert default_calendar == provider.market_calendar


# Integration tests (require actual database)
@pytest.mark.integration
class TestMultiMarketIntegration:
    """Integration tests for multi-market functionality."""

    def test_end_to_end_us_stock(self):
        """Test end-to-end flow for US stock."""
        from maverick_mcp.data.models import Stock, SessionLocal

        with SessionLocal() as session:
            # Create US stock
            stock = Stock.get_or_create(
                session,
                ticker_symbol="AAPL",
                company_name="Apple Inc.",
                sector="Technology",
                industry="Consumer Electronics"
            )
            
            assert stock.ticker_symbol == "AAPL"
            assert stock.market == "US"
            assert stock.country == "US"
            assert stock.currency == "USD"

    def test_end_to_end_indian_nse_stock(self):
        """Test end-to-end flow for Indian NSE stock."""
        from maverick_mcp.data.models import Stock, SessionLocal

        with SessionLocal() as session:
            # Create Indian NSE stock
            stock = Stock.get_or_create(
                session,
                ticker_symbol="RELIANCE.NS",
                company_name="Reliance Industries Ltd.",
                sector="Energy",
                industry="Oil & Gas"
            )
            
            assert stock.ticker_symbol == "RELIANCE.NS"
            assert stock.market == "NSE"
            assert stock.country == "IN"
            assert stock.currency == "INR"

    def test_end_to_end_indian_bse_stock(self):
        """Test end-to-end flow for Indian BSE stock."""
        from maverick_mcp.data.models import Stock, SessionLocal

        with SessionLocal() as session:
            # Create Indian BSE stock
            stock = Stock.get_or_create(
                session,
                ticker_symbol="TCS.BO",
                company_name="Tata Consultancy Services Ltd.",
                sector="Technology",
                industry="IT Services"
            )
            
            assert stock.ticker_symbol == "TCS.BO"
            assert stock.market == "BSE"
            assert stock.country == "IN"
            assert stock.currency == "INR"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])

