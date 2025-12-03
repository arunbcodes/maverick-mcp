"""
Stock screening service.

Provides Maverick screening strategies and custom filters.
"""

from datetime import datetime, UTC
from decimal import Decimal
from typing import Protocol

import pandas as pd

from maverick_schemas.screening import (
    ScreeningStrategy,
    MaverickStock,
    ScreeningFilter,
    ScreeningResult,
    ScreeningResponse,
)
from maverick_schemas.base import Market, TrendDirection


class ScreeningRepository(Protocol):
    """Protocol for screening data access."""

    async def get_maverick_stocks(self, limit: int = 20) -> list[dict]:
        """Get cached Maverick bullish picks."""
        ...

    async def get_maverick_bear_stocks(self, limit: int = 20) -> list[dict]:
        """Get cached Maverick bearish picks."""
        ...

    async def get_breakout_stocks(self, limit: int = 20) -> list[dict]:
        """Get supply/demand breakout stocks."""
        ...


class StockDataProvider(Protocol):
    """Protocol for stock data."""

    async def get_stock_data(
        self,
        ticker: str,
        period: str = "1y",
    ) -> pd.DataFrame:
        """Fetch stock data."""
        ...


def _to_decimal(value: float | int | None) -> Decimal | None:
    """Convert to Decimal."""
    if value is None:
        return None
    if pd.isna(value):
        return None
    return Decimal(str(round(value, 4)))


def _detect_market(ticker: str) -> Market:
    """Detect market from ticker."""
    ticker_upper = ticker.upper()
    if ticker_upper.endswith(".NS"):
        return Market.NSE
    elif ticker_upper.endswith(".BO"):
        return Market.BSE
    return Market.US


