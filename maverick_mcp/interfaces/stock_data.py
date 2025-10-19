"""
Stock data provider interfaces.

Defines protocols (interfaces) for stock data operations to enable
dependency inversion and multiple implementations.
"""

from datetime import date, datetime
from typing import Protocol, Optional, runtime_checkable

import pandas as pd
from sqlalchemy.orm import Session


@runtime_checkable
class IMarketCalendar(Protocol):
    """
    Interface for market calendar operations.
    
    Handles trading days, market hours, and holiday detection.
    """
    
    def is_trading_day(self, dt: datetime | date, symbol: Optional[str] = None) -> bool:
        """
        Check if a date is a trading day.
        
        Args:
            dt: Date to check
            symbol: Optional stock symbol to determine market
            
        Returns:
            True if it's a trading day
        """
        ...
    
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
            DatetimeIndex of trading days
        """
        ...
    
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
        """
        ...
    
    def is_market_open(self, symbol: Optional[str] = None) -> bool:
        """
        Check if the market is currently open.
        
        Args:
            symbol: Optional stock symbol to determine market
            
        Returns:
            True if market is open
        """
        ...


@runtime_checkable
class ICacheManager(Protocol):
    """
    Interface for cache management operations.
    
    Handles reading from and writing to cache (database or memory).
    """
    
    def get_cached_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve cached stock data.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Cached DataFrame or None if not found
        """
        ...
    
    def cache_data(
        self,
        symbol: str,
        data: pd.DataFrame
    ) -> None:
        """
        Store stock data in cache.
        
        Args:
            symbol: Stock ticker symbol
            data: DataFrame with stock data
        """
        ...
    
    def invalidate_cache(self, symbol: Optional[str] = None) -> None:
        """
        Invalidate cache for a symbol or all symbols.
        
        Args:
            symbol: Stock ticker symbol, or None for all
        """
        ...


@runtime_checkable
class IDataFetcher(Protocol):
    """
    Interface for fetching stock data from external sources.
    
    Handles communication with data providers (yfinance, APIs, etc.).
    """
    
    def fetch_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch stock price data.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            period: Alternative to dates (e.g., "1mo", "1y")
            interval: Data interval (1d, 1wk, 1mo)
            
        Returns:
            DataFrame with stock data
        """
        ...
    
    def fetch_stock_info(self, symbol: str) -> dict:
        """
        Fetch detailed stock information.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with stock metadata
        """
        ...
    
    def fetch_realtime_data(self, symbol: str) -> Optional[dict]:
        """
        Fetch real-time stock data.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with real-time data or None
        """
        ...


@runtime_checkable
class IScreeningProvider(Protocol):
    """
    Interface for stock screening operations.
    
    Handles recommendations based on technical analysis and patterns.
    """
    
    def get_maverick_recommendations(
        self,
        limit: int = 20,
        min_score: Optional[int] = None
    ) -> list[dict]:
        """
        Get Maverick bullish stock recommendations.
        
        Args:
            limit: Maximum number of recommendations
            min_score: Minimum combined score filter
            
        Returns:
            List of stock recommendations
        """
        ...
    
    def get_maverick_bear_recommendations(
        self,
        limit: int = 20,
        min_score: Optional[int] = None
    ) -> list[dict]:
        """
        Get Maverick bearish stock recommendations.
        
        Args:
            limit: Maximum number of recommendations
            min_score: Minimum score filter
            
        Returns:
            List of bear recommendations
        """
        ...
    
    def get_supply_demand_breakout_recommendations(
        self,
        limit: int = 20,
        min_momentum_score: Optional[float] = None
    ) -> list[dict]:
        """
        Get supply/demand breakout recommendations.
        
        Args:
            limit: Maximum number of recommendations
            min_momentum_score: Minimum momentum score filter
            
        Returns:
            List of breakout recommendations
        """
        ...
    
    def get_all_screening_recommendations(self) -> dict[str, list[dict]]:
        """
        Get all screening recommendations in one call.
        
        Returns:
            Dictionary with all screening types
        """
        ...


@runtime_checkable
class IStockDataProvider(Protocol):
    """
    Main interface for stock data provider.
    
    Orchestrates calendar, cache, fetching, and screening operations.
    This is the primary interface that clients should depend on.
    """
    
    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        interval: str = "1d",
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Get stock data with caching support.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            period: Alternative to dates (e.g., "1mo", "1y")
            interval: Data interval (1d, 1wk, 1mo)
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with stock data
        """
        ...
    
    async def get_stock_data_async(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        interval: str = "1d",
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Async version of get_stock_data.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            period: Alternative to dates
            interval: Data interval
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with stock data
        """
        ...
    
    def get_stock_info(self, symbol: str) -> dict:
        """
        Get detailed stock information.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with stock metadata
        """
        ...
    
    def get_realtime_data(self, symbol: str) -> Optional[dict]:
        """
        Get real-time stock data.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with real-time data or None
        """
        ...
    
    def get_all_realtime_data(self, symbols: list[str]) -> dict[str, dict]:
        """
        Get real-time data for multiple symbols.
        
        Args:
            symbols: List of stock ticker symbols
            
        Returns:
            Dictionary mapping symbols to their data
        """
        ...
    
    def is_market_open(self) -> bool:
        """
        Check if the market is currently open.
        
        Returns:
            True if market is open
        """
        ...


__all__ = [
    "IMarketCalendar",
    "ICacheManager",
    "IDataFetcher",
    "IScreeningProvider",
    "IStockDataProvider",
]

