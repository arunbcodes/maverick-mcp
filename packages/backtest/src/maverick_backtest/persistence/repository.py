"""
Backtest Persistence Repository.

Provides database operations for backtest results using dependency injection.
The repository pattern allows different database implementations.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Callable
from uuid import UUID, uuid4

import pandas as pd

from maverick_backtest.persistence.protocols import (
    BacktestPersistenceRepository,
    DatabaseSessionProtocol,
)

logger = logging.getLogger(__name__)


class BacktestPersistenceError(Exception):
    """Custom exception for backtest persistence operations."""

    pass


class SQLAlchemyBacktestRepository(BacktestPersistenceRepository):
    """
    SQLAlchemy-based implementation of backtest persistence.

    Uses dependency injection for session factory and model classes.
    """

    def __init__(
        self,
        session_factory: Callable[[], DatabaseSessionProtocol],
        backtest_result_model: type,
        backtest_trade_model: type,
        optimization_result_model: type,
        walk_forward_test_model: type,
    ):
        """
        Initialize repository with injected dependencies.

        Args:
            session_factory: Callable that returns a database session
            backtest_result_model: BacktestResult model class
            backtest_trade_model: BacktestTrade model class
            optimization_result_model: OptimizationResult model class
            walk_forward_test_model: WalkForwardTest model class
        """
        self._session_factory = session_factory
        self._BacktestResult = backtest_result_model
        self._BacktestTrade = backtest_trade_model
        self._OptimizationResult = optimization_result_model
        self._WalkForwardTest = walk_forward_test_model
        self._session: DatabaseSessionProtocol | None = None
        self._owns_session = False

    def __enter__(self):
        """Context manager entry."""
        self._session = self._session_factory()
        self._owns_session = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with proper cleanup."""
        if self._owns_session and self._session:
            if exc_type is None:
                self._session.commit()
            else:
                self._session.rollback()
            self._session.close()
            self._session = None

    @property
    def session(self) -> DatabaseSessionProtocol:
        """Get current session, creating one if needed."""
        if self._session is None:
            self._session = self._session_factory()
            self._owns_session = True
        return self._session

    def save_backtest_result(
        self,
        vectorbt_results: dict[str, Any],
        execution_time: float | None = None,
        notes: str | None = None,
    ) -> str:
        """Save VectorBT backtest results to database."""
        try:
            # Extract basic metadata
            symbol = vectorbt_results.get("symbol", "").upper()
            strategy_type = vectorbt_results.get("strategy", "")
            parameters = vectorbt_results.get("parameters", {})
            metrics = vectorbt_results.get("metrics", {})

            if not symbol or not strategy_type:
                raise BacktestPersistenceError("Symbol and strategy type are required")

            # Create backtest result record
            backtest_result = self._BacktestResult(
                backtest_id=uuid4(),
                symbol=symbol,
                strategy_type=strategy_type,
                backtest_date=datetime.utcnow(),
                # Date range
                start_date=pd.to_datetime(vectorbt_results.get("start_date")).date(),
                end_date=pd.to_datetime(vectorbt_results.get("end_date")).date(),
                initial_capital=Decimal(
                    str(vectorbt_results.get("initial_capital", 10000))
                ),
                # Strategy parameters
                parameters=parameters,
                # Performance metrics
                total_return=self._safe_decimal(metrics.get("total_return")),
                annualized_return=self._safe_decimal(metrics.get("annualized_return")),
                sharpe_ratio=self._safe_decimal(metrics.get("sharpe_ratio")),
                sortino_ratio=self._safe_decimal(metrics.get("sortino_ratio")),
                calmar_ratio=self._safe_decimal(metrics.get("calmar_ratio")),
                # Risk metrics
                max_drawdown=self._safe_decimal(metrics.get("max_drawdown")),
                max_drawdown_duration=metrics.get("max_drawdown_duration"),
                volatility=self._safe_decimal(metrics.get("volatility")),
                downside_volatility=self._safe_decimal(
                    metrics.get("downside_volatility")
                ),
                # Trade statistics
                total_trades=metrics.get("total_trades", 0),
                winning_trades=metrics.get("winning_trades", 0),
                losing_trades=metrics.get("losing_trades", 0),
                win_rate=self._safe_decimal(metrics.get("win_rate")),
                # P&L statistics
                profit_factor=self._safe_decimal(metrics.get("profit_factor")),
                average_win=self._safe_decimal(metrics.get("average_win")),
                average_loss=self._safe_decimal(metrics.get("average_loss")),
                largest_win=self._safe_decimal(metrics.get("largest_win")),
                largest_loss=self._safe_decimal(metrics.get("largest_loss")),
                # Portfolio values
                final_portfolio_value=self._safe_decimal(metrics.get("final_value")),
                peak_portfolio_value=self._safe_decimal(metrics.get("peak_value")),
                # Market analysis
                beta=self._safe_decimal(metrics.get("beta")),
                alpha=self._safe_decimal(metrics.get("alpha")),
                # Time series data
                equity_curve=vectorbt_results.get("equity_curve"),
                drawdown_series=vectorbt_results.get("drawdown_series"),
                # Execution metadata
                execution_time_seconds=Decimal(str(execution_time))
                if execution_time
                else None,
                data_points=len(vectorbt_results.get("equity_curve", [])),
                # Status
                status="completed",
                notes=notes,
            )

            self.session.add(backtest_result)
            self.session.flush()  # Get the ID without committing

            # Save individual trades if available
            trades_data = vectorbt_results.get("trades", [])
            if trades_data:
                self._save_trades(backtest_result.backtest_id, trades_data)

            self.session.commit()
            logger.info(f"Saved backtest result: {backtest_result.backtest_id}")

            return str(backtest_result.backtest_id)

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving backtest: {e}")
            raise BacktestPersistenceError(f"Failed to save backtest: {e}") from e

    def _save_trades(
        self, backtest_id: UUID, trades_data: list[dict[str, Any]]
    ) -> None:
        """Save individual trade records."""
        try:
            trades = []
            for i, trade in enumerate(trades_data, 1):
                trade_record = self._BacktestTrade(
                    trade_id=uuid4(),
                    backtest_id=backtest_id,
                    trade_number=i,
                    # Entry details
                    entry_date=pd.to_datetime(trade.get("entry_date")).date(),
                    entry_price=self._safe_decimal(trade.get("entry_price")),
                    entry_time=pd.to_datetime(trade.get("entry_time"))
                    if trade.get("entry_time")
                    else None,
                    # Exit details
                    exit_date=pd.to_datetime(trade.get("exit_date")).date()
                    if trade.get("exit_date")
                    else None,
                    exit_price=self._safe_decimal(trade.get("exit_price")),
                    exit_time=pd.to_datetime(trade.get("exit_time"))
                    if trade.get("exit_time")
                    else None,
                    # Position details
                    position_size=self._safe_decimal(trade.get("position_size")),
                    direction=trade.get("direction", "long"),
                    # P&L
                    pnl=self._safe_decimal(trade.get("pnl")),
                    pnl_percent=self._safe_decimal(trade.get("pnl_percent")),
                    # Risk metrics
                    mae=self._safe_decimal(trade.get("mae")),
                    mfe=self._safe_decimal(trade.get("mfe")),
                    # Duration
                    duration_days=trade.get("duration_days"),
                    duration_hours=self._safe_decimal(trade.get("duration_hours")),
                    # Exit details
                    exit_reason=trade.get("exit_reason"),
                    fees_paid=self._safe_decimal(trade.get("fees_paid")),
                    slippage_cost=self._safe_decimal(trade.get("slippage_cost")),
                )
                trades.append(trade_record)

            self.session.add_all(trades)
            logger.info(f"Saved {len(trades)} trades for backtest {backtest_id}")

        except Exception as e:
            logger.error(f"Error saving trades: {e}")
            raise

    def get_backtest_by_id(self, backtest_id: str) -> Any | None:
        """Retrieve a backtest by ID."""
        try:
            if isinstance(backtest_id, str):
                backtest_uuid = UUID(backtest_id)
            else:
                backtest_uuid = backtest_id

            return (
                self.session.query(self._BacktestResult)
                .filter(self._BacktestResult.backtest_id == backtest_uuid)
                .first()
            )
        except Exception as e:
            logger.error(f"Error retrieving backtest {backtest_id}: {e}")
            return None

    def get_backtests_by_symbol(
        self,
        symbol: str,
        strategy_type: str | None = None,
        limit: int = 10,
    ) -> list[Any]:
        """Get backtests for a specific symbol."""
        try:
            from sqlalchemy import desc

            query = self.session.query(self._BacktestResult).filter(
                self._BacktestResult.symbol == symbol.upper()
            )

            if strategy_type:
                query = query.filter(self._BacktestResult.strategy_type == strategy_type)

            return (
                query.order_by(desc(self._BacktestResult.backtest_date))
                .limit(limit)
                .all()
            )

        except Exception as e:
            logger.error(f"Error retrieving backtests for {symbol}: {e}")
            return []

    def get_best_performing_strategies(
        self,
        metric: str = "sharpe_ratio",
        min_trades: int = 10,
        limit: int = 20,
    ) -> list[Any]:
        """Get best performing backtests by metric."""
        try:
            from sqlalchemy import desc

            metric_column = getattr(
                self._BacktestResult, metric, self._BacktestResult.sharpe_ratio
            )

            return (
                self.session.query(self._BacktestResult)
                .filter(
                    self._BacktestResult.status == "completed",
                    self._BacktestResult.total_trades >= min_trades,
                    metric_column.isnot(None),
                )
                .order_by(desc(metric_column))
                .limit(limit)
                .all()
            )

        except Exception as e:
            logger.error(f"Error retrieving best performing strategies: {e}")
            return []

    def compare_strategies(
        self,
        backtest_ids: list[str],
        metrics: list[str] | None = None,
    ) -> dict[str, Any]:
        """Compare multiple backtests."""
        if not metrics:
            metrics = [
                "total_return",
                "sharpe_ratio",
                "max_drawdown",
                "win_rate",
                "profit_factor",
                "total_trades",
            ]

        try:
            uuid_list = [UUID(bt_id) if isinstance(bt_id, str) else bt_id for bt_id in backtest_ids]

            backtests = (
                self.session.query(self._BacktestResult)
                .filter(self._BacktestResult.backtest_id.in_(uuid_list))
                .all()
            )

            if not backtests:
                return {"error": "No backtests found"}

            comparison = {"backtests": [], "summary": {}, "rankings": {}}

            for bt in backtests:
                bt_data = {
                    "backtest_id": str(bt.backtest_id),
                    "symbol": bt.symbol,
                    "strategy": bt.strategy_type,
                    "date": bt.backtest_date.isoformat(),
                    "metrics": {},
                }

                for metric in metrics:
                    value = getattr(bt, metric, None)
                    bt_data["metrics"][metric] = float(value) if value else None

                comparison["backtests"].append(bt_data)

            # Calculate rankings
            for metric in metrics:
                metric_values = [
                    (bt["backtest_id"], bt["metrics"].get(metric))
                    for bt in comparison["backtests"]
                    if bt["metrics"].get(metric) is not None
                ]

                if metric_values:
                    reverse_sort = metric != "max_drawdown"
                    sorted_values = sorted(
                        metric_values, key=lambda x: x[1], reverse=reverse_sort
                    )

                    comparison["rankings"][metric] = [
                        {"backtest_id": bt_id, "value": value, "rank": i + 1}
                        for i, (bt_id, value) in enumerate(sorted_values)
                    ]

            comparison["summary"] = {
                "total_backtests": len(backtests),
                "date_range": {
                    "earliest": min(bt.backtest_date for bt in backtests).isoformat(),
                    "latest": max(bt.backtest_date for bt in backtests).isoformat(),
                },
            }

            return comparison

        except Exception as e:
            logger.error(f"Error comparing strategies: {e}")
            return {"error": f"Database error: {e}"}

    def save_optimization_results(
        self,
        backtest_id: str,
        optimization_results: list[dict[str, Any]],
        objective_function: str = "sharpe_ratio",
    ) -> int:
        """Save parameter optimization results."""
        try:
            backtest_uuid = UUID(backtest_id) if isinstance(backtest_id, str) else backtest_id

            optimization_records = []

            for i, result in enumerate(optimization_results, 1):
                record = self._OptimizationResult(
                    optimization_id=uuid4(),
                    backtest_id=backtest_uuid,
                    parameter_set=i,
                    parameters=result.get("parameters", {}),
                    objective_function=objective_function,
                    objective_value=self._safe_decimal(result.get("objective_value")),
                    total_return=self._safe_decimal(result.get("total_return")),
                    sharpe_ratio=self._safe_decimal(result.get("sharpe_ratio")),
                    max_drawdown=self._safe_decimal(result.get("max_drawdown")),
                    win_rate=self._safe_decimal(result.get("win_rate")),
                    profit_factor=self._safe_decimal(result.get("profit_factor")),
                    total_trades=result.get("total_trades"),
                    rank=result.get("rank", i),
                    is_statistically_significant=result.get(
                        "is_statistically_significant", False
                    ),
                    p_value=self._safe_decimal(result.get("p_value")),
                )
                optimization_records.append(record)

            self.session.add_all(optimization_records)
            self.session.commit()

            logger.info(f"Saved {len(optimization_records)} optimization results")
            return len(optimization_records)

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving optimization results: {e}")
            raise BacktestPersistenceError(f"Failed to save optimization results: {e}") from e

    def save_walk_forward_test(
        self,
        parent_backtest_id: str,
        walk_forward_data: dict[str, Any],
    ) -> str:
        """Save walk-forward test results."""
        try:
            parent_uuid = (
                UUID(parent_backtest_id)
                if isinstance(parent_backtest_id, str)
                else parent_backtest_id
            )

            wf_test = self._WalkForwardTest(
                walk_forward_id=uuid4(),
                parent_backtest_id=parent_uuid,
                window_size_months=walk_forward_data.get("window_size_months"),
                step_size_months=walk_forward_data.get("step_size_months"),
                # Time periods
                training_start=pd.to_datetime(
                    walk_forward_data.get("training_start")
                ).date(),
                training_end=pd.to_datetime(
                    walk_forward_data.get("training_end")
                ).date(),
                test_period_start=pd.to_datetime(
                    walk_forward_data.get("test_period_start")
                ).date(),
                test_period_end=pd.to_datetime(
                    walk_forward_data.get("test_period_end")
                ).date(),
                # Results
                optimal_parameters=walk_forward_data.get("optimal_parameters"),
                training_performance=self._safe_decimal(
                    walk_forward_data.get("training_performance")
                ),
                out_of_sample_return=self._safe_decimal(
                    walk_forward_data.get("out_of_sample_return")
                ),
                out_of_sample_sharpe=self._safe_decimal(
                    walk_forward_data.get("out_of_sample_sharpe")
                ),
                out_of_sample_drawdown=self._safe_decimal(
                    walk_forward_data.get("out_of_sample_drawdown")
                ),
                out_of_sample_trades=walk_forward_data.get("out_of_sample_trades"),
                # Performance analysis
                performance_ratio=self._safe_decimal(
                    walk_forward_data.get("performance_ratio")
                ),
                degradation_factor=self._safe_decimal(
                    walk_forward_data.get("degradation_factor")
                ),
                is_profitable=walk_forward_data.get("is_profitable"),
                is_statistically_significant=walk_forward_data.get(
                    "is_statistically_significant", False
                ),
            )

            self.session.add(wf_test)
            self.session.commit()

            logger.info(f"Saved walk-forward test: {wf_test.walk_forward_id}")
            return str(wf_test.walk_forward_id)

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving walk-forward test: {e}")
            raise BacktestPersistenceError(f"Failed to save walk-forward test: {e}") from e

    def get_backtest_performance_summary(
        self,
        symbol: str | None = None,
        strategy_type: str | None = None,
        days_back: int = 30,
    ) -> dict[str, Any]:
        """Get performance summary of recent backtests."""
        try:
            from sqlalchemy import desc

            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            query = self.session.query(self._BacktestResult).filter(
                self._BacktestResult.backtest_date >= cutoff_date,
                self._BacktestResult.status == "completed",
            )

            if symbol:
                query = query.filter(self._BacktestResult.symbol == symbol.upper())
            if strategy_type:
                query = query.filter(self._BacktestResult.strategy_type == strategy_type)

            backtests = query.all()

            if not backtests:
                return {"message": "No backtests found in the specified period"}

            returns = [float(bt.total_return) for bt in backtests if bt.total_return]
            sharpe_ratios = [
                float(bt.sharpe_ratio) for bt in backtests if bt.sharpe_ratio
            ]
            win_rates = [float(bt.win_rate) for bt in backtests if bt.win_rate]

            summary = {
                "period": f"Last {days_back} days",
                "total_backtests": len(backtests),
                "performance_metrics": {
                    "average_return": sum(returns) / len(returns) if returns else 0,
                    "best_return": max(returns) if returns else 0,
                    "worst_return": min(returns) if returns else 0,
                    "average_sharpe": sum(sharpe_ratios) / len(sharpe_ratios)
                    if sharpe_ratios
                    else 0,
                    "average_win_rate": sum(win_rates) / len(win_rates)
                    if win_rates
                    else 0,
                },
                "strategy_breakdown": {},
                "symbol_breakdown": {},
            }

            # Group by strategy
            strategy_groups: dict[str, list] = {}
            for bt in backtests:
                strategy = bt.strategy_type
                if strategy not in strategy_groups:
                    strategy_groups[strategy] = []
                strategy_groups[strategy].append(bt)

            for strategy, strategy_backtests in strategy_groups.items():
                strategy_returns = [
                    float(bt.total_return)
                    for bt in strategy_backtests
                    if bt.total_return
                ]
                summary["strategy_breakdown"][strategy] = {
                    "count": len(strategy_backtests),
                    "average_return": sum(strategy_returns) / len(strategy_returns)
                    if strategy_returns
                    else 0,
                }

            return summary

        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return {"error": f"Database error: {e}"}

    def delete_backtest(self, backtest_id: str) -> bool:
        """Delete a backtest and associated data."""
        try:
            backtest_uuid = UUID(backtest_id) if isinstance(backtest_id, str) else backtest_id

            backtest = (
                self.session.query(self._BacktestResult)
                .filter(self._BacktestResult.backtest_id == backtest_uuid)
                .first()
            )

            if not backtest:
                logger.warning(f"Backtest {backtest_id} not found")
                return False

            self.session.delete(backtest)
            self.session.commit()

            logger.info(f"Deleted backtest {backtest_id}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting backtest {backtest_id}: {e}")
            return False

    @staticmethod
    def _safe_decimal(value: Any) -> Decimal | None:
        """Safely convert value to Decimal."""
        if value is None:
            return None
        try:
            if isinstance(value, int | float):
                return Decimal(str(value))
            elif isinstance(value, Decimal):
                return value
            else:
                return Decimal(str(float(value)))
        except (ValueError, TypeError, InvalidOperation):
            return None


__all__ = [
    "BacktestPersistenceError",
    "SQLAlchemyBacktestRepository",
]
