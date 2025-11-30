"""
Cryptocurrency Data Provider using yfinance.

Primary data provider for cryptocurrency OHLCV data.
Uses yfinance which supports major cryptocurrencies via -USD suffix.

Features:
    - Dynamic symbol normalization (BTC -> BTC-USD)
    - Async interface for consistency with other providers
    - Technical indicator integration via pandas-ta
    - Compatible with maverick backtesting infrastructure
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class CryptoDataProvider:
    """
    Cryptocurrency data provider using Yahoo Finance.
    
    Provides OHLCV data for cryptocurrencies traded against USD.
    Uses the same interface pattern as stock providers for consistency.
    
    Supported symbols:
        - Major coins: BTC, ETH, BNB, SOL, XRP, DOGE, ADA, etc.
        - Any symbol available on Yahoo Finance with -USD suffix
    
    Example:
        >>> provider = CryptoDataProvider()
        >>> btc_data = await provider.get_crypto_data("BTC", days=90)
        >>> print(btc_data.tail())
    
    Note:
        Cryptocurrency markets operate 24/7, so there are no market hours
        or trading day restrictions. All calendar days have data.
    """
    
    # Common alternative suffixes to normalize
    KNOWN_SUFFIXES = ("-USD", "-USDT", "-BUSD", "-BTC", "-ETH", ".NS", ".BO")
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize the crypto data provider.
        
        Args:
            max_workers: Maximum thread pool workers for parallel fetching
        """
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        logger.info("CryptoDataProvider initialized")
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Convert any crypto symbol to yfinance format.
        
        Handles various input formats:
            - "BTC" -> "BTC-USD"
            - "btc" -> "BTC-USD"
            - "BTC-USD" -> "BTC-USD" (unchanged)
            - "BTCUSDT" -> "BTC-USD"
            - "BTC.NS" -> "BTC-USD" (removes stock suffixes)
        
        Args:
            symbol: Input symbol in any format
            
        Returns:
            Normalized symbol in yfinance format (e.g., "BTC-USD")
        """
        symbol = symbol.upper().strip()
        
        # Already in correct format
        if symbol.endswith("-USD"):
            return symbol
        
        # Remove known suffixes
        for suffix in self.KNOWN_SUFFIXES:
            if symbol.endswith(suffix):
                symbol = symbol[:-len(suffix)]
                break
        
        # Handle BTCUSDT, ETHUSDT format
        if symbol.endswith("USDT") or symbol.endswith("BUSD"):
            symbol = symbol[:-4]
        
        return f"{symbol}-USD"
    
    def is_crypto_symbol(self, symbol: str) -> bool:
        """
        Check if a symbol appears to be a cryptocurrency.
        
        Args:
            symbol: Symbol to check
            
        Returns:
            True if symbol looks like a crypto symbol
        """
        symbol = symbol.upper()
        # Check for crypto-specific patterns
        if any(symbol.endswith(suffix) for suffix in ("-USD", "-USDT", "-BUSD", "-BTC", "-ETH")):
            return True
        # Check for common crypto symbols
        common_cryptos = {"BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "AVAX", "DOT", "MATIC"}
        base_symbol = symbol.split("-")[0]
        return base_symbol in common_cryptos
    
    async def get_crypto_data(
        self,
        symbol: str,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        days: int | None = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Fetch historical cryptocurrency OHLCV data.
        
        Args:
            symbol: Crypto symbol (e.g., "BTC", "ETH", "BTC-USD")
            start_date: Start date (YYYY-MM-DD string or date object)
            end_date: End date (YYYY-MM-DD string or date object)
            days: Alternative to dates - fetch last N days
            interval: Data interval (1d, 1h, 1wk, 1mo)
            
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
            Index: DatetimeIndex
            
        Raises:
            ValueError: If symbol is invalid or no data available
        """
        yf_symbol = self.normalize_symbol(symbol)
        logger.info(f"Fetching crypto data for {yf_symbol}")
        
        # Calculate date range
        if days is not None:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
        elif start_date is None:
            # Default to 1 year
            end_date = date.today()
            start_date = end_date - timedelta(days=365)
        
        # Convert dates to strings if needed
        if isinstance(start_date, date):
            start_date = start_date.isoformat()
        if isinstance(end_date, date):
            end_date = end_date.isoformat()
        
        # Fetch data in thread pool (yfinance is sync)
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            self._executor,
            self._fetch_data_sync,
            yf_symbol,
            start_date,
            end_date,
            interval,
        )
        
        if df.empty:
            logger.warning(f"No data returned for {yf_symbol}")
            raise ValueError(f"No data available for symbol: {symbol}")
        
        logger.info(f"Fetched {len(df)} rows for {yf_symbol}")
        return df
    
    def _fetch_data_sync(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str,
    ) -> pd.DataFrame:
        """
        Synchronous data fetch (runs in thread pool).
        
        Args:
            symbol: yfinance symbol (e.g., "BTC-USD")
            start_date: Start date string
            end_date: End date string
            interval: Data interval
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
            )
            
            # Standardize column names
            df.columns = [col.capitalize() for col in df.columns]
            
            # Keep only OHLCV columns
            ohlcv_cols = ["Open", "High", "Low", "Close", "Volume"]
            available_cols = [col for col in ohlcv_cols if col in df.columns]
            df = df[available_cols]
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    async def get_crypto_info(self, symbol: str) -> dict[str, Any]:
        """
        Fetch detailed cryptocurrency information.
        
        Args:
            symbol: Crypto symbol
            
        Returns:
            Dictionary with crypto information
        """
        yf_symbol = self.normalize_symbol(symbol)
        
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            self._executor,
            self._fetch_info_sync,
            yf_symbol,
        )
        
        return info
    
    def _fetch_info_sync(self, symbol: str) -> dict[str, Any]:
        """Synchronous info fetch."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                "symbol": symbol,
                "name": info.get("shortName", info.get("longName", symbol)),
                "currency": info.get("currency", "USD"),
                "market_cap": info.get("marketCap"),
                "volume": info.get("volume"),
                "circulating_supply": info.get("circulatingSupply"),
                "total_supply": info.get("totalSupply"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "price": info.get("regularMarketPrice", info.get("previousClose")),
            }
        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}
    
    async def get_realtime_price(self, symbol: str) -> dict[str, Any] | None:
        """
        Fetch current price for a cryptocurrency.
        
        Args:
            symbol: Crypto symbol
            
        Returns:
            Dictionary with current price data or None
        """
        yf_symbol = self.normalize_symbol(symbol)
        
        loop = asyncio.get_event_loop()
        price_data = await loop.run_in_executor(
            self._executor,
            self._fetch_price_sync,
            yf_symbol,
        )
        
        return price_data
    
    def _fetch_price_sync(self, symbol: str) -> dict[str, Any] | None:
        """Synchronous price fetch."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            price = info.get("regularMarketPrice") or info.get("previousClose")
            if price is None:
                return None
            
            return {
                "symbol": symbol,
                "price": price,
                "change": info.get("regularMarketChange"),
                "change_percent": info.get("regularMarketChangePercent"),
                "volume": info.get("regularMarketVolume"),
                "market_cap": info.get("marketCap"),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    async def get_multiple_cryptos(
        self,
        symbols: list[str],
        days: int = 90,
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch data for multiple cryptocurrencies.
        
        Args:
            symbols: List of crypto symbols
            days: Number of days of history
            
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        results = {}
        
        # Fetch concurrently
        tasks = [
            self.get_crypto_data(symbol, days=days)
            for symbol in symbols
        ]
        
        fetched = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, data in zip(symbols, fetched):
            if isinstance(data, Exception):
                logger.warning(f"Failed to fetch {symbol}: {data}")
                continue
            if not data.empty:
                results[symbol] = data
        
        return results
    
    def __del__(self):
        """Cleanup thread pool on deletion."""
        self._executor.shutdown(wait=False)

