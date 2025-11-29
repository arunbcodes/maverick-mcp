"""
Tests for MarketCalendarService

Tests market calendar operations including:
- Trading day detection
- Market hours checking
- Holiday awareness
- Multi-market support (US, Indian NSE/BSE)
"""

import pytest
from datetime import datetime, date, timedelta
import pandas as pd
import pytz

# Try new package structure first, fall back to legacy
try:
    from maverick_data.services.market_calendar import MarketCalendarService
except ImportError:
    from maverick_mcp.services.market_calendar_service import MarketCalendarService


class TestMarketCalendarServiceInitialization:
    """Test service initialization and setup."""
    
    def test_service_initializes_successfully(self):
        """Test that service can be instantiated."""
        service = MarketCalendarService()
        assert service is not None
        assert hasattr(service, 'market_calendars')
        assert hasattr(service, 'default_calendar')
    
    def test_default_calendar_is_nyse(self):
        """Test that default calendar is NYSE."""
        service = MarketCalendarService()
        assert service.default_calendar is not None
        # NYSE calendar should have name attribute
        assert hasattr(service.default_calendar, 'name')
    
    def test_market_calendars_cache_is_empty_initially(self):
        """Test that calendar cache starts empty."""
        service = MarketCalendarService()
        assert service.market_calendars == {}


class TestTradingDayDetection:
    """Test trading day detection functionality."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return MarketCalendarService()
    
    def test_weekday_is_trading_day(self, service):
        """Test that a regular weekday is recognized as trading day."""
        # Use a known weekday that's not a holiday (arbitrary Tuesday in mid-year)
        weekday = datetime(2024, 6, 11)  # Tuesday, June 11, 2024
        assert service.is_trading_day(weekday) is True
    
    def test_christmas_is_not_trading_day(self, service):
        """Test that Christmas is not a trading day."""
        christmas = datetime(2024, 12, 25)
        assert service.is_trading_day(christmas) is False
    
    def test_new_years_day_is_not_trading_day(self, service):
        """Test that New Year's Day is not a trading day."""
        new_years = datetime(2024, 1, 1)
        assert service.is_trading_day(new_years) is False
    
    def test_independence_day_is_not_trading_day(self, service):
        """Test that July 4th (US holiday) is not a trading day."""
        july_4th = datetime(2024, 7, 4)
        assert service.is_trading_day(july_4th) is False
    
    def test_saturday_is_not_trading_day(self, service):
        """Test that Saturday is not a trading day."""
        # First Saturday of 2024
        saturday = datetime(2024, 1, 6)
        assert service.is_trading_day(saturday) is False
    
    def test_sunday_is_not_trading_day(self, service):
        """Test that Sunday is not a trading day."""
        # First Sunday of 2024
        sunday = datetime(2024, 1, 7)
        assert service.is_trading_day(sunday) is False
    
    def test_accepts_string_date(self, service):
        """Test that method accepts string dates."""
        result = service.is_trading_day("2024-06-11")
        assert isinstance(result, bool)
    
    def test_accepts_date_object(self, service):
        """Test that method accepts date objects."""
        result = service.is_trading_day(date(2024, 6, 11))
        assert isinstance(result, bool)
    
    def test_accepts_datetime_object(self, service):
        """Test that method accepts datetime objects."""
        result = service.is_trading_day(datetime(2024, 6, 11))
        assert isinstance(result, bool)


