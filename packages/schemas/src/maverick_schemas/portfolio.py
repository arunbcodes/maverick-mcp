"""
Portfolio and position models.

Models for tracking positions, portfolio performance, and P&L.
"""

import datetime as dt
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from maverick_schemas.base import Market, MaverickBaseModel, PositionStatus


class Position(MaverickBaseModel):
    """Stock position in a portfolio."""
    
    id: str | None = Field(default=None, description="Position ID")
    ticker: str = Field(description="Stock ticker symbol")
    shares: Decimal = Field(gt=0, description="Number of shares")
    
    # Cost basis
    avg_cost: Decimal = Field(description="Average cost per share")
    total_cost: Decimal = Field(description="Total cost basis")
    
    # Current values (populated when requested)
    current_price: Decimal | None = Field(default=None, description="Current market price")
    current_value: Decimal | None = Field(default=None, description="Current market value")
    
    # P&L
    unrealized_pnl: Decimal | None = Field(default=None, description="Unrealized profit/loss")
    unrealized_pnl_percent: Decimal | None = Field(default=None, description="Unrealized P&L percentage")
    
    # Position details
    market: Market = Field(default=Market.US, description="Market")
    status: PositionStatus = Field(default=PositionStatus.OPEN, description="Position status")
    
    # Dates
    first_purchase_date: dt.date | None = Field(default=None, description="First purchase date")
    last_updated: datetime | None = Field(default=None, description="Last update timestamp")
    
    # Notes
    notes: str | None = Field(default=None, description="Position notes")


class PositionCreate(MaverickBaseModel):
    """Request model for creating a position."""
    
    ticker: str = Field(description="Stock ticker symbol")
    shares: Decimal = Field(gt=0, description="Number of shares")
    purchase_price: Decimal = Field(gt=0, description="Purchase price per share")
    purchase_date: dt.date | None = Field(default=None, description="Purchase date")
    notes: str | None = Field(default=None, description="Optional notes")


class PositionUpdate(MaverickBaseModel):
    """Request model for updating a position."""
    
    shares: Decimal | None = Field(default=None, gt=0, description="New share count")
    notes: str | None = Field(default=None, description="Updated notes")


class PortfolioSummary(MaverickBaseModel):
    """Portfolio summary metrics."""
    
    total_value: Decimal = Field(description="Total portfolio value")
    total_cost: Decimal = Field(description="Total cost basis")
    
    # Overall P&L
    total_pnl: Decimal = Field(description="Total unrealized P&L")
    total_pnl_percent: Decimal = Field(description="Total P&L percentage")
    
    # Position counts
    position_count: int = Field(description="Number of positions")
    winning_positions: int = Field(default=0, description="Positions in profit")
    losing_positions: int = Field(default=0, description="Positions in loss")
    
    # Cash (if tracked)
    cash_balance: Decimal = Field(default=Decimal("0"), description="Cash balance")
    
    # Timestamps
    last_updated: datetime = Field(description="Last calculation timestamp")


class PerformanceDataPoint(MaverickBaseModel):
    """Single data point in performance time series."""
    
    date: dt.date = Field(description="Date")
    portfolio_value: Decimal = Field(description="Portfolio value")
    daily_return: Decimal | None = Field(default=None, description="Daily return %")
    cumulative_return: Decimal | None = Field(default=None, description="Cumulative return %")
    benchmark_value: Decimal | None = Field(default=None, description="Benchmark value")
    benchmark_return: Decimal | None = Field(default=None, description="Benchmark cumulative return %")


class PortfolioPerformance(MaverickBaseModel):
    """Portfolio performance over time."""
    
    period: str = Field(description="Performance period (1D, 1W, 1M, 3M, 6M, 1Y, YTD, ALL)")
    
    # Returns
    return_value: Decimal = Field(description="Return in currency")
    return_percent: Decimal = Field(description="Return percentage")
    
    # Benchmark comparison
    benchmark_return: Decimal | None = Field(default=None, description="Benchmark return")
    alpha: Decimal | None = Field(default=None, description="Alpha vs benchmark")
    
    # Risk metrics
    volatility: Decimal | None = Field(default=None, description="Portfolio volatility")
    sharpe_ratio: Decimal | None = Field(default=None, description="Sharpe ratio")
    max_drawdown: Decimal | None = Field(default=None, description="Maximum drawdown")
    
    # Time series (for charts)
    daily_returns: list[Decimal] | None = Field(default=None, description="Daily returns")
    cumulative_returns: list[Decimal] | None = Field(default=None, description="Cumulative returns")


class PortfolioPerformanceChart(MaverickBaseModel):
    """Portfolio performance data for charting."""
    
    period: str = Field(description="Performance period (7d, 30d, 90d, 1y)")
    start_date: dt.date = Field(description="Start date")
    end_date: dt.date = Field(description="End date")
    
    # Summary metrics
    total_return: Decimal = Field(description="Total return %")
    total_return_value: Decimal = Field(description="Total return value")
    benchmark_return: Decimal | None = Field(default=None, description="Benchmark return %")
    alpha: Decimal | None = Field(default=None, description="Alpha vs benchmark")
    
    # Risk metrics
    volatility: Decimal | None = Field(default=None, description="Annualized volatility %")
    sharpe_ratio: Decimal | None = Field(default=None, description="Sharpe ratio")
    max_drawdown: Decimal | None = Field(default=None, description="Maximum drawdown %")
    max_drawdown_date: dt.date | None = Field(default=None, description="Date of max drawdown")
    
    # Time series for charting
    data: list[PerformanceDataPoint] = Field(description="Time series data")


class Portfolio(MaverickBaseModel):
    """Complete portfolio with positions and summary."""
    
    id: str | None = Field(default=None, description="Portfolio ID")
    name: str = Field(default="My Portfolio", description="Portfolio name")
    user_id: str = Field(description="Owner user ID")
    
    # Positions
    positions: list[Position] = Field(default_factory=list, description="Portfolio positions")
    
    # Summary
    summary: PortfolioSummary | None = Field(default=None, description="Portfolio summary")
    
    # Performance
    performance: dict[str, PortfolioPerformance] | None = Field(
        default=None,
        description="Performance by period"
    )
    
    # Metadata
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")


class PortfolioAllocation(MaverickBaseModel):
    """Portfolio allocation by various dimensions."""
    
    by_sector: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Allocation by sector"
    )
    by_market: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Allocation by market"
    )
    by_position: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Allocation by position"
    )
    
    # Concentration metrics
    top_5_concentration: Decimal = Field(description="Top 5 positions as % of portfolio")
    herfindahl_index: Decimal | None = Field(default=None, description="Concentration index")


class CorrelationMatrix(MaverickBaseModel):
    """Portfolio correlation analysis."""
    
    tickers: list[str] = Field(description="Tickers in correlation matrix")
    matrix: list[list[Decimal]] = Field(description="Correlation matrix values")
    
    # Summary
    avg_correlation: Decimal = Field(description="Average pairwise correlation")
    highly_correlated_pairs: list[tuple[str, str, Decimal]] = Field(
        default_factory=list,
        description="Pairs with correlation > 0.7"
    )


__all__ = [
    "Position",
    "PositionCreate",
    "PositionUpdate",
    "PortfolioSummary",
    "PerformanceDataPoint",
    "PortfolioPerformance",
    "PortfolioPerformanceChart",
    "Portfolio",
    "PortfolioAllocation",
    "CorrelationMatrix",
]

