"""
Market calendar interfaces.

This module defines abstract interfaces for market calendar operations.
"""

from datetime import date, datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class IMarketCalendar(Protocol):
    """
    Interface for market calendar operations.

    This interface defines the contract for checking trading days,
    market hours, and market status.

    Implemented by: maverick-data (MarketCalendarService)
    """

    def is_trading_day(
        self,
        check_date: date,
        market: str = "NYSE",
    ) -> bool:
        """
        Check if date is a trading day.

        Args:
            check_date: Date to check
            market: Market identifier ("NYSE", "NSE", "BSE")

        Returns:
            True if date is a trading day
        """
        ...

    def get_trading_days(
        self,
        start_date: date,
        end_date: date,
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
        ...

    def get_next_trading_day(
        self,
        from_date: date,
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
        ...

    def get_previous_trading_day(
        self,
        from_date: date,
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
        ...

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
        ...

    def get_market_hours(
        self,
        market: str = "NYSE",
    ) -> dict[str, str]:
        """
        Get market trading hours.

        Args:
            market: Market identifier

        Returns:
            Dictionary with:
            - open: Opening time (HH:MM)
            - close: Closing time (HH:MM)
            - timezone: Market timezone
        """
        ...

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
        ...

    def count_trading_days(
        self,
        start_date: date,
        end_date: date,
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
        ...
