"""
Stock Data Provider.

A facade provider that orchestrates data fetching, caching, and market calendar services.
Maintains backward compatibility with the legacy EnhancedStockDataProvider interface.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from functools import partial
from typing import TYPE_CHECKING, Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from maverick_data.cache import CacheManager, get_cache_manager
from maverick_data.models import (
    MaverickBearStocks,
    MaverickStocks,
    PriceCache,
    Stock,
    SupplyDemandBreakoutStocks,
)
from maverick_data.providers.yfinance_provider import YFinanceProvider
from maverick_data.services import MarketCalendarService, bulk_insert_price_data
from maverick_data.session import SessionLocal, get_session

if TYPE_CHECKING:
    pass

logger = logging.getLogger("maverick_data.providers.stock_data")


class StockDataProvider:
    """
    Stock data provider with caching and multi-market support.

    This class provides a unified interface for fetching stock data with:
    - Smart caching (database and memory)
    - Market calendar awareness
    - Screening recommendations
    - Multi-market support (US, Indian NSE/BSE)

    Maintains backward compatibility with the legacy EnhancedStockDataProvider.
    """

    def __init__(self, db_session: Session | None = None):
        """
        Initialize stock data provider.

        Args:
            db_session: Optional database session for dependency injection.
        """
        self._db_session = db_session
        self._yfinance = YFinanceProvider()
        self._calendar = MarketCalendarService()
        self._cache_manager: CacheManager | None = None

        # Legacy attributes for backward compatibility
        self.timeout = 30
        self.max_retries = 3
        self.cache_days = 1
        self.market_calendar = self._calendar.default_calendar

        # Test database connection
        if db_session:
            self._test_db_connection_with_session(db_session)
        else:
            self._test_db_connection()

        logger.info("StockDataProvider initialized")

    def _get_session(self) -> Session:
        """Get database session."""
        if self._db_session:
            return self._db_session
        return get_session()

    def _test_db_connection(self) -> None:
        """Test database connection on initialization."""
        try:
            session = self._get_session()
            result = session.execute(text("SELECT 1"))
            result.fetchone()
            session.close()
            logger.info("Database connection successful")
        except Exception as e:
            logger.warning(f"Database connection test failed: {e}. Caching disabled.")

    def _test_db_connection_with_session(self, session: Session) -> None:
        """Test provided database session."""
        try:
            result = session.execute(text("SELECT 1"))
            result.fetchone()
            logger.info("Database session test successful")
        except Exception as e:
            logger.warning(f"Database session test failed: {e}")

    # =========================================================================
    # Core Stock Data Methods
    # =========================================================================

    def get_stock_data(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        period: str | None = None,
        interval: str = "1d",
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch stock data with intelligent caching.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            period: Alternative to dates (e.g., "1mo", "1y")
            interval: Data interval (1d, 1wk, etc.)
            use_cache: Whether to use cached data

        Returns:
            DataFrame with OHLCV data
        """
        symbol = symbol.upper()

        # For non-daily intervals or periods, fetch fresh
        if interval != "1d" or period:
            return asyncio.run(
                self._yfinance.get_stock_data(symbol, start_date, end_date, period, interval)
            )

        # Set default dates
        if start_date is None:
            start_date = (datetime.now(UTC) - timedelta(days=365)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now(UTC).strftime("%Y-%m-%d")

        # Adjust end date to last trading day
        if interval == "1d" and use_cache:
            end_dt = pd.to_datetime(end_date)
            if not self._calendar.is_trading_day(end_dt, symbol):
                last_trading = self._calendar.get_last_trading_day(end_dt, symbol)
                end_date = last_trading.strftime("%Y-%m-%d")

        # Try cache first
        if use_cache:
            try:
                return self._get_data_with_cache(symbol, start_date, end_date, interval)
            except Exception as e:
                logger.warning(f"Cache lookup failed: {e}")

        # Fetch fresh data
        return asyncio.run(
            self._yfinance.get_stock_data(symbol, start_date, end_date, None, interval)
        )

    def _get_data_with_cache(
        self, symbol: str, start_date: str, end_date: str, interval: str
    ) -> pd.DataFrame:
        """Get stock data with database caching."""
        symbol = symbol.upper()
        session = self._get_session()

        try:
            # Check cache
            stock = session.query(Stock).filter(Stock.ticker_symbol == symbol).first()

            if stock:
                cached_df = self._get_cached_data(session, stock.stock_id, start_date, end_date)
                if cached_df is not None and not cached_df.empty:
                    logger.info(f"Cache hit for {symbol}: {len(cached_df)} records")
                    return cached_df

            # Fetch from yfinance
            df = asyncio.run(
                self._yfinance.get_stock_data(symbol, start_date, end_date, None, interval)
            )

            # Cache the data
            if not df.empty:
                try:
                    bulk_insert_price_data(session, symbol, df)
                except Exception as e:
                    logger.warning(f"Failed to cache data: {e}")

            return df

        finally:
            if not self._db_session:
                session.close()

    def _get_cached_data(
        self, session: Session, stock_id: int, start_date: str, end_date: str
    ) -> pd.DataFrame | None:
        """Get cached price data from database."""
        try:
            start_dt = pd.to_datetime(start_date).date()
            end_dt = pd.to_datetime(end_date).date()

            records = (
                session.query(PriceCache)
                .filter(
                    PriceCache.stock_id == stock_id,
                    PriceCache.date >= start_dt,
                    PriceCache.date <= end_dt,
                )
                .order_by(PriceCache.date)
                .all()
            )

            if not records:
                return None

            data = []
            for r in records:
                data.append({
                    "Date": r.date,
                    "Open": float(r.open_price),
                    "High": float(r.high_price),
                    "Low": float(r.low_price),
                    "Close": float(r.close_price),
                    "Volume": r.volume,
                })

            df = pd.DataFrame(data)
            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)
            return df

        except Exception as e:
            logger.error(f"Error getting cached data: {e}")
            return None

    async def get_stock_data_async(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        period: str | None = None,
        interval: str = "1d",
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """Async version of get_stock_data."""
        loop = asyncio.get_event_loop()
        sync_method = partial(
            self.get_stock_data,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            period=period,
            interval=interval,
            use_cache=use_cache,
        )
        return await loop.run_in_executor(None, sync_method)

    # =========================================================================
    # Stock Info Methods (delegated to YFinance)
    # =========================================================================

    def get_stock_info(self, symbol: str) -> dict[str, Any]:
        """Get detailed stock information."""
        return asyncio.run(self._yfinance.get_stock_info(symbol))

    def get_realtime_data(self, symbol: str) -> dict[str, Any] | None:
        """Get real-time stock data."""
        return asyncio.run(self._yfinance.get_realtime_quote(symbol))

    def get_all_realtime_data(self, symbols: list[str]) -> dict[str, dict]:
        """Get real-time data for multiple symbols."""
        results = {}
        for symbol in symbols:
            quote = asyncio.run(self._yfinance.get_realtime_quote(symbol))
            if quote:
                results[symbol] = quote
        return results

    def get_news(self, symbol: str, limit: int = 10) -> pd.DataFrame:
        """Get news for a stock."""
        news = asyncio.run(self._yfinance.get_news(symbol, limit))
        return pd.DataFrame(news)

    def get_earnings(self, symbol: str) -> dict[str, Any]:
        """Get earnings information."""
        return asyncio.run(self._yfinance.get_earnings(symbol))

    def get_recommendations(self, symbol: str) -> pd.DataFrame:
        """Get analyst recommendations."""
        recs = asyncio.run(self._yfinance.get_recommendations(symbol))
        return pd.DataFrame(recs)

    def is_etf(self, symbol: str) -> bool:
        """Check if symbol is an ETF."""
        return asyncio.run(self._yfinance.is_etf(symbol))

    # =========================================================================
    # Screening Methods
    # =========================================================================

    def get_maverick_recommendations(
        self, limit: int = 20, min_score: int | None = None
    ) -> list[dict]:
        """Get Maverick bullish stock recommendations."""
        session = self._get_session()
        try:
            query = session.query(MaverickStocks).order_by(
                MaverickStocks.combined_score.desc()
            )
            if min_score:
                query = query.filter(MaverickStocks.combined_score >= min_score)
            results = query.limit(limit).all()
            return [r.to_dict() for r in results]
        finally:
            if not self._db_session:
                session.close()

    def get_maverick_bear_recommendations(
        self, limit: int = 20, min_score: int | None = None
    ) -> list[dict]:
        """Get Maverick bearish stock recommendations."""
        session = self._get_session()
        try:
            query = session.query(MaverickBearStocks).order_by(
                MaverickBearStocks.score.desc()
            )
            if min_score:
                query = query.filter(MaverickBearStocks.score >= min_score)
            results = query.limit(limit).all()
            return [r.to_dict() for r in results]
        finally:
            if not self._db_session:
                session.close()

    def get_supply_demand_breakout_recommendations(
        self, limit: int = 20, min_momentum_score: float | None = None
    ) -> list[dict]:
        """Get supply/demand breakout recommendations."""
        session = self._get_session()
        try:
            query = session.query(SupplyDemandBreakoutStocks).order_by(
                SupplyDemandBreakoutStocks.momentum_score.desc()
            )
            if min_momentum_score:
                query = query.filter(
                    SupplyDemandBreakoutStocks.momentum_score >= min_momentum_score
                )
            results = query.limit(limit).all()
            return [r.to_dict() for r in results]
        finally:
            if not self._db_session:
                session.close()

    def get_all_screening_recommendations(self) -> dict[str, list[dict]]:
        """Get all screening recommendations in one call."""
        return {
            "maverick_stocks": self.get_maverick_recommendations(),
            "maverick_bear_stocks": self.get_maverick_bear_recommendations(),
            "supply_demand_breakouts": self.get_supply_demand_breakout_recommendations(),
        }

    # =========================================================================
    # Market Calendar Methods
    # =========================================================================

    def is_market_open(self) -> bool:
        """Check if the stock market is currently open."""
        return self._calendar.is_market_open()

    def _is_trading_day(self, date, symbol: str | None = None) -> bool:
        """Check if a date is a trading day."""
        return self._calendar.is_trading_day(date, symbol)

    def _get_trading_days(
        self, start_date, end_date, symbol: str | None = None
    ) -> pd.DatetimeIndex:
        """Get trading days between dates."""
        return self._calendar.get_trading_days(start_date, end_date, symbol)

    def _get_last_trading_day(self, date, symbol: str | None = None) -> pd.Timestamp:
        """Get last trading day."""
        return self._calendar.get_last_trading_day(date, symbol)


# Backward compatibility alias
EnhancedStockDataProvider = StockDataProvider

__all__ = ["StockDataProvider", "EnhancedStockDataProvider"]

