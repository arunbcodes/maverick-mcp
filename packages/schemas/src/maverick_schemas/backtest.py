"""
Backtesting models.

Models for strategy configuration, backtest results, and optimization.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import Field

from maverick_schemas.base import MaverickBaseModel, OrderSide


class StrategyType(str, Enum):
    """Available backtesting strategies."""
    
    SMA_CROSS = "sma_cross"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER = "bollinger"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ML_PREDICTOR = "ml_predictor"
    ENSEMBLE = "ensemble"


class JobStatus(str, Enum):
    """Async job status."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StrategyConfig(MaverickBaseModel):
    """Strategy configuration for backtesting."""
    
    strategy_type: StrategyType = Field(description="Strategy type")
    
    # Common parameters
    initial_capital: Decimal = Field(default=Decimal("10000"), description="Starting capital")
    position_size: Decimal = Field(default=Decimal("1.0"), description="Position size (0-1)")
    
    # Strategy-specific parameters (flexible dict)
    parameters: dict[str, int | float | str | bool] = Field(
        default_factory=dict,
        description="Strategy-specific parameters"
    )


class BacktestRequest(MaverickBaseModel):
    """Request model for running a backtest."""
    
    symbol: str = Field(description="Stock symbol to backtest")
    strategy: StrategyConfig = Field(description="Strategy configuration")
    
    # Date range
    start_date: date | None = Field(default=None, description="Backtest start date")
    end_date: date | None = Field(default=None, description="Backtest end date")
    
    # Options
    include_charts: bool = Field(default=False, description="Generate charts")
    include_trades: bool = Field(default=True, description="Include trade details")


class BacktestTrade(MaverickBaseModel):
    """Individual trade in a backtest."""
    
    trade_id: int = Field(description="Trade sequence number")
    
    # Entry
    entry_date: date = Field(description="Entry date")
    entry_price: Decimal = Field(description="Entry price")
    entry_side: OrderSide = Field(description="Entry side")
    
    # Exit
    exit_date: date | None = Field(default=None, description="Exit date")
    exit_price: Decimal | None = Field(default=None, description="Exit price")
    
    # Position
    shares: Decimal = Field(description="Number of shares")
    position_value: Decimal = Field(description="Position value at entry")
    
    # P&L
    pnl: Decimal | None = Field(default=None, description="Profit/loss")
    pnl_percent: Decimal | None = Field(default=None, description="P&L percentage")
    
    # Duration
    holding_days: int | None = Field(default=None, description="Days held")
    
    # Signal info
    entry_signal: str | None = Field(default=None, description="Entry signal description")
    exit_signal: str | None = Field(default=None, description="Exit signal description")


class BacktestMetrics(MaverickBaseModel):
    """Performance metrics from a backtest."""
    
    # Returns
    total_return: Decimal = Field(description="Total return percentage")
    annual_return: Decimal = Field(description="Annualized return")
    
    # Risk metrics
    volatility: Decimal = Field(description="Annualized volatility")
    sharpe_ratio: Decimal = Field(description="Sharpe ratio")
    sortino_ratio: Decimal | None = Field(default=None, description="Sortino ratio")
    max_drawdown: Decimal = Field(description="Maximum drawdown")
    
    # Trade statistics
    total_trades: int = Field(description="Total number of trades")
    winning_trades: int = Field(description="Number of winning trades")
    losing_trades: int = Field(description="Number of losing trades")
    win_rate: Decimal = Field(description="Win rate percentage")
    
    # Average trade
    avg_win: Decimal | None = Field(default=None, description="Average winning trade")
    avg_loss: Decimal | None = Field(default=None, description="Average losing trade")
    profit_factor: Decimal | None = Field(default=None, description="Profit factor")
    
    # Exposure
    avg_holding_days: Decimal | None = Field(default=None, description="Average holding period")
    time_in_market: Decimal | None = Field(default=None, description="% time in market")
    
    # Benchmark comparison
    benchmark_return: Decimal | None = Field(default=None, description="Benchmark return")
    alpha: Decimal | None = Field(default=None, description="Alpha vs benchmark")
    beta: Decimal | None = Field(default=None, description="Beta vs benchmark")


class BacktestResult(MaverickBaseModel):
    """Complete backtest result."""
    
    # Request info
    symbol: str = Field(description="Symbol backtested")
    strategy: StrategyConfig = Field(description="Strategy used")
    start_date: date = Field(description="Backtest start date")
    end_date: date = Field(description="Backtest end date")
    
    # Results
    metrics: BacktestMetrics = Field(description="Performance metrics")
    trades: list[BacktestTrade] = Field(default_factory=list, description="Trade history")
    
    # Equity curve
    equity_curve: list[Decimal] | None = Field(default=None, description="Daily equity values")
    
    # Charts (base64 encoded if requested)
    charts: dict[str, str] | None = Field(default=None, description="Chart images")
    
    # Execution info
    execution_time_ms: int = Field(description="Execution time in milliseconds")
    completed_at: datetime = Field(description="Completion timestamp")


class BacktestJob(MaverickBaseModel):
    """Async backtest job status."""
    
    job_id: str = Field(description="Job ID")
    status: JobStatus = Field(description="Job status")
    
    # Progress
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    message: str | None = Field(default=None, description="Status message")
    
    # Timing
    created_at: datetime = Field(description="Job creation time")
    started_at: datetime | None = Field(default=None, description="Job start time")
    completed_at: datetime | None = Field(default=None, description="Job completion time")
    
    # Result (when completed)
    result: BacktestResult | None = Field(default=None, description="Backtest result")
    error: str | None = Field(default=None, description="Error message if failed")


class OptimizationResult(MaverickBaseModel):
    """Strategy optimization result."""
    
    symbol: str = Field(description="Symbol optimized")
    strategy_type: StrategyType = Field(description="Strategy type")
    
    # Best parameters
    best_parameters: dict[str, int | float] = Field(description="Optimal parameters")
    best_sharpe: Decimal = Field(description="Best Sharpe ratio achieved")
    best_return: Decimal = Field(description="Best return achieved")
    
    # Parameter sensitivity
    parameter_importance: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Parameter importance scores"
    )
    
    # Top combinations
    top_results: list[dict] = Field(default_factory=list, description="Top parameter combinations")
    
    # Metadata
    combinations_tested: int = Field(description="Number of combinations tested")
    execution_time_ms: int = Field(description="Execution time")


class WalkForwardResult(MaverickBaseModel):
    """Walk-forward analysis result."""
    
    symbol: str = Field(description="Symbol analyzed")
    strategy_type: StrategyType = Field(description="Strategy type")
    
    # Period results
    periods: list[dict] = Field(description="Individual period results")
    
    # Aggregate metrics
    avg_in_sample_sharpe: Decimal = Field(description="Average in-sample Sharpe")
    avg_out_sample_sharpe: Decimal = Field(description="Average out-of-sample Sharpe")
    consistency_ratio: Decimal = Field(description="Out/In sample performance ratio")
    
    # Is strategy robust?
    is_robust: bool = Field(description="Whether strategy passes robustness test")
    robustness_score: Decimal = Field(description="Robustness score (0-100)")


__all__ = [
    "StrategyType",
    "JobStatus",
    "StrategyConfig",
    "BacktestRequest",
    "BacktestTrade",
    "BacktestMetrics",
    "BacktestResult",
    "BacktestJob",
    "OptimizationResult",
    "WalkForwardResult",
]

