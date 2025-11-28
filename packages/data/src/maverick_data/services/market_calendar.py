"""
Market Calendar Service.

Handles trading day calculations, market hours, and holiday detection
for different stock exchanges (US, Indian NSE/BSE).
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from typing import Any

import pandas as pd
import pandas_market_calendars as mcal
import pytz

logger = logging.getLogger(__name__)


# Market configurations
MARKET_CONFIGS = {
    "NYSE": {
        "calendar_name": "NYSE",
        "timezone": "America/New_York",
        "open": "09:30",
        "close": "16:00",
        "currency": "USD",
    },
    "NASDAQ": {
        "calendar_name": "NASDAQ",
        "timezone": "America/New_York",
        "open": "09:30",
        "close": "16:00",
        "currency": "USD",
    },
    "NSE": {
        "calendar_name": "NSE",
        "timezone": "Asia/Kolkata",
        "open": "09:15",
        "close": "15:30",
        "currency": "INR",
    },
    "BSE": {
        "calendar_name": "BSE",
        "timezone": "Asia/Kolkata",
        "open": "09:15",
        "close": "15:30",
        "currency": "INR",
    },
}


def get_market_from_symbol(symbol: str) -> str:
    """
    Determine market from symbol suffix.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Market identifier (NYSE, NSE, BSE)
    """
    symbol = symbol.upper()
    if symbol.endswith(".NS"):
        return "NSE"
    elif symbol.endswith(".BO"):
        return "BSE"
    return "NYSE"


class MarketCalendarService:
    """
    Service for market calendar operations.

    Implements IMarketCalendar interface to provide trading day calculations,
    market hours, and holiday detection for multiple exchanges.

    Features:
    - Multi-market support (US, Indian NSE/BSE)
    - Trading day detection
    - Market hours checking
    - Holiday awareness
    - Calendar caching
    """

    def __init__(self):
        """Initialize market calendar service."""
        # Cache for market calendars
        self._calendars: dict[str, Any] = {}

        # Initialize default NYSE calendar
        self._default_calendar = mcal.get_calendar("NYSE")

        logger.info("MarketCalendarService initialized")

    def _get_calendar(self, market: str = "NYSE"):
        """
        Get or create cached calendar for market.

        Args:
            market: Market identifier

        Returns:
            pandas_market_calendars calendar
        """
        market = market.upper()

        if market not in self._calendars:
            config = MARKET_CONFIGS.get(market, MARKET_CONFIGS["NYSE"])
            try:
                self._calendars[market] = mcal.get_calendar(config["calendar_name"])
            except Exception as e:
                logger.warning(f"Could not load calendar for {market}: {e}, using NYSE")
                self._calendars[market] = self._default_calendar

        return self._calendars[market]

    def _get_market_from_symbol(self, symbol: str | None) -> str:
        """Get market identifier from symbol."""
        if symbol:
            return get_market_from_symbol(symbol)
        return "NYSE"

    def is_trading_day(
        self,
        check_date: date | datetime | str,
        market: str = "NYSE",
    ) -> bool:
        """
        Check if date is a trading day.

        Args:
            check_date: Date to check
            market: Market identifier

        Returns:
            True if date is a trading day
        """
        if isinstance(check_date, str):
            check_date = pd.to_datetime(check_date)
        elif isinstance(check_date, date) and not isinstance(check_date, datetime):
            check_date = datetime.combine(check_date, time())

        calendar = self._get_calendar(market)
        schedule = calendar.schedule(start_date=check_date, end_date=check_date)
        return len(schedule) > 0

    def get_trading_days(
        self,
        start_date: date | datetime | str,
        end_date: date | datetime | str,
        market: str = "NYSE",
    ) -> list[date]:
        """
        Get list of trading days in range.

        Args:
            start_date: Range start date
            end_date: Range end date
            market: Market identifier

        Returns:
            List of trading days
        """
        # Convert to datetime
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)

        # Ensure start_date <= end_date
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        calendar = self._get_calendar(market)
        schedule = calendar.schedule(start_date=start_date, end_date=end_date)

        return [d.date() for d in schedule.index]

    def get_trading_days_index(
        self,
        start_date: date | datetime | str,
        end_date: date | datetime | str,
        market: str = "NYSE",
    ) -> pd.DatetimeIndex:
        """
        Get trading days as DatetimeIndex.

        Args:
            start_date: Range start date
            end_date: Range end date
            market: Market identifier

        Returns:
            DatetimeIndex of trading days (timezone-naive)
        """
        # Convert to datetime
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date).tz_localize(None)
        elif hasattr(start_date, "tz_localize"):
            start_date = start_date.tz_localize(None)

        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date).tz_localize(None)
        elif hasattr(end_date, "tz_localize"):
            end_date = end_date.tz_localize(None)

        # Ensure start_date <= end_date
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        calendar = self._get_calendar(market)
        schedule = calendar.schedule(start_date=start_date, end_date=end_date)

        # Return timezone-naive index
        return schedule.index.tz_localize(None)

    def get_next_trading_day(
        self,
        from_date: date | datetime | str,
        market: str = "NYSE",
    ) -> date:
        """
        Get next trading day after date.

        Args:
            from_date: Starting date
            market: Market identifier

        Returns:
            Next trading day
        """
        if isinstance(from_date, str):
            from_date = pd.to_datetime(from_date).date()
        elif isinstance(from_date, datetime):
            from_date = from_date.date()

        # Look ahead up to 10 days
        for i in range(1, 11):
            check_date = from_date + timedelta(days=i)
            if self.is_trading_day(check_date, market):
                return check_date

        # Fallback
        logger.warning(f"Could not find next trading day after {from_date}")
        return from_date + timedelta(days=1)

    def get_previous_trading_day(
        self,
        from_date: date | datetime | str,
        market: str = "NYSE",
    ) -> date:
        """
        Get previous trading day before date.

        Args:
            from_date: Starting date
            market: Market identifier

        Returns:
            Previous trading day
        """
        if isinstance(from_date, str):
            from_date = pd.to_datetime(from_date).date()
        elif isinstance(from_date, datetime):
            from_date = from_date.date()

        # Check if from_date is a trading day
        if self.is_trading_day(from_date, market):
            return from_date

        # Look back up to 10 days
        for i in range(1, 11):
            check_date = from_date - timedelta(days=i)
            if self.is_trading_day(check_date, market):
                return check_date

        # Fallback
        logger.warning(f"Could not find previous trading day before {from_date}")
        return from_date - timedelta(days=1)

    def get_last_trading_day(
        self,
        from_date: date | datetime | str,
        market: str = "NYSE",
    ) -> date:
        """
        Get last trading day on or before date.

        Alias for get_previous_trading_day.
        """
        return self.get_previous_trading_day(from_date, market)

    def is_market_open(
        self,
        check_time: datetime | None = None,
        market: str = "NYSE",
    ) -> bool:
        """
        Check if market is currently open.

        Args:
            check_time: Time to check (default: now)
            market: Market identifier

        Returns:
            True if market is open
        """
        config = MARKET_CONFIGS.get(market.upper(), MARKET_CONFIGS["NYSE"])
        tz = pytz.timezone(config["timezone"])

        # Get current time in market timezone
        if check_time is None:
            now = datetime.now(tz)
        else:
            if check_time.tzinfo is None:
                now = tz.localize(check_time)
            else:
                now = check_time.astimezone(tz)

        # Check if weekday
        if now.weekday() >= 5:  # Saturday=5, Sunday=6
            return False

        # Check if trading day
        if not self.is_trading_day(now.date(), market):
            return False

        # Get market hours
        calendar = self._get_calendar(market)
        schedule = calendar.schedule(start_date=now.date(), end_date=now.date())

        if len(schedule) == 0:
            return False

        market_open = schedule.iloc[0]["market_open"].to_pydatetime()
        market_close = schedule.iloc[0]["market_close"].to_pydatetime()

        return market_open <= now <= market_close

    def get_market_hours(
        self,
        market: str = "NYSE",
    ) -> dict[str, str]:
        """
        Get market trading hours.

        Args:
            market: Market identifier

        Returns:
            Dictionary with open, close, timezone
        """
        config = MARKET_CONFIGS.get(market.upper(), MARKET_CONFIGS["NYSE"])
        return {
            "open": config["open"],
            "close": config["close"],
            "timezone": config["timezone"],
        }

    def get_market_holidays(
        self,
        year: int,
        market: str = "NYSE",
    ) -> list[date]:
        """
        Get market holidays for a year.

        Args:
            year: Year to get holidays for
            market: Market identifier

        Returns:
            List of holiday dates
        """
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        # Get all days in year
        all_days = pd.date_range(start=start_date, end=end_date, freq="B")  # Business days

        # Get trading days
        trading_days = set(self.get_trading_days(start_date, end_date, market))

        # Holidays are business days that aren't trading days
        holidays = []
        for day in all_days:
            if day.date() not in trading_days:
                holidays.append(day.date())

        return holidays

    def count_trading_days(
        self,
        start_date: date | datetime | str,
        end_date: date | datetime | str,
        market: str = "NYSE",
    ) -> int:
        """
        Count trading days in range.

        Args:
            start_date: Range start date
            end_date: Range end date
            market: Market identifier

        Returns:
            Number of trading days
        """
        return len(self.get_trading_days(start_date, end_date, market))

    def is_trading_day_between(
        self,
        start_date: date | datetime,
        end_date: date | datetime,
        market: str = "NYSE",
    ) -> bool:
        """
        Check if there's a trading day between two dates.

        Args:
            start_date: Start date
            end_date: End date
            market: Market identifier

        Returns:
            True if there's a trading day between the dates
        """
        # Add one day to start since we're checking "between"
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        check_start = start_date + timedelta(days=1)

        if isinstance(end_date, datetime):
            end_date = end_date.date()

        if check_start > end_date:
            return False

        trading_days = self.get_trading_days(check_start, end_date, market)
        return len(trading_days) > 0

    def for_symbol(self, symbol: str) -> "MarketCalendarService":
        """
        Create a symbol-aware calendar helper.

        Args:
            symbol: Stock symbol

        Returns:
            Self (for method chaining with symbol context)
        """
        # This method is here for compatibility with existing code
        # The actual market detection happens in each method
        return self

    def get_market_config(self, market: str = "NYSE") -> dict[str, Any]:
        """
        Get full market configuration.

        Args:
            market: Market identifier

        Returns:
            Market configuration dictionary
        """
        return MARKET_CONFIGS.get(market.upper(), MARKET_CONFIGS["NYSE"])


__all__ = ["MarketCalendarService", "get_market_from_symbol", "MARKET_CONFIGS"]