class ScreeningService:
    """
    Domain service for stock screening.

    Provides Maverick screening strategies and custom filtering.
    """

    def __init__(
        self,
        repository: ScreeningRepository,
        provider: StockDataProvider | None = None,
    ):
        """
        Initialize screening service.

        Args:
            repository: Screening data repository
            provider: Optional stock data provider for live screening
        """
        self._repository = repository
        self._provider = provider

    async def get_maverick_stocks(
        self,
        limit: int = 20,
        filters: ScreeningFilter | None = None,
    ) -> list[MaverickStock]:
        """
        Get Maverick bullish stock picks.

        Args:
            limit: Maximum number of results
            filters: Optional additional filters

        Returns:
            List of MaverickStock picks
        """
        stocks_data = await self._repository.get_maverick_stocks(limit=limit * 2)

        stocks = []
        for data in stocks_data:
            stock = MaverickStock(
                ticker=data["ticker"],
                name=data.get("name"),
                market=_detect_market(data["ticker"]),
                maverick_score=_to_decimal(data.get("maverick_score", 0)),
                momentum_score=_to_decimal(data.get("momentum_score")),
                trend_score=_to_decimal(data.get("trend_score")),
                current_price=_to_decimal(data.get("current_price", 0)),
                change_percent=_to_decimal(data.get("change_percent")),
                rsi=_to_decimal(data.get("rsi")),
                trend=TrendDirection(data["trend"]) if data.get("trend") else None,
                above_sma_50=data.get("above_sma_50", False),
                above_sma_200=data.get("above_sma_200", False),
                relative_volume=_to_decimal(data.get("relative_volume")),
                pattern=data.get("pattern"),
                pattern_confidence=_to_decimal(data.get("pattern_confidence")),
                screened_at=datetime.now(UTC),
            )

            # Apply filters if provided
            if filters and not self._passes_filters(stock, filters):
                continue

            stocks.append(stock)

            if len(stocks) >= limit:
                break

        return stocks

    async def get_maverick_bear_stocks(
        self,
        limit: int = 20,
        filters: ScreeningFilter | None = None,
    ) -> list[MaverickStock]:
        """
        Get Maverick bearish stock picks.

        Args:
            limit: Maximum number of results
            filters: Optional additional filters

        Returns:
            List of MaverickStock bearish picks
        """
        stocks_data = await self._repository.get_maverick_bear_stocks(limit=limit * 2)

        stocks = []
        for data in stocks_data:
            stock = MaverickStock(
                ticker=data["ticker"],
                name=data.get("name"),
                market=_detect_market(data["ticker"]),
                maverick_score=_to_decimal(data.get("bear_score", 0)),
                momentum_score=_to_decimal(data.get("momentum_score")),
                current_price=_to_decimal(data.get("current_price", 0)),
                change_percent=_to_decimal(data.get("change_percent")),
                rsi=_to_decimal(data.get("rsi")),
                above_sma_50=data.get("above_sma_50", False),
                above_sma_200=data.get("above_sma_200", False),
                screened_at=datetime.now(UTC),
            )

            if filters and not self._passes_filters(stock, filters):
                continue

            stocks.append(stock)

            if len(stocks) >= limit:
                break

        return stocks

    async def get_breakout_stocks(
        self,
        limit: int = 20,
        filters: ScreeningFilter | None = None,
    ) -> list[MaverickStock]:
        """
        Get supply/demand breakout candidates.

        Args:
            limit: Maximum number of results
            filters: Optional additional filters

        Returns:
            List of MaverickStock breakout candidates
        """
        stocks_data = await self._repository.get_breakout_stocks(limit=limit * 2)

        stocks = []
        for data in stocks_data:
            stock = MaverickStock(
                ticker=data["ticker"],
                name=data.get("name"),
                market=_detect_market(data["ticker"]),
                maverick_score=_to_decimal(data.get("breakout_score", 0)),
                momentum_score=_to_decimal(data.get("momentum_score")),
                current_price=_to_decimal(data.get("current_price", 0)),
                change_percent=_to_decimal(data.get("change_percent")),
                relative_volume=_to_decimal(data.get("relative_volume")),
                pattern=data.get("pattern", "breakout"),
                screened_at=datetime.now(UTC),
            )

            if filters and not self._passes_filters(stock, filters):
                continue

            stocks.append(stock)

            if len(stocks) >= limit:
                break

        return stocks

    async def screen_by_criteria(
        self,
        filters: ScreeningFilter,
        limit: int = 20,
    ) -> ScreeningResponse:
        """
        Screen stocks by custom criteria.

        Args:
            filters: Screening filters to apply
            limit: Maximum number of results

        Returns:
            ScreeningResponse with matching stocks
        """
        # Get all available stocks
        all_stocks = []
        all_stocks.extend(await self._repository.get_maverick_stocks(limit=100))
        all_stocks.extend(await self._repository.get_maverick_bear_stocks(limit=100))
        all_stocks.extend(await self._repository.get_breakout_stocks(limit=100))

        # Deduplicate by ticker
        seen = set()
        unique_stocks = []
        for stock in all_stocks:
            if stock["ticker"] not in seen:
                seen.add(stock["ticker"])
                unique_stocks.append(stock)

        # Apply filters
        results = []
        for rank, data in enumerate(unique_stocks, 1):
            stock = MaverickStock(
                ticker=data["ticker"],
                name=data.get("name"),
                market=_detect_market(data["ticker"]),
                maverick_score=_to_decimal(data.get("maverick_score", 0)),
                current_price=_to_decimal(data.get("current_price", 0)),
                rsi=_to_decimal(data.get("rsi")),
                above_sma_50=data.get("above_sma_50", False),
                above_sma_200=data.get("above_sma_200", False),
                screened_at=datetime.now(UTC),
            )

            if not self._passes_filters(stock, filters):
                continue

            result = ScreeningResult(
                ticker=stock.ticker,
                name=stock.name,
                score=stock.maverick_score or Decimal("0"),
                rank=rank,
                metrics={
                    "price": stock.current_price,
                    "rsi": stock.rsi,
                    "above_sma_50": stock.above_sma_50,
                    "above_sma_200": stock.above_sma_200,
                },
                match_reasons=self._get_match_reasons(stock, filters),
            )
            results.append(result)

            if len(results) >= limit:
                break

        return ScreeningResponse(
            strategy=ScreeningStrategy.CUSTOM,
            results=results,
            filters=filters,
            total_scanned=len(unique_stocks),
            total_matched=len(results),
            screened_at=datetime.now(UTC),
        )

    def _passes_filters(
        self,
        stock: MaverickStock,
        filters: ScreeningFilter,
    ) -> bool:
        """Check if stock passes all filters."""
        # Price filters
        if filters.min_price and stock.current_price:
            if stock.current_price < filters.min_price:
                return False
        if filters.max_price and stock.current_price:
            if stock.current_price > filters.max_price:
                return False

        # RSI filters
        if filters.min_rsi and stock.rsi:
            if stock.rsi < filters.min_rsi:
                return False
        if filters.max_rsi and stock.rsi:
            if stock.rsi > filters.max_rsi:
                return False

        # Moving average filters
        if filters.above_sma_50 is True and not stock.above_sma_50:
            return False
        if filters.above_sma_200 is True and not stock.above_sma_200:
            return False

        # Momentum filter
        if filters.min_momentum_score and stock.momentum_score:
            if stock.momentum_score < filters.min_momentum_score:
                return False

        # Market filter
        if filters.markets and stock.market not in filters.markets:
            return False

        # Exclusion filter
        if filters.exclude_tickers and stock.ticker in filters.exclude_tickers:
            return False

        return True

    def _get_match_reasons(
        self,
        stock: MaverickStock,
        filters: ScreeningFilter,
    ) -> list[str]:
        """Get reasons why stock matched filters."""
        reasons = []

        if filters.min_price and stock.current_price:
            reasons.append(f"Price ${stock.current_price} above ${filters.min_price}")

        if filters.above_sma_50 and stock.above_sma_50:
            reasons.append("Above 50-day SMA")

        if filters.above_sma_200 and stock.above_sma_200:
            reasons.append("Above 200-day SMA")

        if filters.min_rsi and stock.rsi:
            reasons.append(f"RSI {stock.rsi} above {filters.min_rsi}")

        if stock.maverick_score and stock.maverick_score > 70:
            reasons.append(f"High Maverick score: {stock.maverick_score}")

        return reasons


__all__ = ["ScreeningService"]

