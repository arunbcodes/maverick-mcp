"""
Base Provider Interface.

Defines the abstract base for all stock data providers.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class BaseStockProvider(ABC):
    """
    Abstract base class for stock data providers.

    This class defines the contract that all stock data providers
    must implement, allowing for easy swapping between data sources.
    """

    @abstractmethod
    async def get_stock_data(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        period: str | None = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Fetch historical stock data.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            period: Alternative to dates (e.g., "1mo", "1y")
            interval: Data interval (1d, 1wk, 1mo, etc.)

        Returns:
            DataFrame with OHLCV data indexed by date
        """
        ...

    @abstractmethod
    async def get_stock_info(self, symbol: str) -> dict[str, Any]:
        """
        Fetch detailed stock information.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with company info, sector, etc.
        """
        ...

    @abstractmethod
    async def get_realtime_quote(self, symbol: str) -> dict[str, Any] | None:
        """
        Fetch real-time stock quote.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with current price data or None
        """
        ...

    async def get_multiple_stocks_data(
        self,
        symbols: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stocks.

        Default implementation fetches sequentially. Override for
        parallel fetching in subclasses.

        Args:
            symbols: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dictionary mapping symbol to DataFrame
        """
        results = {}
        for symbol in symbols:
            try:
                df = await self.get_stock_data(symbol, start_date, end_date)
                if not df.empty:
                    results[symbol] = df
            except Exception as e:
                logger.warning(f"Failed to fetch data for {symbol}: {e}")
        return results

    async def is_market_open(self, market: str = "NYSE") -> bool:
        """
        Check if market is currently open.

        Args:
            market: Market identifier

        Returns:
            True if market is open
        """
        # Default implementation - subclasses can override
        return False


__all__ = ["BaseStockProvider"]
