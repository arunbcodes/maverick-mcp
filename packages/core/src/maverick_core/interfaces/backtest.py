"""
Backtesting interfaces.

This module defines abstract interfaces for backtesting operations.
"""

from typing import Any, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class IBacktestEngine(Protocol):
    """
    Interface for backtesting engine.

    This interface defines the contract for running backtests,
    optimizing strategies, and analyzing results.

    Implemented by: maverick-backtest (VectorBTEngine)
    """

    async def run_backtest(
        self,
        symbol: str,
        strategy: str,
        start_date: str | None = None,
        end_date: str | None = None,
        initial_capital: float = 10000,
        **strategy_params: Any,
    ) -> dict[str, Any]:
        """
        Run backtest with specified strategy.

        Args:
            symbol: Stock ticker
            strategy: Strategy name (e.g., "sma_cross", "rsi", "macd")
            start_date: Backtest start date (YYYY-MM-DD)
            end_date: Backtest end date (YYYY-MM-DD)
            initial_capital: Starting capital
            **strategy_params: Strategy-specific parameters

        Returns:
            Dictionary with:
            - metrics: Performance metrics (sharpe, sortino, max_drawdown, etc.)
            - trades: List of trades executed
            - equity_curve: Equity values over time
            - drawdown: Drawdown series
            - positions: Position history
            - summary: Human-readable summary
        """
        ...

    async def optimize_strategy(
        self,
        symbol: str,
        strategy: str,
        param_ranges: dict[str, list[Any]],
        metric: str = "sharpe_ratio",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Optimize strategy parameters.

        Args:
            symbol: Stock ticker
            strategy: Strategy name
            param_ranges: Dictionary of parameter ranges to test
            metric: Metric to optimize ("sharpe_ratio", "total_return", "win_rate")
            start_date: Optimization start date
            end_date: Optimization end date

        Returns:
            Dictionary with:
            - best_params: Optimal parameters
            - best_metric: Best metric value
            - all_results: All parameter combinations tested
            - optimization_time: Time taken
        """
        ...

    async def compare_strategies(
        self,
        symbol: str,
        strategies: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
        initial_capital: float = 10000,
    ) -> dict[str, Any]:
        """
        Compare multiple strategies.

        Args:
            symbol: Stock ticker
            strategies: List of strategy names
            start_date: Comparison start date
            end_date: Comparison end date
            initial_capital: Starting capital

        Returns:
            Dictionary with:
            - results: Results for each strategy
            - ranking: Strategies ranked by performance
            - comparison_metrics: Side-by-side metrics comparison
        """
        ...

    async def walk_forward_analysis(
        self,
        symbol: str,
        strategy: str,
        window_size: int = 252,
        step_size: int = 63,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Perform walk-forward analysis.

        Args:
            symbol: Stock ticker
            strategy: Strategy name
            window_size: Training window size in trading days
            step_size: Step size for rolling window
            start_date: Analysis start date
            end_date: Analysis end date

        Returns:
            Dictionary with:
            - windows: Results for each window
            - aggregate_metrics: Aggregated performance
            - robustness_score: Strategy robustness score
        """
        ...

    async def monte_carlo_simulation(
        self,
        symbol: str,
        strategy: str,
        num_simulations: int = 1000,
        **strategy_params: Any,
    ) -> dict[str, Any]:
        """
        Run Monte Carlo simulation.

        Args:
            symbol: Stock ticker
            strategy: Strategy name
            num_simulations: Number of simulations
            **strategy_params: Strategy parameters

        Returns:
            Dictionary with:
            - simulations: Simulation results
            - confidence_intervals: Confidence intervals
            - var: Value at Risk estimates
            - expected_return: Expected return distribution
        """
        ...

    def get_available_strategies(self) -> list[dict[str, Any]]:
        """
        Get list of available strategies.

        Returns:
            List of strategy info dictionaries with:
            - name: Strategy name
            - description: Strategy description
            - parameters: Available parameters with defaults
            - category: Strategy category
        """
        ...


@runtime_checkable
class IStrategy(Protocol):
    """
    Interface for trading strategies.

    This interface defines the contract for individual trading strategies
    that can be used with the backtest engine.

    Implemented by: maverick-backtest (various strategy classes)
    """

    @property
    def name(self) -> str:
        """Strategy name."""
        ...

    @property
    def description(self) -> str:
        """Strategy description."""
        ...

    @property
    def parameters(self) -> dict[str, Any]:
        """
        Strategy parameters with defaults.

        Returns:
            Dictionary with parameter names and default values
        """
        ...

    @property
    def category(self) -> str:
        """
        Strategy category.

        Returns:
            Category string (e.g., "trend", "momentum", "mean_reversion", "ml")
        """
        ...

    def generate_signals(
        self,
        data: pd.DataFrame,
        **params: Any,
    ) -> pd.Series:
        """
        Generate trading signals.

        Args:
            data: OHLCV DataFrame
            **params: Strategy parameters

        Returns:
            Series with signals: 1 (buy), -1 (sell), 0 (hold)
        """
        ...

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Validate and normalize strategy parameters.

        Args:
            params: Parameters to validate

        Returns:
            Validated parameters with defaults applied

        Raises:
            ValidationError: If parameters are invalid
        """
        ...

    def get_param_ranges(self) -> dict[str, tuple[Any, Any, Any]]:
        """
        Get parameter ranges for optimization.

        Returns:
            Dictionary with parameter name -> (min, max, step)
        """
        ...
