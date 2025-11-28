"""
Persistence Protocols - Abstract Interfaces.

Defines abstract interfaces for backtest persistence operations.
These protocols allow the persistence layer to work with any database
implementation that satisfies the interface.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class BacktestResultProtocol(Protocol):
    """Protocol for backtest result objects."""

    backtest_id: UUID
    symbol: str
    strategy_type: str
    backtest_date: datetime
    start_date: Any  # date
    end_date: Any  # date
    initial_capital: Decimal
    parameters: dict[str, Any]
    total_return: Decimal | None
    sharpe_ratio: Decimal | None
    max_drawdown: Decimal | None
    win_rate: Decimal | None
    profit_factor: Decimal | None
    total_trades: int | None
    status: str


@runtime_checkable
class BacktestTradeProtocol(Protocol):
    """Protocol for backtest trade objects."""

    trade_id: UUID
    backtest_id: UUID
    trade_number: int
    entry_date: Any  # date
    entry_price: Decimal | None
    exit_date: Any | None  # date
    exit_price: Decimal | None
    position_size: Decimal | None
    direction: str
    pnl: Decimal | None
    pnl_percent: Decimal | None


@runtime_checkable
class OptimizationResultProtocol(Protocol):
    """Protocol for optimization result objects."""

    optimization_id: UUID
    backtest_id: UUID
    parameter_set: int
    parameters: dict[str, Any]
    objective_function: str
    objective_value: Decimal | None
    total_return: Decimal | None
    sharpe_ratio: Decimal | None
    rank: int | None


@runtime_checkable
class WalkForwardTestProtocol(Protocol):
    """Protocol for walk-forward test objects."""

    walk_forward_id: UUID
    parent_backtest_id: UUID
    window_size_months: int | None
    training_start: Any  # date
    training_end: Any  # date
    test_period_start: Any  # date
    test_period_end: Any  # date
    optimal_parameters: dict[str, Any] | None
    out_of_sample_return: Decimal | None
    out_of_sample_sharpe: Decimal | None


@runtime_checkable
class DatabaseSessionProtocol(Protocol):
    """Protocol for database session objects."""

    def add(self, instance: Any) -> None:
        """Add an instance to the session."""
        ...

    def add_all(self, instances: list[Any]) -> None:
        """Add multiple instances to the session."""
        ...

    def commit(self) -> None:
        """Commit the transaction."""
        ...

    def rollback(self) -> None:
        """Rollback the transaction."""
        ...

    def close(self) -> None:
        """Close the session."""
        ...

    def flush(self) -> None:
        """Flush pending changes."""
        ...

    def query(self, *entities: Any) -> Any:
        """Create a query."""
        ...


class BacktestPersistenceRepository(ABC):
    """
    Abstract base class for backtest persistence operations.

    Implementations can use SQLAlchemy, MongoDB, or any other database.
    """

    @abstractmethod
    def save_backtest_result(
        self,
        vectorbt_results: dict[str, Any],
        execution_time: float | None = None,
        notes: str | None = None,
    ) -> str:
        """
        Save backtest results.

        Args:
            vectorbt_results: Results dictionary from backtest engine
            execution_time: Execution time in seconds
            notes: Optional user notes

        Returns:
            UUID string of the saved backtest
        """
        pass

    @abstractmethod
    def get_backtest_by_id(self, backtest_id: str) -> Any | None:
        """
        Retrieve a backtest by ID.

        Args:
            backtest_id: UUID string of the backtest

        Returns:
            Backtest result or None if not found
        """
        pass

    @abstractmethod
    def get_backtests_by_symbol(
        self,
        symbol: str,
        strategy_type: str | None = None,
        limit: int = 10,
    ) -> list[Any]:
        """
        Get backtests for a specific symbol.

        Args:
            symbol: Stock symbol
            strategy_type: Optional strategy filter
            limit: Maximum number of results

        Returns:
            List of backtest results
        """
        pass

    @abstractmethod
    def get_best_performing_strategies(
        self,
        metric: str = "sharpe_ratio",
        min_trades: int = 10,
        limit: int = 20,
    ) -> list[Any]:
        """
        Get best performing backtests by metric.

        Args:
            metric: Performance metric to sort by
            min_trades: Minimum trades required
            limit: Maximum results

        Returns:
            List of top performing backtest results
        """
        pass

    @abstractmethod
    def compare_strategies(
        self,
        backtest_ids: list[str],
        metrics: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Compare multiple backtests.

        Args:
            backtest_ids: List of backtest UUID strings
            metrics: Metrics to compare

        Returns:
            Comparison results dictionary
        """
        pass

    @abstractmethod
    def save_optimization_results(
        self,
        backtest_id: str,
        optimization_results: list[dict[str, Any]],
        objective_function: str = "sharpe_ratio",
    ) -> int:
        """
        Save parameter optimization results.

        Args:
            backtest_id: Parent backtest UUID
            optimization_results: List of optimization result dicts
            objective_function: Optimization objective

        Returns:
            Number of results saved
        """
        pass

    @abstractmethod
    def save_walk_forward_test(
        self,
        parent_backtest_id: str,
        walk_forward_data: dict[str, Any],
    ) -> str:
        """
        Save walk-forward test results.

        Args:
            parent_backtest_id: Parent backtest UUID
            walk_forward_data: Walk-forward test data

        Returns:
            UUID string of saved walk-forward test
        """
        pass

    @abstractmethod
    def delete_backtest(self, backtest_id: str) -> bool:
        """
        Delete a backtest and associated data.

        Args:
            backtest_id: UUID string of backtest to delete

        Returns:
            True if deleted successfully
        """
        pass


__all__ = [
    "BacktestResultProtocol",
    "BacktestTradeProtocol",
    "OptimizationResultProtocol",
    "WalkForwardTestProtocol",
    "DatabaseSessionProtocol",
    "BacktestPersistenceRepository",
]
