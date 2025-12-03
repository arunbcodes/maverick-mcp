"""
Stock data service.

Provides stock quotes, historical data, and company information.
Used by both MCP server and REST API.
"""

from datetime import date, datetime, UTC
from decimal import Decimal
from typing import Protocol

import pandas as pd

from maverick_schemas.stock import (
    StockQuote,
    StockInfo,
    StockHistory,
    OHLCV,
    BatchQuoteResponse,
)
from maverick_schemas.base import Market
from maverick_services.exceptions import StockNotFoundError, InsufficientDataError


class StockDataProvider(Protocol):
    """Protocol for stock data providers."""

    async def get_stock_data(
        self,
        ticker: str,
        start_date: str | None = None,
        end_date: str | None = None,
        period: str | None = None,
    ) -> pd.DataFrame:
        """Fetch stock data."""
        ...

    async def get_stock_info(self, ticker: str) -> dict:
        """Fetch stock information."""
        ...


class CacheProvider(Protocol):
    """Protocol for cache providers."""

    async def get(self, key: str) -> dict | None:
        """Get cached value."""
        ...

    async def set(self, key: str, value: dict, ttl: int | None = None) -> None:
        """Set cached value."""
        ...


def _to_decimal(value: float | int | None) -> Decimal | None:
    """Convert to Decimal, handling None."""
    if value is None:
        return None
    return Decimal(str(value))


def _detect_market(ticker: str) -> Market:
    """Detect market from ticker suffix."""
    ticker_upper = ticker.upper()
    if ticker_upper.endswith(".NS"):
        return Market.NSE
    elif ticker_upper.endswith(".BO"):
        return Market.BSE
    return Market.US


class StockService:
    """
    Domain service for stock operations.

    Used by both MCP routers and REST API routers.
    All business logic for stock data lives here.
    """

    def __init__(
        self,
        provider: StockDataProvider,
        cache: CacheProvider | None = None,
    ):
        """
        Initialize stock service.

        Args:
            provider: Stock data provider (e.g., YFinanceProvider)
            cache: Optional cache provider for caching quotes
        """
        self._provider = provider
        self._cache = cache

    async def get_quote(self, ticker: str) -> StockQuote:
        """
        Get real-time quote for a stock.

        Args:
            ticker: Stock ticker symbol

        Returns:
            StockQuote with current price and change

        Raises:
            StockNotFoundError: If ticker not found
        """
        # Check cache first
        if self._cache:
            cached = await self._cache.get(f"quote:{ticker.upper()}")
            if cached:
                return StockQuote.model_validate(cached)

        # Fetch from provider
        df = await self._provider.get_stock_data(ticker, period="5d")

        if df is None or df.empty:
            raise StockNotFoundError(ticker)

        latest = df.iloc[-1]
        prev_close = df.iloc[-2]["Close"] if len(df) > 1 else latest["Close"]
        change = float(latest["Close"]) - float(prev_close)
        change_percent = (change / float(prev_close)) * 100 if prev_close else 0

        quote = StockQuote(
            ticker=ticker.upper(),
            price=_to_decimal(latest["Close"]),
            change=_to_decimal(change),
            change_percent=_to_decimal(change_percent),
            volume=int(latest["Volume"]),
            timestamp=datetime.now(UTC),
            open=_to_decimal(latest.get("Open")),
            high=_to_decimal(latest.get("High")),
            low=_to_decimal(latest.get("Low")),
            previous_close=_to_decimal(prev_close),
        )

        # Cache the quote
        if self._cache:
            await self._cache.set(
                f"quote:{ticker.upper()}",
                quote.model_dump(mode="json"),
                ttl=60,  # 1 minute TTL for quotes
            )

        return quote

    async def get_history(
        self,
        ticker: str,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        interval: str = "1d",
    ) -> StockHistory:
        """
        Get historical OHLCV data for a stock.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD or date object)
            end_date: End date (YYYY-MM-DD or date object)
            interval: Data interval (1d, 1wk, 1mo)

        Returns:
            StockHistory with OHLCV data

        Raises:
            StockNotFoundError: If ticker not found
            InsufficientDataError: If no data in range
        """
        # Convert dates to strings if needed
        start_str = str(start_date) if start_date else None
        end_str = str(end_date) if end_date else None

        df = await self._provider.get_stock_data(
            ticker,
            start_date=start_str,
            end_date=end_str,
        )

        if df is None or df.empty:
            raise StockNotFoundError(ticker)

        # Convert DataFrame to OHLCV list
        ohlcv_data = []
        for idx, row in df.iterrows():
            ohlcv = OHLCV(
                date=idx.date() if hasattr(idx, "date") else idx,
                open=_to_decimal(row["Open"]),
                high=_to_decimal(row["High"]),
                low=_to_decimal(row["Low"]),
                close=_to_decimal(row["Close"]),
                volume=int(row["Volume"]),
                adj_close=_to_decimal(row.get("Adj Close")),
            )
            ohlcv_data.append(ohlcv)

        return StockHistory(
            ticker=ticker.upper(),
            data=ohlcv_data,
            start_date=ohlcv_data[0].date,
            end_date=ohlcv_data[-1].date,
            data_points=len(ohlcv_data),
            interval=interval,
        )

    async def get_info(self, ticker: str) -> StockInfo:
        """
        Get company information for a stock.

        Args:
            ticker: Stock ticker symbol

        Returns:
            StockInfo with company details

        Raises:
            StockNotFoundError: If ticker not found
        """
        info = await self._provider.get_stock_info(ticker)

        if not info:
            raise StockNotFoundError(ticker)

        return StockInfo(
            ticker=ticker.upper(),
            name=info.get("longName") or info.get("shortName") or ticker,
            market=_detect_market(ticker),
            sector=info.get("sector"),
            industry=info.get("industry"),
            market_cap=_to_decimal(info.get("marketCap")),
            pe_ratio=_to_decimal(info.get("trailingPE")),
            forward_pe=_to_decimal(info.get("forwardPE")),
            peg_ratio=_to_decimal(info.get("pegRatio")),
            price_to_book=_to_decimal(info.get("priceToBook")),
            dividend_yield=_to_decimal(info.get("dividendYield")),
            dividend_rate=_to_decimal(info.get("dividendRate")),
            avg_volume=info.get("averageVolume"),
            fifty_two_week_high=_to_decimal(info.get("fiftyTwoWeekHigh")),
            fifty_two_week_low=_to_decimal(info.get("fiftyTwoWeekLow")),
            description=info.get("longBusinessSummary"),
            website=info.get("website"),
            employees=info.get("fullTimeEmployees"),
        )

    async def get_batch_quotes(self, tickers: list[str]) -> BatchQuoteResponse:
        """
        Get quotes for multiple stocks.

        Args:
            tickers: List of ticker symbols

        Returns:
            BatchQuoteResponse with quotes and any errors
        """
        quotes = {}
        errors = {}

        for ticker in tickers:
            try:
                quote = await self.get_quote(ticker)
                quotes[ticker.upper()] = quote
            except StockNotFoundError:
                errors[ticker.upper()] = f"Stock not found: {ticker}"
            except Exception as e:
                errors[ticker.upper()] = str(e)

        return BatchQuoteResponse(quotes=quotes, errors=errors)


__all__ = ["StockService"]

