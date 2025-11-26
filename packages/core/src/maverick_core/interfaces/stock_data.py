"""
Stock data provider interfaces.

This module defines abstract interfaces for stock data fetching and screening operations.
These interfaces separate concerns between basic data retrieval and advanced screening logic,
following the Interface Segregation Principle.
"""

from typing import Any, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class IStockDataFetcher(Protocol):
    """
    Interface for fetching basic stock data.

    This interface defines the contract for retrieving historical price data,
    real-time quotes, company information, and related financial data.

    Implemented by: maverick-data (StockDataProvider, EnhancedStockDataProvider)
    """

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
            symbol: Stock ticker symbol (e.g., "AAPL", "RELIANCE.NS")
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            period: Alternative to start/end dates (e.g., '1y', '6mo')
            interval: Data interval ('1d', '1wk', '1mo', etc.)

        Returns:
            DataFrame with OHLCV data indexed by date.
            Columns: Open, High, Low, Close, Volume

        Raises:
            StockDataError: If data cannot be fetched
        """
        ...

    async def get_realtime_quote(self, symbol: str) -> dict[str, Any] | None:
        """
        Get real-time stock quote.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with current price, change, volume, etc.
            Returns None if quote unavailable.

            Expected keys:
            - price: Current price
            - change: Price change
            - change_percent: Percentage change
            - volume: Trading volume
            - timestamp: Quote timestamp
        """
        ...

    async def get_stock_info(self, symbol: str) -> dict[str, Any]:
        """
        Get detailed stock information and fundamentals.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with company info, financials, and market data.

            Expected keys:
            - name: Company name
            - sector: Business sector
            - industry: Industry classification
            - market_cap: Market capitalization
            - pe_ratio: Price-to-earnings ratio
            - dividend_yield: Dividend yield percentage
            - description: Company description
        """
        ...

    async def get_multiple_stocks_data(
        self,
        symbols: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stocks efficiently.

        Args:
            symbols: List of stock tickers
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary mapping symbol to DataFrame
        """
        ...

    async def is_market_open(self, market: str = "NYSE") -> bool:
        """
        Check if the stock market is currently open.

        Args:
            market: Market identifier ("NYSE", "NSE", "BSE")

        Returns:
            True if market is open, False otherwise
        """
        ...


@runtime_checkable
class IStockScreener(Protocol):
    """
    Interface for stock screening and recommendation operations.

    This interface defines the contract for generating stock recommendations
    based on various technical and fundamental criteria.

    Implemented by: maverick-data (ScreeningService)
    """

    async def get_maverick_recommendations(
        self,
        limit: int = 20,
        min_score: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get bullish Maverick stock recommendations.

        Args:
            limit: Maximum number of recommendations
            min_score: Minimum combined score filter

        Returns:
            List of stock recommendations with technical analysis.

            Each recommendation contains:
            - symbol: Stock ticker
            - score: Combined score
            - momentum_score: Momentum indicator
            - trend_strength: Trend strength
            - support_level: Support price
            - resistance_level: Resistance price
        """
        ...

    async def get_maverick_bear_recommendations(
        self,
        limit: int = 20,
        min_score: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get bearish Maverick stock recommendations.

        Args:
            limit: Maximum number of recommendations
            min_score: Minimum score filter

        Returns:
            List of bear stock recommendations
        """
        ...

    async def get_supply_demand_breakouts(
        self,
        limit: int = 20,
        filter_above_ma: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Get stocks showing supply/demand breakout patterns.

        Args:
            limit: Maximum number of recommendations
            filter_above_ma: Only return stocks above moving averages

        Returns:
            List of breakout candidates
        """
        ...

    async def screen_by_criteria(
        self,
        min_momentum_score: float | None = None,
        min_volume: int | None = None,
        max_price: float | None = None,
        sector: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Screen stocks by custom criteria.

        Args:
            min_momentum_score: Minimum momentum score (0-100)
            min_volume: Minimum average daily volume
            max_price: Maximum stock price
            sector: Filter by sector
            limit: Maximum results

        Returns:
            List of matching stocks
        """
        ...

    async def get_all_screening_recommendations(
        self,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Get all screening recommendations in one call.

        Returns:
            Dictionary with all screening types and their recommendations.

            Keys:
            - maverick: Bullish recommendations
            - maverick_bear: Bearish recommendations
            - supply_demand: Breakout candidates
        """
        ...
