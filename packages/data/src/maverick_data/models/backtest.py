"""
Backtest models for storing strategy testing results.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, Session, relationship

from maverick_data.models.base import Base, TimestampMixin


class BacktestResult(Base, TimestampMixin):
    """Main backtest results table with comprehensive metrics."""

    __tablename__ = "mcp_backtest_results"
    __table_args__ = (
        Index("mcp_backtest_results_symbol_idx", "symbol"),
        Index("mcp_backtest_results_strategy_idx", "strategy_type"),
        Index("mcp_backtest_results_date_idx", "backtest_date"),
        Index("mcp_backtest_results_sharpe_idx", "sharpe_ratio"),
        Index("mcp_backtest_results_total_return_idx", "total_return"),
        Index("mcp_backtest_results_symbol_strategy_idx", "symbol", "strategy_type"),
    )

    backtest_id = Column(Uuid, primary_key=True, default=uuid.uuid4)

    # Basic backtest metadata
    symbol = Column(String(10), nullable=False, index=True)
    strategy_type = Column(String(50), nullable=False)
    backtest_date = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    # Date range and setup
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_capital = Column(Numeric(15, 2), default=10000.0)

    # Trading costs and parameters
    fees = Column(Numeric(6, 4), default=0.001)
    slippage = Column(Numeric(6, 4), default=0.001)

    # Strategy parameters (stored as JSON for flexibility)
    parameters = Column(JSON)

    # Key Performance Metrics
    total_return = Column(Numeric(10, 4))
    annualized_return = Column(Numeric(10, 4))
    sharpe_ratio = Column(Numeric(8, 4))
    sortino_ratio = Column(Numeric(8, 4))
    calmar_ratio = Column(Numeric(8, 4))

    # Risk Metrics
    max_drawdown = Column(Numeric(8, 4))
    max_drawdown_duration = Column(Integer)
    volatility = Column(Numeric(8, 4))
    downside_volatility = Column(Numeric(8, 4))

    # Trade Statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Numeric(5, 4))

    # P&L Statistics
    profit_factor = Column(Numeric(8, 4))
    average_win = Column(Numeric(12, 4))
    average_loss = Column(Numeric(12, 4))
    largest_win = Column(Numeric(12, 4))
    largest_loss = Column(Numeric(12, 4))

    # Portfolio Value Metrics
    final_portfolio_value = Column(Numeric(15, 2))
    peak_portfolio_value = Column(Numeric(15, 2))

    # Additional Analysis
    beta = Column(Numeric(8, 4))
    alpha = Column(Numeric(8, 4))

    # Time series data (stored as JSON for efficient queries)
    equity_curve = Column(JSON)
    drawdown_series = Column(JSON)

    # Execution metadata
    execution_time_seconds = Column(Numeric(8, 3))
    data_points = Column(Integer)

    # Status and notes
    status = Column(String(20), default="completed")
    error_message = Column(Text)
    notes = Column(Text)

    # Relationships
    trades: Mapped[list["BacktestTrade"]] = relationship(
        "BacktestTrade",
        back_populates="backtest_result",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    optimization_results: Mapped[list["OptimizationResult"]] = relationship(
        "OptimizationResult",
        back_populates="backtest_result",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<BacktestResult(id={self.backtest_id}, symbol={self.symbol}, "
            f"strategy={self.strategy_type}, return={self.total_return})>"
        )

    @classmethod
    def get_by_symbol_and_strategy(
        cls, session: Session, symbol: str, strategy_type: str, limit: int = 10
    ) -> Sequence[BacktestResult]:
        """Get recent backtests for a specific symbol and strategy."""
        return (
            session.query(cls)
            .filter(cls.symbol == symbol.upper(), cls.strategy_type == strategy_type)
            .order_by(cls.backtest_date.desc())
            .limit(limit)
            .all()
        )

    @classmethod
    def get_best_performing(
        cls, session: Session, metric: str = "sharpe_ratio", limit: int = 20
    ) -> Sequence[BacktestResult]:
        """Get best performing backtests by specified metric."""
        metric_column = getattr(cls, metric, cls.sharpe_ratio)
        return (
            session.query(cls)
            .filter(cls.status == "completed")
            .order_by(metric_column.desc())
            .limit(limit)
            .all()
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "backtest_id": str(self.backtest_id),
            "symbol": self.symbol,
            "strategy_type": self.strategy_type,
            "backtest_date": (
                self.backtest_date.isoformat() if self.backtest_date else None
            ),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "initial_capital": (
                float(self.initial_capital) if self.initial_capital else 0
            ),
            "total_return": float(self.total_return) if self.total_return else 0,
            "sharpe_ratio": float(self.sharpe_ratio) if self.sharpe_ratio else 0,
            "max_drawdown": float(self.max_drawdown) if self.max_drawdown else 0,
            "win_rate": float(self.win_rate) if self.win_rate else 0,
            "total_trades": self.total_trades,
            "parameters": self.parameters,
            "status": self.status,
        }


class BacktestTrade(Base, TimestampMixin):
    """Individual trade records from backtests."""

    __tablename__ = "mcp_backtest_trades"
    __table_args__ = (
        Index("mcp_backtest_trades_backtest_idx", "backtest_id"),
        Index("mcp_backtest_trades_entry_date_idx", "entry_date"),
        Index("mcp_backtest_trades_exit_date_idx", "exit_date"),
        Index("mcp_backtest_trades_pnl_idx", "pnl"),
        Index("mcp_backtest_trades_backtest_entry_idx", "backtest_id", "entry_date"),
    )

    trade_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    backtest_id = Column(
        Uuid, ForeignKey("mcp_backtest_results.backtest_id"), nullable=False
    )

    # Trade identification
    trade_number = Column(Integer, nullable=False)

    # Entry details
    entry_date = Column(Date, nullable=False)
    entry_price = Column(Numeric(12, 4), nullable=False)
    entry_time = Column(DateTime(timezone=True))

    # Exit details
    exit_date = Column(Date)
    exit_price = Column(Numeric(12, 4))
    exit_time = Column(DateTime(timezone=True))

    # Position details
    position_size = Column(Numeric(15, 2))
    direction = Column(String(5), nullable=False)

    # P&L and performance
    pnl = Column(Numeric(12, 4))
    pnl_percent = Column(Numeric(8, 4))

    # Risk metrics for this trade
    mae = Column(Numeric(8, 4))
    mfe = Column(Numeric(8, 4))

    # Trade duration
    duration_days = Column(Integer)
    duration_hours = Column(Numeric(8, 2))

    # Exit reason and fees
    exit_reason = Column(String(50))
    fees_paid = Column(Numeric(10, 4), default=0)
    slippage_cost = Column(Numeric(10, 4), default=0)

    # Relationships
    backtest_result: Mapped["BacktestResult"] = relationship(
        "BacktestResult", back_populates="trades", lazy="joined"
    )

    def __repr__(self):
        return (
            f"<BacktestTrade(id={self.trade_id}, backtest_id={self.backtest_id}, "
            f"pnl={self.pnl}, duration={self.duration_days}d)>"
        )

    @classmethod
    def get_trades_for_backtest(
        cls, session: Session, backtest_id: str
    ) -> Sequence[BacktestTrade]:
        """Get all trades for a specific backtest."""
        return (
            session.query(cls)
            .filter(cls.backtest_id == backtest_id)
            .order_by(cls.entry_date, cls.trade_number)
            .all()
        )

    @classmethod
    def get_winning_trades(
        cls, session: Session, backtest_id: str
    ) -> Sequence[BacktestTrade]:
        """Get winning trades for a backtest."""
        return (
            session.query(cls)
            .filter(cls.backtest_id == backtest_id, cls.pnl > 0)
            .order_by(cls.pnl.desc())
            .all()
        )

    @classmethod
    def get_losing_trades(
        cls, session: Session, backtest_id: str
    ) -> Sequence[BacktestTrade]:
        """Get losing trades for a backtest."""
        return (
            session.query(cls)
            .filter(cls.backtest_id == backtest_id, cls.pnl < 0)
            .order_by(cls.pnl)
            .all()
        )


class OptimizationResult(Base, TimestampMixin):
    """Parameter optimization results for strategies."""

    __tablename__ = "mcp_optimization_results"
    __table_args__ = (
        Index("mcp_optimization_results_backtest_idx", "backtest_id"),
        Index("mcp_optimization_results_param_set_idx", "parameter_set"),
        Index("mcp_optimization_results_objective_idx", "objective_value"),
    )

    optimization_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    backtest_id = Column(
        Uuid, ForeignKey("mcp_backtest_results.backtest_id"), nullable=False
    )

    # Optimization metadata
    optimization_date = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    parameter_set = Column(Integer, nullable=False)

    # Parameters tested (JSON for flexibility)
    parameters = Column(JSON, nullable=False)

    # Optimization objective and results
    objective_function = Column(String(50))
    objective_value = Column(Numeric(12, 6))

    # Key metrics for this parameter set
    total_return = Column(Numeric(10, 4))
    sharpe_ratio = Column(Numeric(8, 4))
    max_drawdown = Column(Numeric(8, 4))
    win_rate = Column(Numeric(5, 4))
    profit_factor = Column(Numeric(8, 4))
    total_trades = Column(Integer)

    # Ranking within optimization
    rank = Column(Integer)

    # Statistical significance
    is_statistically_significant = Column(Boolean, default=False)
    p_value = Column(Numeric(8, 6))

    # Relationships
    backtest_result: Mapped["BacktestResult"] = relationship(
        "BacktestResult", back_populates="optimization_results", lazy="joined"
    )

    def __repr__(self):
        return (
            f"<OptimizationResult(id={self.optimization_id}, "
            f"objective={self.objective_value}, rank={self.rank})>"
        )

    @classmethod
    def get_best_parameters(
        cls, session: Session, backtest_id: str, limit: int = 5
    ) -> Sequence[OptimizationResult]:
        """Get top performing parameter sets for a backtest."""
        return (
            session.query(cls)
            .filter(cls.backtest_id == backtest_id)
            .order_by(cls.rank)
            .limit(limit)
            .all()
        )


class WalkForwardTest(Base, TimestampMixin):
    """Walk-forward validation test results."""

    __tablename__ = "mcp_walk_forward_tests"
    __table_args__ = (
        Index("mcp_walk_forward_tests_parent_idx", "parent_backtest_id"),
        Index("mcp_walk_forward_tests_period_idx", "test_period_start"),
        Index("mcp_walk_forward_tests_performance_idx", "out_of_sample_return"),
    )

    walk_forward_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    parent_backtest_id = Column(
        Uuid, ForeignKey("mcp_backtest_results.backtest_id"), nullable=False
    )

    # Test configuration
    test_date = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    window_size_months = Column(Integer, nullable=False)
    step_size_months = Column(Integer, nullable=False)

    # Time periods
    training_start = Column(Date, nullable=False)
    training_end = Column(Date, nullable=False)
    test_period_start = Column(Date, nullable=False)
    test_period_end = Column(Date, nullable=False)

    # Optimization results from training period
    optimal_parameters = Column(JSON)
    training_performance = Column(Numeric(10, 4))

    # Out-of-sample test results
    out_of_sample_return = Column(Numeric(10, 4))
    out_of_sample_sharpe = Column(Numeric(8, 4))
    out_of_sample_drawdown = Column(Numeric(8, 4))
    out_of_sample_trades = Column(Integer)

    # Performance vs training expectations
    performance_ratio = Column(Numeric(8, 4))
    degradation_factor = Column(Numeric(8, 4))

    # Statistical validation
    is_profitable = Column(Boolean)
    is_statistically_significant = Column(Boolean, default=False)

    # Relationships
    parent_backtest: Mapped["BacktestResult"] = relationship(
        "BacktestResult", foreign_keys=[parent_backtest_id], lazy="joined"
    )

    def __repr__(self):
        return (
            f"<WalkForwardTest(id={self.walk_forward_id}, "
            f"return={self.out_of_sample_return}, ratio={self.performance_ratio})>"
        )

    @classmethod
    def get_walk_forward_results(
        cls, session: Session, parent_backtest_id: str
    ) -> Sequence[WalkForwardTest]:
        """Get all walk-forward test results for a backtest."""
        return (
            session.query(cls)
            .filter(cls.parent_backtest_id == parent_backtest_id)
            .order_by(cls.test_period_start)
            .all()
        )


class BacktestPortfolio(Base, TimestampMixin):
    """Portfolio-level backtests with multiple symbols."""

    __tablename__ = "mcp_backtest_portfolios"
    __table_args__ = (
        Index("mcp_backtest_portfolios_name_idx", "portfolio_name"),
        Index("mcp_backtest_portfolios_date_idx", "backtest_date"),
        Index("mcp_backtest_portfolios_return_idx", "total_return"),
    )

    portfolio_backtest_id = Column(Uuid, primary_key=True, default=uuid.uuid4)

    # Portfolio identification
    portfolio_name = Column(String(100), nullable=False)
    description = Column(Text)

    # Test metadata
    backtest_date = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Portfolio composition
    symbols = Column(JSON, nullable=False)
    weights = Column(JSON)
    rebalance_frequency = Column(String(20))

    # Portfolio parameters
    initial_capital = Column(Numeric(15, 2), default=100000.0)
    max_positions = Column(Integer)
    position_sizing_method = Column(String(50))

    # Risk management
    portfolio_stop_loss = Column(Numeric(6, 4))
    max_sector_allocation = Column(Numeric(5, 4))
    correlation_threshold = Column(Numeric(5, 4))

    # Performance metrics (portfolio level)
    total_return = Column(Numeric(10, 4))
    annualized_return = Column(Numeric(10, 4))
    sharpe_ratio = Column(Numeric(8, 4))
    sortino_ratio = Column(Numeric(8, 4))
    max_drawdown = Column(Numeric(8, 4))
    volatility = Column(Numeric(8, 4))

    # Portfolio-specific metrics
    diversification_ratio = Column(Numeric(8, 4))
    concentration_index = Column(Numeric(8, 4))
    turnover_rate = Column(Numeric(8, 4))

    # Individual component backtests (JSON references)
    component_backtest_ids = Column(JSON)

    # Time series data
    portfolio_equity_curve = Column(JSON)
    portfolio_weights_history = Column(JSON)

    # Status
    status = Column(String(20), default="completed")
    notes = Column(Text)

    def __repr__(self):
        return (
            f"<BacktestPortfolio(id={self.portfolio_backtest_id}, "
            f"name={self.portfolio_name}, return={self.total_return})>"
        )

    @classmethod
    def get_portfolio_backtests(
        cls, session: Session, portfolio_name: str | None = None, limit: int = 10
    ) -> Sequence[BacktestPortfolio]:
        """Get portfolio backtests, optionally filtered by name."""
        query = session.query(cls).order_by(cls.backtest_date.desc())
        if portfolio_name:
            query = query.filter(cls.portfolio_name == portfolio_name)
        return query.limit(limit).all()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "portfolio_backtest_id": str(self.portfolio_backtest_id),
            "portfolio_name": self.portfolio_name,
            "symbols": self.symbols,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "total_return": float(self.total_return) if self.total_return else 0,
            "sharpe_ratio": float(self.sharpe_ratio) if self.sharpe_ratio else 0,
            "max_drawdown": float(self.max_drawdown) if self.max_drawdown else 0,
            "status": self.status,
        }
