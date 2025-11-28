"""Tests for maverick-data services."""

from datetime import date, datetime

import pytest

from maverick_data.services import MarketCalendarService
from maverick_data.services.market_calendar import get_market_from_symbol, MARKET_CONFIGS


class TestServiceImports:
    """Test that service components can be imported."""

    def test_market_calendar_service_import(self):
        """Test MarketCalendarService import."""
        assert MarketCalendarService is not None

    def test_get_market_from_symbol_import(self):
        """Test get_market_from_symbol import."""
        assert get_market_from_symbol is not None

    def test_market_configs_import(self):
        """Test MARKET_CONFIGS import."""
        assert MARKET_CONFIGS is not None
        assert isinstance(MARKET_CONFIGS, dict)


class TestGetMarketFromSymbol:
    """Test market detection from symbols."""

    def test_us_stock(self):
        """Test US stock detection."""
        assert get_market_from_symbol("AAPL") == "NYSE"
        assert get_market_from_symbol("MSFT") == "NYSE"
        assert get_market_from_symbol("GOOGL") == "NYSE"

    def test_nse_stock(self):
        """Test NSE stock detection."""
        assert get_market_from_symbol("RELIANCE.NS") == "NSE"
        assert get_market_from_symbol("TCS.NS") == "NSE"
        assert get_market_from_symbol("INFY.NS") == "NSE"

    def test_bse_stock(self):
        """Test BSE stock detection."""
        assert get_market_from_symbol("RELIANCE.BO") == "BSE"
        assert get_market_from_symbol("TCS.BO") == "BSE"
        assert get_market_from_symbol("INFY.BO") == "BSE"

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert get_market_from_symbol("reliance.ns") == "NSE"
        assert get_market_from_symbol("RELIANCE.ns") == "NSE"


class TestMarketConfigs:
    """Test market configuration data."""

    def test_nyse_config(self):
        """Test NYSE configuration."""
        config = MARKET_CONFIGS["NYSE"]
        assert config["timezone"] == "America/New_York"
        assert config["open"] == "09:30"
        assert config["close"] == "16:00"
        assert config["currency"] == "USD"

    def test_nse_config(self):
        """Test NSE configuration."""
        config = MARKET_CONFIGS["NSE"]
        assert config["timezone"] == "Asia/Kolkata"
        assert config["open"] == "09:15"
        assert config["close"] == "15:30"
        assert config["currency"] == "INR"

    def test_bse_config(self):
        """Test BSE configuration."""
        config = MARKET_CONFIGS["BSE"]
        assert config["timezone"] == "Asia/Kolkata"
        assert config["currency"] == "INR"


class TestMarketCalendarService:
    """Test MarketCalendarService class."""

    def test_create_service(self):
        """Test creating market calendar service."""
        service = MarketCalendarService()
        assert service is not None

    def test_service_has_required_methods(self):
        """Test service has all required interface methods."""
        service = MarketCalendarService()

        # IMarketCalendar methods
        assert hasattr(service, "is_trading_day")
        assert hasattr(service, "get_trading_days")
        assert hasattr(service, "get_next_trading_day")
        assert hasattr(service, "get_previous_trading_day")
        assert hasattr(service, "is_market_open")
        assert hasattr(service, "get_market_hours")
        assert hasattr(service, "get_market_holidays")
        assert hasattr(service, "count_trading_days")

    def test_is_trading_day_weekday(self):
        """Test trading day detection for a weekday."""
        service = MarketCalendarService()
        # January 2, 2024 was a Tuesday
        result = service.is_trading_day("2024-01-02", "NYSE")
        assert isinstance(result, bool)

    def test_is_trading_day_weekend(self):
        """Test weekend is not a trading day."""
        service = MarketCalendarService()
        # January 6, 2024 was a Saturday
        result = service.is_trading_day("2024-01-06", "NYSE")
        assert result is False

    def test_get_trading_days_returns_list(self):
        """Test get_trading_days returns a list."""
        service = MarketCalendarService()
        days = service.get_trading_days("2024-01-01", "2024-01-31", "NYSE")
        assert isinstance(days, list)
        # January 2024 should have trading days
        assert len(days) > 0

    def test_get_market_hours(self):
        """Test getting market hours."""
        service = MarketCalendarService()
        hours = service.get_market_hours("NYSE")
        assert "open" in hours
        assert "close" in hours
        assert "timezone" in hours
        assert hours["open"] == "09:30"
        assert hours["close"] == "16:00"

    def test_get_market_hours_nse(self):
        """Test getting NSE market hours."""
        service = MarketCalendarService()
        hours = service.get_market_hours("NSE")
        assert hours["open"] == "09:15"
        assert hours["close"] == "15:30"
        assert hours["timezone"] == "Asia/Kolkata"

    def test_count_trading_days(self):
        """Test counting trading days."""
        service = MarketCalendarService()
        count = service.count_trading_days("2024-01-01", "2024-01-31", "NYSE")
        assert isinstance(count, int)
        # January 2024 should have ~21 trading days
        assert 19 <= count <= 23

    def test_get_next_trading_day(self):
        """Test getting next trading day."""
        service = MarketCalendarService()
        # After Friday Jan 5, 2024, next trading day should be Jan 8 (Monday)
        next_day = service.get_next_trading_day("2024-01-05", "NYSE")
        assert isinstance(next_day, date)

    def test_get_previous_trading_day(self):
        """Test getting previous trading day."""
        service = MarketCalendarService()
        # Before Monday Jan 8, 2024, previous trading day should be Jan 5 (Friday)
        prev_day = service.get_previous_trading_day("2024-01-08", "NYSE")
        assert isinstance(prev_day, date)

    def test_get_market_config(self):
        """Test getting full market configuration."""
        service = MarketCalendarService()
        config = service.get_market_config("NYSE")
        assert isinstance(config, dict)
        assert "timezone" in config
        assert "open" in config
        assert "close" in config
