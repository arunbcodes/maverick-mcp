"""
Market Calendar Service

Handles trading day calculations, market hours, and holiday detection
for different stock exchanges (US, Indian NSE/BSE).
"""

import logging
from datetime import date, datetime, timedelta, time
from typing import Optional

import pandas as pd
import pandas_market_calendars as mcal
import pytz

logger = logging.getLogger(__name__)


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
        # Cache for market calendars (avoid repeated loading)
        self.market_calendars: dict[str, any] = {}
        
        # Initialize default NYSE calendar for backward compatibility
        self.default_calendar = mcal.get_calendar("NYSE")
        
        logger.info("MarketCalendarService initialized")
    
    def _get_market_calendar(self, symbol: Optional[str] = None):
        """
        Get the appropriate market calendar for a symbol.
        
        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "RELIANCE.NS")
                   If None, returns default NYSE calendar
        
        Returns:
            pandas_market_calendars calendar instance
        """
        if symbol is None:
            return self.default_calendar
        
        try:
            from maverick_mcp.config.markets import get_market_config
            
            market_config = get_market_config(symbol)
            market_key = market_config.name
            
            # Cache calendar instances to avoid repeated initialization
            if market_key not in self.market_calendars:
                try:
                    self.market_calendars[market_key] = market_config.get_calendar()
                    logger.debug(f"Loaded {market_config.calendar_name} calendar for {symbol}")
                except Exception as e:
                    logger.warning(
                        f"Could not load calendar for {market_config.name}: {e}. "
                        f"Falling back to NYSE calendar."
                    )
                    self.market_calendars[market_key] = self.default_calendar
            
            return self.market_calendars[market_key]
            
        except Exception as e:
            logger.warning(f"Error determining market for {symbol}: {e}. Using default NYSE calendar.")
            return self.default_calendar
    
    def is_trading_day(self, dt: datetime | date | str, symbol: Optional[str] = None) -> bool:
        """
        Check if a date is a trading day.
        
        Args:
            dt: Date to check (datetime, date, or string)
            symbol: Optional stock symbol to determine market
            
        Returns:
            True if it's a trading day
            
        Example:
            >>> service = MarketCalendarService()
            >>> service.is_trading_day("2024-12-25")  # Christmas
            False
            >>> service.is_trading_day("2024-12-26")
            True
        """
        # Convert to datetime if needed
        if isinstance(dt, str):
            dt = pd.to_datetime(dt)
        elif isinstance(dt, date) and not isinstance(dt, datetime):
            dt = datetime.combine(dt, time())
        
        calendar = self._get_market_calendar(symbol)
        schedule = calendar.schedule(start_date=dt, end_date=dt)
        return len(schedule) > 0
    
    def get_trading_days(
        self,
        start_date: datetime | date | str,
        end_date: datetime | date | str,
        symbol: Optional[str] = None
    ) -> pd.DatetimeIndex:
        """
        Get all trading days between start and end dates.
        
        Args:
            start_date: Start date
            end_date: End date
            symbol: Optional stock symbol to determine market
            
        Returns:
            DatetimeIndex of trading days (timezone-naive)
            
        Example:
            >>> service = MarketCalendarService()
            >>> days = service.get_trading_days("2024-01-01", "2024-01-31")
            >>> len(days)  # Number of trading days in January 2024
            21
        """
        # Ensure dates are datetime objects (timezone-naive)
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date).tz_localize(None)
        else:
            start_date = pd.to_datetime(start_date).tz_localize(None)
        
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date).tz_localize(None)
        else:
            end_date = pd.to_datetime(end_date).tz_localize(None)
        
        # Get market-specific calendar
        calendar = self._get_market_calendar(symbol)
        
        # Get valid trading days from market calendar
        schedule = calendar.schedule(start_date=start_date, end_date=end_date)
        
        # Return timezone-naive index
        return schedule.index.tz_localize(None)
    
    def get_last_trading_day(
        self,
        dt: datetime | date | str,
        symbol: Optional[str] = None
    ) -> pd.Timestamp:
        """
        Get the last trading day on or before the given date.
        
        Args:
            dt: Date to check
            symbol: Optional stock symbol to determine market
            
        Returns:
            Last trading day as pd.Timestamp
            
        Example:
            >>> service = MarketCalendarService()
            >>> service.get_last_trading_day("2024-12-25")  # Christmas (holiday)
            Timestamp('2024-12-24 00:00:00')  # Previous trading day
        """
        # Convert to datetime if needed
        if isinstance(dt, str):
            dt = pd.to_datetime(dt)
        elif isinstance(dt, date) and not isinstance(dt, datetime):
            dt = pd.Timestamp(dt)
        
        # Check if the date itself is a trading day
        if self.is_trading_day(dt, symbol):
            return pd.Timestamp(dt)
        
        # Otherwise, find the previous trading day
        for i in range(1, 10):  # Look back up to 10 days
            check_date = dt - timedelta(days=i)
            if self.is_trading_day(check_date, symbol):
                return pd.Timestamp(check_date)
        
        # Fallback to the date itself if no trading day found
        logger.warning(f"Could not find trading day before {dt}, returning original date")
        return pd.Timestamp(dt)
    
    def is_market_open(self, symbol: Optional[str] = None) -> bool:
        """
        Check if the market is currently open.
        
        Args:
            symbol: Optional stock symbol to determine market
                   If None, checks US market (NYSE)
            
        Returns:
            True if market is open
            
        Example:
            >>> service = MarketCalendarService()
            >>> service.is_market_open()  # US market
            True  # If called during US market hours
        """
        try:
            # Get market configuration
            if symbol:
                from maverick_mcp.config.markets import get_market_config
                config = get_market_config(symbol)
                timezone = config.timezone
            else:
                # Default to US Eastern Time
                timezone = "US/Eastern"
            
            # Get current time in market timezone
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            
            # Check if it's a weekday
            if now.weekday() >= 5:  # Saturday=5, Sunday=6
                return False
            
            # Check if it's a trading day (not a holiday)
            if not self.is_trading_day(now.date(), symbol):
                return False
            
            # Get market hours
            calendar = self._get_market_calendar(symbol)
            schedule = calendar.schedule(start_date=now.date(), end_date=now.date())
            
            if len(schedule) == 0:
                return False
            
            market_open = schedule.iloc[0]['market_open'].to_pydatetime()
            market_close = schedule.iloc[0]['market_close'].to_pydatetime()
            
            # Check if current time is within market hours
            return market_open <= now <= market_close
            
        except Exception as e:
            logger.error(f"Error checking if market is open: {e}")
            # Fallback to simple weekday check
            now = datetime.now(pytz.timezone("US/Eastern"))
            if now.weekday() >= 5:
                return False
            
            market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
            return market_open <= now <= market_close
    
    def is_trading_day_between(
        self,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
        symbol: Optional[str] = None
    ) -> bool:
        """
        Check if there's a trading day between two dates.
        
        Args:
            start_date: Start date
            end_date: End date
            symbol: Optional stock symbol to determine market
            
        Returns:
            True if there's a trading day between the dates
        """
        # Add one day to start since we're checking "between"
        check_start = start_date + timedelta(days=1)
        
        if check_start > end_date:
            return False
        
        # Get trading days in the range
        trading_days = self.get_trading_days(check_start, end_date, symbol)
        return len(trading_days) > 0


__all__ = ["MarketCalendarService"]

