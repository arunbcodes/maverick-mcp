"""
Stock screening service.

Provides Maverick screening strategies, persona-based filtering, and risk scoring.
"""

from datetime import datetime, UTC
from decimal import Decimal
from enum import Enum
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


class InvestorPersona(str, Enum):
    """Investor risk profiles for personalized screening."""
    
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


# Persona-based filtering thresholds
PERSONA_CONFIG = {
    InvestorPersona.CONSERVATIVE: {
        "min_market_cap": 10_000_000_000,  # $10B+
        "max_volatility_percentile": 40,  # Lower volatility
        "prefer_dividend": True,
        "min_score_threshold": 60,
        "max_rsi": 70,  # Avoid overbought
        "require_sma_200": True,  # Must be above 200 SMA
        "score_weight_adjustments": {
            "stability": 1.5,
            "momentum": 0.7,
            "breakout": 0.5,
        },
    },
    InvestorPersona.MODERATE: {
        "min_market_cap": 2_000_000_000,  # $2B+
        "max_volatility_percentile": 70,
        "prefer_dividend": False,
        "min_score_threshold": 50,
        "max_rsi": 80,
        "require_sma_200": False,
        "score_weight_adjustments": {
            "stability": 1.0,
            "momentum": 1.0,
            "breakout": 1.0,
        },
    },
    InvestorPersona.AGGRESSIVE: {
        "min_market_cap": 0,  # Any size
        "max_volatility_percentile": 100,  # Higher volatility OK
        "prefer_dividend": False,
        "min_score_threshold": 40,
        "max_rsi": 90,  # Can chase momentum
        "require_sma_200": False,
        "score_weight_adjustments": {
            "stability": 0.5,
            "momentum": 1.5,
            "breakout": 1.5,
        },
    },
}


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

    # =====================
    # Persona-Based Methods
    # =====================

    async def get_maverick_stocks_by_persona(
        self,
        persona: InvestorPersona,
        limit: int = 20,
        filters: ScreeningFilter | None = None,
    ) -> list[MaverickStock]:
        """
        Get Maverick stocks filtered by investor persona.
        
        Args:
            persona: Investor risk profile
            limit: Maximum number of results
            filters: Additional filters to apply
            
        Returns:
            List of MaverickStock picks suitable for the persona
        """
        # Get more stocks than needed for filtering
        stocks = await self.get_maverick_stocks(limit=limit * 3, filters=filters)
        
        # Apply persona-based filtering and scoring
        persona_stocks = self._filter_by_persona(stocks, persona)
        
        # Sort by adjusted score and limit
        persona_stocks.sort(
            key=lambda s: self._calculate_persona_adjusted_score(s, persona),
            reverse=True
        )
        
        return persona_stocks[:limit]

    async def get_maverick_bear_stocks_by_persona(
        self,
        persona: InvestorPersona,
        limit: int = 20,
        filters: ScreeningFilter | None = None,
    ) -> list[MaverickStock]:
        """
        Get bearish stocks filtered by investor persona.
        
        Conservative investors might prefer less risky shorts (lower volatility).
        Aggressive investors might prefer high-volatility short opportunities.
        """
        stocks = await self.get_maverick_bear_stocks(limit=limit * 3, filters=filters)
        persona_stocks = self._filter_by_persona(stocks, persona)
        
        persona_stocks.sort(
            key=lambda s: self._calculate_persona_adjusted_score(s, persona),
            reverse=True
        )
        
        return persona_stocks[:limit]

    async def get_breakout_stocks_by_persona(
        self,
        persona: InvestorPersona,
        limit: int = 20,
        filters: ScreeningFilter | None = None,
    ) -> list[MaverickStock]:
        """
        Get breakout stocks filtered by investor persona.
        
        Conservative investors see fewer breakouts (higher confidence required).
        Aggressive investors see more breakout opportunities.
        """
        stocks = await self.get_breakout_stocks(limit=limit * 3, filters=filters)
        persona_stocks = self._filter_by_persona(stocks, persona)
        
        persona_stocks.sort(
            key=lambda s: self._calculate_persona_adjusted_score(s, persona),
            reverse=True
        )
        
        return persona_stocks[:limit]

    def _filter_by_persona(
        self,
        stocks: list[MaverickStock],
        persona: InvestorPersona,
    ) -> list[MaverickStock]:
        """
        Filter stocks based on persona risk profile.
        """
        config = PERSONA_CONFIG[persona]
        filtered = []
        
        for stock in stocks:
            # Apply persona-specific filters
            
            # RSI filter
            if stock.rsi and float(stock.rsi) > config["max_rsi"]:
                continue
            
            # 200 SMA requirement for conservative
            if config["require_sma_200"] and not stock.above_sma_200:
                continue
            
            # Score threshold
            if stock.maverick_score:
                if float(stock.maverick_score) < config["min_score_threshold"]:
                    continue
            
            # Add risk score to stock (stored in pattern_confidence for now)
            risk_score = self._calculate_risk_score(stock)
            
            # Conservative investors skip high-risk stocks
            if persona == InvestorPersona.CONSERVATIVE and risk_score > 6:
                continue
            
            # Store risk score for API response
            stock.pattern_confidence = Decimal(str(risk_score))
            
            filtered.append(stock)
        
        return filtered

    def _calculate_persona_adjusted_score(
        self,
        stock: MaverickStock,
        persona: InvestorPersona,
    ) -> float:
        """
        Calculate a persona-adjusted score for ranking.
        
        Different personas weight different factors differently.
        """
        config = PERSONA_CONFIG[persona]
        weights = config["score_weight_adjustments"]
        
        base_score = float(stock.maverick_score or 0)
        
        # Stability bonus (above both SMAs)
        stability_bonus = 0
        if stock.above_sma_50 and stock.above_sma_200:
            stability_bonus = 10 * weights["stability"]
        elif stock.above_sma_50:
            stability_bonus = 5 * weights["stability"]
        
        # Momentum bonus (RSI in good range)
        momentum_bonus = 0
        if stock.rsi:
            rsi = float(stock.rsi)
            if 40 <= rsi <= 60:
                momentum_bonus = 5 * weights["momentum"]
            elif 30 <= rsi <= 70:
                momentum_bonus = 3 * weights["momentum"]
        
        # Breakout bonus (high relative volume)
        breakout_bonus = 0
        if stock.relative_volume:
            rv = float(stock.relative_volume)
            if rv > 2.0:
                breakout_bonus = 10 * weights["breakout"]
            elif rv > 1.5:
                breakout_bonus = 5 * weights["breakout"]
        
        return base_score + stability_bonus + momentum_bonus + breakout_bonus

    def _calculate_risk_score(self, stock: MaverickStock) -> int:
        """
        Calculate a risk score from 1-10 for a stock.
        
        Higher score = higher risk.
        
        Factors:
        - RSI extremes increase risk
        - Lack of SMA support increases risk
        - High relative volume increases risk
        - Pattern type affects risk
        """
        risk = 5  # Start at medium risk
        
        # RSI extremes
        if stock.rsi:
            rsi = float(stock.rsi)
            if rsi > 80 or rsi < 20:
                risk += 2  # Very overbought/oversold
            elif rsi > 70 or rsi < 30:
                risk += 1
        
        # SMA support
        if stock.above_sma_50 and stock.above_sma_200:
            risk -= 2  # Strong support
        elif stock.above_sma_50 or stock.above_sma_200:
            risk -= 1
        else:
            risk += 1  # Below both SMAs
        
        # High volume can indicate volatility
        if stock.relative_volume:
            rv = float(stock.relative_volume)
            if rv > 3.0:
                risk += 2
            elif rv > 2.0:
                risk += 1
        
        # Pattern-based risk
        if stock.pattern:
            pattern_lower = stock.pattern.lower()
            if "breakout" in pattern_lower or "gap" in pattern_lower:
                risk += 1  # Breakouts are riskier
            elif "consolidation" in pattern_lower or "base" in pattern_lower:
                risk -= 1  # More stable patterns
        
        # Clamp to 1-10 range
        return max(1, min(10, risk))

    @staticmethod
    def calculate_risk_score_for_data(
        rsi: float | None = None,
        above_sma_50: bool = False,
        above_sma_200: bool = False,
        relative_volume: float | None = None,
        pattern: str | None = None,
    ) -> int:
        """
        Static method to calculate risk score from raw data.
        
        Useful when you don't have a MaverickStock object.
        """
        risk = 5
        
        if rsi:
            if rsi > 80 or rsi < 20:
                risk += 2
            elif rsi > 70 or rsi < 30:
                risk += 1
        
        if above_sma_50 and above_sma_200:
            risk -= 2
        elif above_sma_50 or above_sma_200:
            risk -= 1
        else:
            risk += 1
        
        if relative_volume:
            if relative_volume > 3.0:
                risk += 2
            elif relative_volume > 2.0:
                risk += 1
        
        if pattern:
            pattern_lower = pattern.lower()
            if "breakout" in pattern_lower or "gap" in pattern_lower:
                risk += 1
            elif "consolidation" in pattern_lower or "base" in pattern_lower:
                risk -= 1
        
        return max(1, min(10, risk))


__all__ = [
    "ScreeningService",
    "InvestorPersona",
    "PERSONA_CONFIG",
]

