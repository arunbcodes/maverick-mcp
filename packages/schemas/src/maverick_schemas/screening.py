"""
Stock screening models.

Models for screening results, filters, and Maverick stock picks.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import Field

from maverick_schemas.base import Market, MaverickBaseModel, TrendDirection


class ScreeningStrategy(str, Enum):
    """Available screening strategies."""
    
    MAVERICK = "maverick"
    MAVERICK_BEAR = "maverick_bear"
    SUPPLY_DEMAND_BREAKOUT = "supply_demand_breakout"
    MOMENTUM = "momentum"
    VALUE = "value"
    DIVIDEND = "dividend"
    CUSTOM = "custom"


class MaverickStock(MaverickBaseModel):
    """Stock picked by Maverick screening strategy."""
    
    ticker: str = Field(description="Stock ticker symbol")
    name: str | None = Field(default=None, description="Company name")
    market: Market = Field(default=Market.US, description="Market")
    
    # Scoring
    maverick_score: Decimal = Field(description="Maverick score (0-100)")
    momentum_score: Decimal | None = Field(default=None, description="Momentum score")
    trend_score: Decimal | None = Field(default=None, description="Trend score")
    
    # Price data
    current_price: Decimal = Field(description="Current price")
    change_percent: Decimal | None = Field(default=None, description="Daily change %")
    
    # Technical metrics
    rsi: Decimal | None = Field(default=None, description="RSI value")
    trend: TrendDirection | None = Field(default=None, description="Trend direction")
    
    # Moving averages
    above_sma_50: bool = Field(default=False, description="Price above 50 SMA")
    above_sma_200: bool = Field(default=False, description="Price above 200 SMA")
    
    # Volume
    relative_volume: Decimal | None = Field(default=None, description="Volume vs average")
    
    # Pattern recognition
    pattern: str | None = Field(default=None, description="Detected pattern")
    pattern_confidence: Decimal | None = Field(default=None, description="Pattern confidence")
    
    # Metadata
    screened_at: datetime | None = Field(default=None, description="Screening timestamp")


class ScreeningFilter(MaverickBaseModel):
    """Filter criteria for stock screening."""
    
    # Price filters
    min_price: Decimal | None = Field(default=None, ge=0, description="Minimum price")
    max_price: Decimal | None = Field(default=None, ge=0, description="Maximum price")
    
    # Volume filters
    min_volume: int | None = Field(default=None, ge=0, description="Minimum avg volume")
    min_relative_volume: Decimal | None = Field(default=None, ge=0, description="Min relative volume")
    
    # Market cap filters
    min_market_cap: Decimal | None = Field(default=None, ge=0, description="Min market cap")
    max_market_cap: Decimal | None = Field(default=None, ge=0, description="Max market cap")
    
    # Technical filters
    min_rsi: Decimal | None = Field(default=None, ge=0, le=100, description="Min RSI")
    max_rsi: Decimal | None = Field(default=None, ge=0, le=100, description="Max RSI")
    above_sma_50: bool | None = Field(default=None, description="Require above 50 SMA")
    above_sma_200: bool | None = Field(default=None, description="Require above 200 SMA")
    
    # Momentum filters
    min_momentum_score: Decimal | None = Field(default=None, ge=0, le=100, description="Min momentum")
    
    # Sector/Market filters
    sectors: list[str] | None = Field(default=None, description="Filter by sectors")
    markets: list[Market] | None = Field(default=None, description="Filter by markets")
    
    # Exclusions
    exclude_tickers: list[str] | None = Field(default=None, description="Tickers to exclude")


class ScreeningResult(MaverickBaseModel):
    """Individual screening result."""
    
    ticker: str = Field(description="Stock ticker symbol")
    name: str | None = Field(default=None, description="Company name")
    sector: str | None = Field(default=None, description="Sector")
    
    # Scores
    score: Decimal = Field(description="Overall screening score")
    rank: int = Field(description="Rank in results")
    
    # Key metrics (varies by strategy)
    metrics: dict[str, Decimal | str | bool] = Field(
        default_factory=dict,
        description="Strategy-specific metrics"
    )
    
    # Match reasons
    match_reasons: list[str] = Field(
        default_factory=list,
        description="Why this stock matched"
    )


class ScreeningResponse(MaverickBaseModel):
    """Response from screening endpoint."""
    
    strategy: ScreeningStrategy = Field(description="Screening strategy used")
    results: list[ScreeningResult] = Field(description="Screening results")
    
    # Filters applied
    filters: ScreeningFilter | None = Field(default=None, description="Filters applied")
    
    # Metadata
    total_scanned: int = Field(description="Total stocks scanned")
    total_matched: int = Field(description="Stocks matching criteria")
    screened_at: datetime = Field(description="Screening timestamp")
    
    # Data freshness
    data_as_of: datetime | None = Field(default=None, description="Price data timestamp")


class MaverickScreeningResponse(MaverickBaseModel):
    """Response from Maverick-specific screening."""
    
    bullish: list[MaverickStock] = Field(default_factory=list, description="Bullish picks")
    bearish: list[MaverickStock] = Field(default_factory=list, description="Bearish picks")
    breakouts: list[MaverickStock] = Field(default_factory=list, description="Breakout candidates")
    
    # Summary
    total_bullish: int = Field(description="Total bullish picks")
    total_bearish: int = Field(description="Total bearish picks")
    total_breakouts: int = Field(description="Total breakout candidates")
    
    # Metadata
    screened_at: datetime = Field(description="Screening timestamp")
    market_sentiment: str = Field(description="Overall market sentiment")


__all__ = [
    "ScreeningStrategy",
    "MaverickStock",
    "ScreeningFilter",
    "ScreeningResult",
    "ScreeningResponse",
    "MaverickScreeningResponse",
]