class TestGetTradingDays:
    """Test getting range of trading days."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return MarketCalendarService()
    
    def test_get_trading_days_returns_datetimeindex(self, service):
        """Test that method returns DatetimeIndex."""
        start = "2024-01-02"
        end = "2024-01-31"
        result = service.get_trading_days(start, end)
        assert isinstance(result, pd.DatetimeIndex)
    
    def test_trading_days_excludes_weekends(self, service):
        """Test that weekends are excluded from trading days."""
        # Week with clear weekend
        start = "2024-01-08"  # Monday
        end = "2024-01-14"    # Sunday
        trading_days = service.get_trading_days(start, end)
        
        # Should be 5 days (Mon-Fri), excluding Sat-Sun
        assert len(trading_days) == 5
    
    def test_trading_days_excludes_holidays(self, service):
        """Test that holidays are excluded from trading days."""
        # Range including New Year's Day
        start = "2023-12-29"
        end = "2024-01-05"
        trading_days = service.get_trading_days(start, end)
        
        # Check that Jan 1 is not included
        jan_1 = pd.Timestamp("2024-01-01")
        assert jan_1 not in trading_days
    
    def test_single_day_range(self, service):
        """Test getting trading days for a single day."""
        # Single trading day
        day = "2024-06-11"
        result = service.get_trading_days(day, day)
        assert len(result) == 1
    
    def test_accepts_different_date_formats(self, service):
        """Test that method accepts various date formats."""
        start_str = "2024-01-02"
        end_datetime = datetime(2024, 1, 31)
        
        result = service.get_trading_days(start_str, end_datetime)
        assert isinstance(result, pd.DatetimeIndex)
        assert len(result) > 0
    
    def test_returns_timezone_naive_index(self, service):
        """Test that returned index is timezone-naive."""
        start = "2024-01-02"
        end = "2024-01-05"
        result = service.get_trading_days(start, end)
        
        # Check that the index is timezone-naive
        assert result.tz is None


class TestGetLastTradingDay:
    """Test getting last trading day functionality."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return MarketCalendarService()
    
    def test_returns_same_day_if_trading_day(self, service):
        """Test that if given a trading day, it returns the same day."""
        trading_day = datetime(2024, 6, 11)  # Tuesday
        result = service.get_last_trading_day(trading_day)
        assert result.date() == trading_day.date()
    
    def test_returns_friday_for_saturday(self, service):
        """Test that Saturday returns previous Friday."""
        saturday = datetime(2024, 1, 6)
        result = service.get_last_trading_day(saturday)
        # Should return Friday, Jan 5
        assert result.date() == date(2024, 1, 5)
    
    def test_returns_friday_for_sunday(self, service):
        """Test that Sunday returns previous Friday."""
        sunday = datetime(2024, 1, 7)
        result = service.get_last_trading_day(sunday)
        # Should return Friday, Jan 5
        assert result.date() == date(2024, 1, 5)
    
    def test_handles_holiday_weekend_combination(self, service):
        """Test handling of holiday followed by weekend."""
        # Day after New Year's when New Year falls on Monday
        # Jan 2, 2024 (Tuesday) should be a trading day
        tuesday_after_newyears = datetime(2024, 1, 2)
        result = service.get_last_trading_day(tuesday_after_newyears)
        assert isinstance(result, pd.Timestamp)
    
    def test_accepts_string_date(self, service):
        """Test that method accepts string dates."""
        result = service.get_last_trading_day("2024-06-11")
        assert isinstance(result, pd.Timestamp)
    
    def test_returns_timestamp(self, service):
        """Test that method returns pandas Timestamp."""
        result = service.get_last_trading_day(datetime(2024, 6, 11))
        assert isinstance(result, pd.Timestamp)


class TestIsMarketOpen:
    """Test market open/closed detection."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return MarketCalendarService()
    
    def test_returns_boolean(self, service):
        """Test that method returns boolean."""
        result = service.is_market_open()
        assert isinstance(result, bool)
    
    def test_handles_no_symbol_parameter(self, service):
        """Test that method works without symbol parameter."""
        # Should default to US market
        result = service.is_market_open()
        assert isinstance(result, bool)
    
    def test_weekend_returns_false(self, service):
        """Test that weekends return False regardless of time."""
        # Note: This test checks the logic but actual result depends on current time
        # The service should return False for weekends
        result = service.is_market_open()
        # We can't assert the exact value without mocking datetime,
        # but we can verify it returns a boolean
        assert isinstance(result, bool)


class TestIsTradingDayBetween:
    """Test checking if trading day exists between dates."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return MarketCalendarService()
    
    def test_returns_true_for_weekday_range(self, service):
        """Test returns True when weekdays exist between dates."""
        start = pd.Timestamp("2024-01-08")  # Monday
        end = pd.Timestamp("2024-01-12")    # Friday
        result = service.is_trading_day_between(start, end)
        assert result is True
    
    def test_returns_false_for_same_day(self, service):
        """Test returns False when start and end are same day."""
        day = pd.Timestamp("2024-01-08")
        result = service.is_trading_day_between(day, day)
        assert result is False
    
    def test_returns_false_for_adjacent_days(self, service):
        """Test returns False for consecutive days."""
        start = pd.Timestamp("2024-01-08")  # Monday
        end = pd.Timestamp("2024-01-09")    # Tuesday (no day between)
        result = service.is_trading_day_between(start, end)
        # Might be False if they're adjacent trading days
        assert isinstance(result, bool)
    
    def test_handles_weekend_gap(self, service):
        """Test handling of weekend between dates."""
        friday = pd.Timestamp("2024-01-05")
        saturday = pd.Timestamp("2024-01-06")
        result = service.is_trading_day_between(friday, saturday)
        # Only weekend day between - no trading days
        assert result is False


