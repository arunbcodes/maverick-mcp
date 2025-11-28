"""
Yahoo Finance Stock Data Provider.

Implements stock data fetching using yfinance library.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from functools import partial
from typing import Any

import pandas as pd
import yfinance as yf

from maverick_data.providers.base import BaseStockProvider

logger = logging.getLogger(__name__)


class YFinanceProvider(BaseStockProvider):
    """
    Stock data provider using Yahoo Finance (yfinance).

    This provider implements the IStockDataFetcher interface using
    yfinance as the data source. Supports historical data, real-time
    quotes, and stock information.

    Features:
    - Async wrappers around yfinance sync calls
    - Connection pooling for better performance
    - Multi-ticker batch downloads
    - ETF detection
    - News and recommendations
    """

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize yfinance provider.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self._ticker_cache: dict[str, yf.Ticker] = {}
        logger.info("YFinanceProvider initialized")

    def _get_ticker(self, symbol: str) -> yf.Ticker:
        """Get or create cached ticker object."""
        symbol = symbol.upper()
        if symbol not in self._ticker_cache:
            self._ticker_cache[symbol] = yf.Ticker(symbol)
        return self._ticker_cache[symbol]

    async def _run_sync(self, func, *args, **kwargs):
        """Run synchronous function in executor."""
        loop = asyncio.get_event_loop()
        partial_func = partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, partial_func)

    async def get_stock_data(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        period: str | None = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Fetch historical stock data from yfinance.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            period: Alternative to dates (e.g., "1mo", "1y")
            interval: Data interval (1d, 1wk, 1mo, etc.)

        Returns:
            DataFrame with OHLCV data indexed by date
        """
        symbol = symbol.upper()
        logger.debug(f"Fetching data for {symbol}: {start_date} to {end_date}, period={period}")

        try:
            ticker = self._get_ticker(symbol)

            # Build history parameters
            params: dict[str, Any] = {"interval": interval}
            if period:
                params["period"] = period
            else:
                if start_date:
                    params["start"] = start_date
                if end_date:
                    params["end"] = end_date
                if not start_date and not end_date:
                    params["period"] = "1y"

            # Fetch data async
            df = await self._run_sync(ticker.history, **params)

            if df.empty:
                logger.warning(f"Empty dataframe for {symbol}")
                return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

            # Ensure required columns exist
            required_cols = ["Open", "High", "Low", "Close", "Volume"]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = 0 if col == "Volume" else 0.0

            # Normalize index to timezone-naive
            df.index = pd.to_datetime(df.index).tz_localize(None)
            df.index.name = "Date"

            logger.debug(f"Fetched {len(df)} records for {symbol}")
            return df[required_cols]

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

    async def get_stock_info(self, symbol: str) -> dict[str, Any]:
        """
        Fetch detailed stock information from yfinance.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with company info, financials, etc.
        """
        symbol = symbol.upper()
        logger.debug(f"Fetching info for {symbol}")

        try:
            ticker = self._get_ticker(symbol)
            info = await self._run_sync(lambda: ticker.info)

            if not info:
                return {"symbol": symbol, "error": "No info available"}

            # Extract relevant fields
            return {
                "symbol": symbol,
                "name": info.get("shortName", info.get("longName", symbol)),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "avg_volume": info.get("averageVolume"),
                "description": info.get("longBusinessSummary"),
                "currency": info.get("currency", "USD"),
                "exchange": info.get("exchange"),
                "quote_type": info.get("quoteType"),
                "previous_close": info.get("previousClose"),
                "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
            }

        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}

    async def get_realtime_quote(self, symbol: str) -> dict[str, Any] | None:
        """
        Fetch real-time quote for a stock.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with current price data or None
        """
        symbol = symbol.upper()

        try:
            ticker = self._get_ticker(symbol)

            # Get latest data
            df = await self._run_sync(ticker.history, period="1d")
            if df.empty:
                return None

            latest = df.iloc[-1]

            # Get previous close for change calculation
            info = await self._run_sync(lambda: ticker.info)
            prev_close = info.get("previousClose")
            if prev_close is None:
                # Fallback to 2-day history
                df_2d = await self._run_sync(ticker.history, period="2d")
                if len(df_2d) > 1:
                    prev_close = df_2d.iloc[0]["Close"]
                else:
                    prev_close = latest["Close"]

            price = latest["Close"]
            change = price - prev_close
            change_percent = (change / prev_close * 100) if prev_close else 0

            return {
                "symbol": symbol,
                "price": round(float(price), 2),
                "change": round(float(change), 2),
                "change_percent": round(float(change_percent), 2),
                "volume": int(latest["Volume"]),
                "timestamp": df.index[-1].isoformat(),
                "is_realtime": False,  # yfinance has delay
            }

        except Exception as e:
            logger.error(f"Error fetching realtime quote for {symbol}: {e}")
            return None

    async def get_multiple_stocks_data(
        self,
        symbols: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stocks efficiently using batch download.

        Args:
            symbols: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dictionary mapping symbol to DataFrame
        """
        if not symbols:
            return {}

        symbols = [s.upper() for s in symbols]
        tickers_str = " ".join(symbols)

        try:
            # Use yfinance batch download
            params: dict[str, Any] = {
                "tickers": tickers_str,
                "group_by": "ticker",
                "threads": True,
                "progress": False,
            }

            if start_date:
                params["start"] = start_date
            if end_date:
                params["end"] = end_date
            else:
                params["period"] = "1y"

            data = await self._run_sync(yf.download, **params)

            if data.empty:
                return {}

            results = {}

            # Handle single vs multiple ticker response
            if len(symbols) == 1:
                # Single ticker - data is not grouped
                df = data[["Open", "High", "Low", "Close", "Volume"]].copy()
                df.index = pd.to_datetime(df.index).tz_localize(None)
                results[symbols[0]] = df
            else:
                # Multiple tickers - data is grouped
                for symbol in symbols:
                    try:
                        if symbol in data.columns.get_level_values(0):
                            df = data[symbol][["Open", "High", "Low", "Close", "Volume"]].copy()
                            df = df.dropna(how="all")
                            if not df.empty:
                                df.index = pd.to_datetime(df.index).tz_localize(None)
                                results[symbol] = df
                    except Exception as e:
                        logger.debug(f"Error processing {symbol}: {e}")

            logger.info(f"Batch fetched data for {len(results)}/{len(symbols)} symbols")
            return results

        except Exception as e:
            logger.error(f"Error in batch download: {e}")
            # Fallback to sequential fetching
            return await super().get_multiple_stocks_data(symbols, start_date, end_date)

    async def get_news(self, symbol: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Fetch news for a stock.

        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of articles

        Returns:
            List of news articles
        """
        symbol = symbol.upper()

        try:
            ticker = self._get_ticker(symbol)
            news = await self._run_sync(lambda: ticker.news)

            if not news:
                return []

            results = []
            for article in news[:limit]:
                results.append({
                    "title": article.get("title"),
                    "publisher": article.get("publisher"),
                    "link": article.get("link"),
                    "published": datetime.fromtimestamp(
                        article.get("providerPublishTime", 0), tz=UTC
                    ).isoformat() if article.get("providerPublishTime") else None,
                    "type": article.get("type"),
                })

            return results

        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []

    async def get_recommendations(self, symbol: str) -> list[dict[str, Any]]:
        """
        Fetch analyst recommendations.

        Args:
            symbol: Stock ticker symbol

        Returns:
            List of recommendations
        """
        symbol = symbol.upper()

        try:
            ticker = self._get_ticker(symbol)
            recs = await self._run_sync(lambda: ticker.recommendations)

            if recs is None or recs.empty:
                return []

            results = []
            for idx, row in recs.iterrows():
                results.append({
                    "date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx),
                    "firm": row.get("Firm"),
                    "to_grade": row.get("To Grade"),
                    "from_grade": row.get("From Grade"),
                    "action": row.get("Action"),
                })

            return results

        except Exception as e:
            logger.error(f"Error fetching recommendations for {symbol}: {e}")
            return []

    async def get_earnings(self, symbol: str) -> dict[str, Any]:
        """
        Fetch earnings information.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with earnings data
        """
        symbol = symbol.upper()

        try:
            ticker = self._get_ticker(symbol)

            earnings = await self._run_sync(lambda: getattr(ticker, "earnings", None))
            earnings_dates = await self._run_sync(lambda: getattr(ticker, "earnings_dates", None))

            return {
                "earnings": earnings.to_dict() if earnings is not None and not earnings.empty else {},
                "earnings_dates": earnings_dates.to_dict() if earnings_dates is not None and not earnings_dates.empty else {},
            }

        except Exception as e:
            logger.error(f"Error fetching earnings for {symbol}: {e}")
            return {"earnings": {}, "earnings_dates": {}}

    async def is_etf(self, symbol: str) -> bool:
        """
        Check if symbol is an ETF.

        Args:
            symbol: Stock ticker symbol

        Returns:
            True if symbol is an ETF
        """
        symbol = symbol.upper()

        # Quick check for common ETFs
        common_etfs = {
            "SPY", "QQQ", "IWM", "DIA", "XLB", "XLE", "XLF", "XLI", "XLK",
            "XLP", "XLU", "XLV", "XLY", "XLC", "XLRE", "XME", "VTI", "VOO",
            "VEA", "VWO", "BND", "AGG", "TLT", "GLD", "SLV", "USO", "UNG",
        }
        if symbol in common_etfs:
            return True

        try:
            info = await self.get_stock_info(symbol)
            quote_type = info.get("quote_type", "")
            return quote_type.upper() == "ETF"
        except Exception:
            return False

    def clear_cache(self, symbol: str | None = None) -> None:
        """
        Clear ticker cache.

        Args:
            symbol: Specific symbol to clear, or None to clear all
        """
        if symbol:
            self._ticker_cache.pop(symbol.upper(), None)
        else:
            self._ticker_cache.clear()


__all__ = ["YFinanceProvider"]
