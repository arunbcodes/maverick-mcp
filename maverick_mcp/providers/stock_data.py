"""
Enhanced Stock Data Provider - Refactored with Composition

This is a facade that orchestrates four specialized services:
- MarketCalendarService: Trading day calculations
- StockCacheManager: Database caching
- StockDataFetcher: External data fetching
- ScreeningService: Stock recommendations

Maintains backward compatibility with the original EnhancedStockDataProvider.
"""

# Suppress specific pyright warnings for pandas operations
# pyright: reportOperatorIssue=false

import logging
from datetime import UTC, datetime, timedelta
from typing import Optional

import pandas as pd
import pytz
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import Session

from maverick_mcp.data.models import SessionLocal
from maverick_mcp.data.session_management import get_db_session_read_only
from maverick_mcp.services import (
    MarketCalendarService,
    StockCacheManager,
    StockDataFetcher,
    ScreeningService,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("maverick_mcp.stock_data")


class EnhancedStockDataProvider:
    """
    Enhanced provider for stock data using composition pattern.
    
    This class acts as a facade that orchestrates four specialized services:
    - MarketCalendarService: Handles trading days and market hours
    - StockCacheManager: Manages database caching
    - StockDataFetcher: Fetches data from external sources (yfinance)
    - ScreeningService: Provides stock recommendations
    
    Supports multi-market functionality for US, Indian NSE, and Indian BSE stocks.
    Maintains complete backward compatibility with the original implementation.
    """

    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize the stock data provider with composition.

        Args:
            db_session: Optional database session for dependency injection.
                       If not provided, services will create sessions as needed.
        """
        self._db_session = db_session
        
        # Initialize composed services
        self.calendar = MarketCalendarService()
        self.cache = StockCacheManager(db_session)
        self.fetcher = StockDataFetcher()
        self.screening = ScreeningService(db_session)
        
        # Legacy attributes for backward compatibility
        self.timeout = 30
        self.max_retries = 3
        self.cache_days = 1
        self.market_calendar = self.calendar.default_calendar
        
        # Test database connection
        if db_session:
            self._test_db_connection_with_session(db_session)
        else:
            self._test_db_connection()
        
        logger.info("EnhancedStockDataProvider initialized (refactored with composition)")
    
    # Database connection testing
    
    def _test_db_connection(self):
        """Test database connection on initialization."""
        try:
            with get_db_session_read_only() as session:
                result = session.execute(text("SELECT 1"))
                result.fetchone()
                logger.info("Database connection successful")
        except Exception as e:
            logger.warning(
                f"Database connection test failed: {e}. Caching will be disabled."
            )
    
    def _test_db_connection_with_session(self, session: Session):
        """Test provided database session."""
        try:
            result = session.execute(text("SELECT 1"))
            result.fetchone()
            logger.info("Database session test successful")
        except Exception as e:
            logger.warning(
                f"Database session test failed: {e}. Caching may not work properly."
            )
    
    # Core stock data methods
    
    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        interval: str = "1d",
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch stock data with intelligent caching.

        Orchestrates caching and fetching:
        1. Check cache for existing data
        2. Identify missing date ranges
        3. Fetch only missing data
        4. Combine and cache results

        Args:
            symbol: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            period: Alternative to start/end dates (e.g., '1d', '5d', '1mo', '1y')
            interval: Data interval ('1d', '1wk', '1mo', '1m', '5m', etc.)
            use_cache: Whether to use cached data if available

        Returns:
            DataFrame with stock data
        """
        # For non-daily intervals or periods, always fetch fresh data
        if interval != "1d" or period:
            return self.fetcher.fetch_stock_data(
                symbol, start_date, end_date, period, interval
            )
        
        # Set default dates if not provided
        if start_date is None:
            start_date = (datetime.now(UTC) - timedelta(days=365)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now(UTC).strftime("%Y-%m-%d")
        
        # For daily data, adjust end date to last trading day if needed
        if interval == "1d" and use_cache:
            end_dt = pd.to_datetime(end_date)
            if not self.calendar.is_trading_day(end_dt, symbol):
                last_trading = self.calendar.get_last_trading_day(end_dt, symbol)
                logger.debug(
                    f"Adjusting end date from {end_date} to last trading day "
                    f"{last_trading.strftime('%Y-%m-%d')} for {symbol}"
                )
                end_date = last_trading.strftime("%Y-%m-%d")
        
        # If cache is disabled, fetch directly
        if not use_cache:
            logger.info(f"Cache disabled, fetching from yfinance for {symbol}")
            return self.fetcher.fetch_stock_data(
                symbol, start_date, end_date, period, interval
            )
        
        # Try smart caching approach
        try:
            return self._get_data_with_smart_cache(
                symbol, start_date, end_date, interval
            )
        except Exception as e:
            logger.warning(f"Smart cache failed, falling back to yfinance: {e}")
            return self.fetcher.fetch_stock_data(
                symbol, start_date, end_date, period, interval
            )
    
    def _get_data_with_smart_cache(
        self, symbol: str, start_date: str, end_date: str, interval: str
    ) -> pd.DataFrame:
        """
        Get stock data using smart caching strategy.

        This method:
        1. Gets all available data from cache
        2. Identifies missing date ranges
        3. Fetches only missing data from yfinance
        4. Combines and returns the complete dataset

        Args:
            symbol: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval (only '1d' is cached)

        Returns:
            DataFrame with complete stock data
        """
        symbol = symbol.upper()
        
        # Step 1: Get ALL available cached data for the date range
        logger.info(f"Checking cache for {symbol} from {start_date} to {end_date}")
        cached_df = self.cache.get_cached_data(symbol, start_date, end_date)
        
        # Convert dates for comparison - ensure timezone-naive for consistency
        start_dt = pd.to_datetime(start_date).tz_localize(None)
        end_dt = pd.to_datetime(end_date).tz_localize(None)
        
        # Step 2: Determine what data we need
        if cached_df is not None and not cached_df.empty:
            logger.info(f"Found {len(cached_df)} cached records for {symbol}")
            
            # Check if we have all the data we need
            cached_start = pd.to_datetime(cached_df.index.min()).tz_localize(None)
            cached_end = pd.to_datetime(cached_df.index.max()).tz_localize(None)
            
            # Identify missing ranges
            missing_ranges = []
            
            # Missing data at the beginning?
            if start_dt < cached_start:
                missing_start_trading = self.calendar.get_trading_days(
                    start_dt, cached_start - timedelta(days=1), symbol
                )
                if len(missing_start_trading) > 0:
                    missing_ranges.append(
                        (
                            missing_start_trading[0].strftime("%Y-%m-%d"),
                            missing_start_trading[-1].strftime("%Y-%m-%d"),
                        )
                    )
            
            # Missing recent data?
            if end_dt > cached_end:
                if self.calendar.is_trading_day_between(cached_end, end_dt, symbol):
                    missing_end_trading = self.calendar.get_trading_days(
                        cached_end + timedelta(days=1), end_dt, symbol
                    )
                    if len(missing_end_trading) > 0:
                        missing_ranges.append(
                            (
                                missing_end_trading[0].strftime("%Y-%m-%d"),
                                missing_end_trading[-1].strftime("%Y-%m-%d"),
                            )
                        )
            
            # If no missing data, return cached data
            if not missing_ranges:
                logger.info(
                    f"Cache hit! Returning {len(cached_df)} cached records for {symbol}"
                )
                cached_df.index = pd.to_datetime(cached_df.index).tz_localize(None)
                mask = (cached_df.index >= start_dt) & (cached_df.index <= end_dt)
                return cached_df.loc[mask]
            
            # Step 3: Fetch only missing data
            logger.info(f"Cache partial hit. Missing ranges: {missing_ranges}")
            all_dfs = [cached_df]
            
            for miss_start, miss_end in missing_ranges:
                logger.info(
                    f"Fetching missing data for {symbol} from {miss_start} to {miss_end}"
                )
                missing_df = self.fetcher.fetch_stock_data(
                    symbol, miss_start, miss_end, None, interval
                )
                if not missing_df.empty:
                    all_dfs.append(missing_df)
                    # Cache the new data
                    self.cache.cache_data(symbol, missing_df)
            
            # Combine all data
            combined_df = pd.concat(all_dfs).sort_index()
            combined_df = combined_df[~combined_df.index.duplicated(keep="first")]
            
            # Filter to requested range
            combined_df.index = pd.to_datetime(combined_df.index).tz_localize(None)
            mask = (combined_df.index >= start_dt) & (combined_df.index <= end_dt)
            return combined_df.loc[mask]
        
        else:
            # No cached data, fetch everything for trading days only
            logger.info(
                f"No cached data found for {symbol}, fetching from yfinance"
            )
            
            # Adjust dates to trading days
            trading_days = self.calendar.get_trading_days(start_date, end_date, symbol)
            if len(trading_days) == 0:
                logger.warning(
                    f"No trading days found between {start_date} and {end_date}"
                )
                return pd.DataFrame(
                    columns=[  # type: ignore[arg-type]
                        "Open",
                        "High",
                        "Low",
                        "Close",
                        "Volume",
                        "Dividends",
                        "Stock Splits",
                    ]
                )
            
            # Fetch data only for the trading day range
            fetch_start = trading_days[0].strftime("%Y-%m-%d")
            fetch_end = trading_days[-1].strftime("%Y-%m-%d")
            
            logger.info(
                f"Fetching data for trading days: {fetch_start} to {fetch_end}"
            )
            df = self.fetcher.fetch_stock_data(
                symbol, fetch_start, fetch_end, None, interval
            )
            if not df.empty:
                # Cache the data
                self.cache.cache_data(symbol, df)
            return df
    
    async def get_stock_data_async(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        interval: str = "1d",
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Async version of get_stock_data for parallel processing.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            period: Alternative to start/end dates
            interval: Data interval
            use_cache: Whether to use cached data

        Returns:
            DataFrame with stock data
        """
        import asyncio
        import functools
        
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        
        sync_method = functools.partial(
            self.get_stock_data,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            period=period,
            interval=interval,
            use_cache=use_cache,
        )
        
        return await loop.run_in_executor(None, sync_method)
    
    # Delegate to StockDataFetcher
    
    def get_stock_info(self, symbol: str) -> dict:
        """Get detailed stock information."""
        return self.fetcher.fetch_stock_info(symbol)
    
    def get_realtime_data(self, symbol: str):
        """Get real-time stock data."""
        return self.fetcher.fetch_realtime_data(symbol)
    
    def get_all_realtime_data(self, symbols: list[str]):
        """Get real-time data for multiple symbols."""
        return self.fetcher.fetch_multiple_realtime(symbols)
    
    def get_news(self, symbol: str, limit: int = 10) -> pd.DataFrame:
        """Get news for a stock."""
        return self.fetcher.fetch_news(symbol, limit)
    
    def get_earnings(self, symbol: str) -> dict:
        """Get earnings information."""
        return self.fetcher.fetch_earnings(symbol)
    
    def get_recommendations(self, symbol: str) -> pd.DataFrame:
        """Get analyst recommendations."""
        return self.fetcher.fetch_recommendations(symbol)
    
    def is_etf(self, symbol: str) -> bool:
        """Check if a symbol is an ETF."""
        return self.fetcher.is_etf(symbol)
    
    # Delegate to ScreeningService
    
    def get_maverick_recommendations(
        self, limit: int = 20, min_score: Optional[int] = None
    ) -> list[dict]:
        """Get Maverick bullish stock recommendations."""
        return self.screening.get_maverick_recommendations(limit, min_score)
    
    def get_maverick_bear_recommendations(
        self, limit: int = 20, min_score: Optional[int] = None
    ) -> list[dict]:
        """Get Maverick bearish stock recommendations."""
        return self.screening.get_maverick_bear_recommendations(limit, min_score)
    
    def get_supply_demand_breakout_recommendations(
        self, limit: int = 20, min_momentum_score: Optional[float] = None
    ) -> list[dict]:
        """Get supply/demand breakout recommendations."""
        return self.screening.get_supply_demand_breakout_recommendations(
            limit, min_momentum_score
        )
    
    def get_all_screening_recommendations(self) -> dict[str, list[dict]]:
        """Get all screening recommendations in one call."""
        return self.screening.get_all_screening_recommendations()
    
    # Delegate to MarketCalendarService
    
    def is_market_open(self) -> bool:
        """Check if the US stock market is currently open."""
        return self.calendar.is_market_open()
    
    # Backward compatibility helpers (these delegate to services)
    
    def _is_trading_day(self, date, symbol: Optional[str] = None) -> bool:
        """Check if a date is a trading day."""
        return self.calendar.is_trading_day(date, symbol)
    
    def _get_trading_days(
        self, start_date, end_date, symbol: Optional[str] = None
    ) -> pd.DatetimeIndex:
        """Get trading days between dates."""
        return self.calendar.get_trading_days(start_date, end_date, symbol)
    
    def _get_last_trading_day(self, date, symbol: Optional[str] = None) -> pd.Timestamp:
        """Get last trading day."""
        return self.calendar.get_last_trading_day(date, symbol)
    
    def _get_market_calendar(self, symbol: Optional[str] = None):
        """Get market calendar."""
        return self.calendar._get_market_calendar(symbol)


# Maintain backward compatibility
StockDataProvider = EnhancedStockDataProvider