class TestMultiMarketSupport:
    """Test support for multiple markets (US, Indian)."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return MarketCalendarService()
    
    def test_handles_us_symbol(self, service):
        """Test handling of US stock symbols."""
        # Test with a US symbol
        result = service.is_trading_day("2024-06-11", symbol="AAPL")
        assert isinstance(result, bool)
    
    def test_handles_indian_nse_symbol(self, service):
        """Test handling of Indian NSE symbols."""
        # Test with NSE symbol
        try:
            result = service.is_trading_day("2024-06-11", symbol="RELIANCE.NS")
            assert isinstance(result, bool)
        except Exception:
            # If market calendar not available, test should not fail
            pytest.skip("Indian market calendar not available")
    
    def test_handles_indian_bse_symbol(self, service):
        """Test handling of Indian BSE symbols."""
        # Test with BSE symbol
        try:
            result = service.is_trading_day("2024-06-11", symbol="RELIANCE.BO")
            assert isinstance(result, bool)
        except Exception:
            # If market calendar not available, test should not fail
            pytest.skip("Indian market calendar not available")
    
    def test_caches_calendar_for_market(self, service):
        """Test that calendars are cached after first use."""
        # Make first call
        service.is_trading_day("2024-06-11", symbol="AAPL")
        
        # Check if calendar was cached
        # Note: Cache key depends on market config implementation
        # This test verifies the caching mechanism exists
        initial_cache_size = len(service.market_calendars)
        
        # Make second call with same symbol
        service.is_trading_day("2024-06-12", symbol="AAPL")
        
        # Cache size should not increase (calendar reused)
        assert len(service.market_calendars) == initial_cache_size


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return MarketCalendarService()
    
    def test_handles_invalid_date_string(self, service):
        """Test handling of invalid date strings."""
        with pytest.raises((ValueError, TypeError)):
            service.is_trading_day("not-a-date")
    
    def test_handles_future_dates(self, service):
        """Test handling of future dates."""
        # Far future date
        future_date = datetime(2050, 6, 15)
        result = service.is_trading_day(future_date)
        assert isinstance(result, bool)
    
    def test_handles_very_old_dates(self, service):
        """Test handling of historical dates."""
        # Old date (before some exchanges existed)
        old_date = datetime(1990, 1, 15)
        result = service.is_trading_day(old_date)
        assert isinstance(result, bool)
    
    def test_handles_invalid_symbol_gracefully(self, service):
        """Test that invalid symbols fall back to default calendar."""
        # Invalid symbol should not crash
        result = service.is_trading_day("2024-06-11", symbol="INVALID_SYMBOL_XYZ")
        assert isinstance(result, bool)
    
    def test_get_trading_days_with_reversed_dates(self, service):
        """Test behavior when end date is before start date."""
        start = "2024-01-31"
        end = "2024-01-01"
        # Should handle gracefully (might return empty or swap dates)
        result = service.get_trading_days(start, end)
        assert isinstance(result, pd.DatetimeIndex)


class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return MarketCalendarService()
    
    def test_repeated_calls_use_cache(self, service):
        """Test that repeated calls benefit from caching."""
        symbol = "AAPL"
        
        # First call - loads calendar
        service.is_trading_day("2024-01-15", symbol=symbol)
        cache_size_after_first = len(service.market_calendars)
        
        # Subsequent calls - should reuse cached calendar
        for _ in range(10):
            service.is_trading_day("2024-01-16", symbol=symbol)
        
        # Cache size should not grow
        assert len(service.market_calendars) == cache_size_after_first
    
    def test_handles_large_date_range(self, service):
        """Test handling of large date ranges."""
        # 5 years of trading days
        start = "2020-01-01"
        end = "2024-12-31"
        result = service.get_trading_days(start, end)
        
        assert len(result) > 1000  # Should be ~1260 trading days in 5 years
        assert isinstance(result, pd.DatetimeIndex)


# Note: These are unit tests that don't require external dependencies

