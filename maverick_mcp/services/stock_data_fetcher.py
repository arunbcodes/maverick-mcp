"""
Stock Data Fetcher Service

Handles fetching stock data from external sources (yfinance).
"""

import logging
from typing import Optional

import pandas as pd
import yfinance as yf

from maverick_mcp.utils.circuit_breaker_decorators import with_stock_data_circuit_breaker
from maverick_mcp.utils.yfinance_pool import get_yfinance_pool

logger = logging.getLogger(__name__)


class StockDataFetcher:
    """
    Service for fetching stock data from external sources.
    
    Implements IDataFetcher interface to provide data fetching
    from yfinance with circuit breaker protection and connection pooling.
    
    Features:
    - Connection pooling for performance
    - Circuit breaker for resilience
    - Real-time and historical data
    - Stock metadata fetching
    """
    
    def __init__(self):
        """Initialize stock data fetcher."""
        # Initialize yfinance connection pool
        self._yf_pool = get_yfinance_pool()
        logger.info("StockDataFetcher initialized")
    
    @with_stock_data_circuit_breaker(use_fallback=False)
    def fetch_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch stock price data from yfinance.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            period: Alternative to dates (e.g., "1mo", "1y")
            interval: Data interval (1d, 1wk, 1mo, 1m, 5m)
            
        Returns:
            DataFrame with stock data (OHLCV)
            
        Raises:
            CircuitBreakerError: If circuit breaker is open
        """
        logger.info(
            f"Fetching data from yfinance for {symbol} - "
            f"Start: {start_date}, End: {end_date}, Period: {period}, Interval: {interval}"
        )
        
        # Use the optimized connection pool
        df = self._yf_pool.get_history(
            symbol=symbol,
            start=start_date,
            end=end_date,
            period=period,
            interval=interval,
        )
        
        # Check if dataframe is empty or if required columns are missing
        if df.empty:
            logger.warning(f"Empty dataframe returned for {symbol}")
            return pd.DataFrame(
                columns=["Open", "High", "Low", "Close", "Volume"]  # type: ignore[arg-type]
            )
        
        # Ensure all expected columns exist
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col not in df.columns:
                logger.warning(
                    f"Column {col} missing from data for {symbol}, adding empty column"
                )
                # Use appropriate default values
                if col == "Volume":
                    df[col] = 0
                else:
                    df[col] = 0.0
        
        df.index.name = "Date"
        logger.debug(f"Fetched {len(df)} records for {symbol}")
        return df
    
    @with_stock_data_circuit_breaker(use_fallback=False)
    def fetch_stock_info(self, symbol: str) -> dict:
        """
        Fetch detailed stock information from yfinance.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with stock metadata (company name, sector, etc.)
            
        Raises:
            CircuitBreakerError: If circuit breaker is open
        """
        logger.debug(f"Fetching stock info for {symbol}")
        
        # Use connection pool for better performance
        info = self._yf_pool.get_info(symbol)
        
        logger.debug(f"Retrieved info for {symbol}")
        return info
    
    def fetch_realtime_data(self, symbol: str) -> Optional[dict]:
        """
        Fetch real-time stock data.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with real-time data or None if unavailable
        """
        try:
            # Use connection pool for real-time data
            data = self._yf_pool.get_history(symbol, period="1d")
            
            if data.empty:
                logger.warning(f"No real-time data available for {symbol}")
                return None
            
            latest = data.iloc[-1]
            
            # Get previous close for change calculation
            info = self._yf_pool.get_info(symbol)
            prev_close = info.get("previousClose", None)
            if prev_close is None:
                # Try to get from 2-day history
                data_2d = self._yf_pool.get_history(symbol, period="2d")
                if len(data_2d) > 1:
                    prev_close = data_2d.iloc[0]["Close"]
                else:
                    prev_close = latest["Close"]
            
            # Calculate change
            price = latest["Close"]
            change = price - prev_close
            change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
            
            result = {
                "symbol": symbol,
                "price": round(price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume": int(latest["Volume"]),
                "timestamp": data.index[-1],
                "timestamp_display": data.index[-1].strftime("%Y-%m-%d %H:%M:%S"),
                "is_real_time": False,  # yfinance data has some delay
            }
            
            logger.debug(f"Fetched realtime data for {symbol}: {result['price']}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching realtime data for {symbol}: {e}")
            return None
    
    def fetch_multiple_realtime(self, symbols: list[str]) -> dict[str, dict]:
        """
        Fetch real-time data for multiple symbols.
        
        Args:
            symbols: List of stock ticker symbols
            
        Returns:
            Dictionary mapping symbols to their real-time data
        """
        results = {}
        for symbol in symbols:
            data = self.fetch_realtime_data(symbol)
            if data:
                results[symbol] = data
        
        logger.info(f"Fetched realtime data for {len(results)}/{len(symbols)} symbols")
        return results
    
    def fetch_news(self, symbol: str, limit: int = 10) -> pd.DataFrame:
        """
        Fetch news for a stock from yfinance.
        
        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of news items
            
        Returns:
            DataFrame with news articles
        """
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return pd.DataFrame(
                    columns=[  # type: ignore[arg-type]
                        "title",
                        "publisher",
                        "link",
                        "providerPublishTime",
                        "type",
                    ]
                )
            
            df = pd.DataFrame(news[:limit])
            
            # Convert timestamp to datetime
            if "providerPublishTime" in df.columns:
                df["providerPublishTime"] = pd.to_datetime(
                    df["providerPublishTime"], unit="s"
                )
            
            logger.debug(f"Fetched {len(df)} news items for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return pd.DataFrame(
                columns=["title", "publisher", "link", "providerPublishTime", "type"]  # type: ignore[arg-type]
            )
    
    def fetch_earnings(self, symbol: str) -> dict:
        """
        Fetch earnings information for a stock.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with earnings data
        """
        try:
            ticker = yf.Ticker(symbol)
            result = {
                "earnings": ticker.earnings.to_dict()
                if hasattr(ticker, "earnings") and not ticker.earnings.empty
                else {},
                "earnings_dates": ticker.earnings_dates.to_dict()
                if hasattr(ticker, "earnings_dates") and not ticker.earnings_dates.empty
                else {},
                "earnings_trend": ticker.earnings_trend
                if hasattr(ticker, "earnings_trend")
                else {},
            }
            
            logger.debug(f"Fetched earnings data for {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching earnings for {symbol}: {e}")
            return {"earnings": {}, "earnings_dates": {}, "earnings_trend": {}}
    
    def fetch_recommendations(self, symbol: str) -> pd.DataFrame:
        """
        Fetch analyst recommendations for a stock.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            DataFrame with recommendations
        """
        try:
            ticker = yf.Ticker(symbol)
            recommendations = ticker.recommendations
            
            if recommendations is None or recommendations.empty:
                return pd.DataFrame(columns=["firm", "toGrade", "fromGrade", "action"])  # type: ignore[arg-type]
            
            logger.debug(f"Fetched {len(recommendations)} recommendations for {symbol}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error fetching recommendations for {symbol}: {e}")
            return pd.DataFrame(columns=["firm", "toGrade", "fromGrade", "action"])  # type: ignore[arg-type]
    
    def is_etf(self, symbol: str) -> bool:
        """
        Check if a symbol is an ETF.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            True if the symbol is an ETF
        """
        try:
            stock = yf.Ticker(symbol)
            # Check if quoteType exists and is ETF
            if "quoteType" in stock.info:
                return stock.info["quoteType"].upper() == "ETF"  # type: ignore[no-any-return]
            
            # Fallback check for common ETF identifiers
            return any(
                [
                    symbol.endswith(("ETF", "FUND")),
                    symbol
                    in [
                        "SPY",
                        "QQQ",
                        "IWM",
                        "DIA",
                        "XLB",
                        "XLE",
                        "XLF",
                        "XLI",
                        "XLK",
                        "XLP",
                        "XLU",
                        "XLV",
                        "XLY",
                        "XLC",
                        "XLRE",
                        "XME",
                    ],
                    "ETF" in stock.info.get("longName", "").upper(),
                ]
            )
        except Exception as e:
            logger.error(f"Error checking if {symbol} is ETF: {e}")
            return False


__all__ = ["StockDataFetcher"]

