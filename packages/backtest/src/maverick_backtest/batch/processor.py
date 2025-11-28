"""
Batch Processing for Backtesting.

Provides batch processing capabilities for running multiple backtests
in parallel, parameter optimization, and strategy validation.
"""

import asyncio
import gc
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, runtime_checkable

import numpy as np

logger = logging.getLogger(__name__)


@runtime_checkable
class CacheManagerProtocol(Protocol):
    """Protocol for cache managers."""

    def get(self, key: str) -> Any | None:
        """Get cached value."""
        ...

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set cached value."""
        ...


@runtime_checkable
class BacktestEngineProtocol(Protocol):
    """Protocol for backtest engine."""

    async def run_backtest(
        self,
        symbol: str,
        strategy_type: str,
        parameters: dict[str, Any],
        start_date: str,
        end_date: str,
        initial_capital: float,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Run a single backtest."""
        ...


@dataclass
class ExecutionContext:
    """Context for strategy execution."""

    strategy_id: str
    symbol: str
    strategy_type: str
    parameters: dict[str, Any]
    start_date: str
    end_date: str
    initial_capital: float = 10000.0
    fees: float = 0.001
    slippage: float = 0.001
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of strategy execution."""

    context: ExecutionContext
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None
    execution_time: float = 0.0


class BatchProcessor:
    """
    Batch processor for running multiple backtests in parallel.

    Provides methods for:
    - Running batch backtests
    - Parameter optimization
    - Strategy validation
    """

    def __init__(
        self,
        engine: BacktestEngineProtocol,
        cache_manager: CacheManagerProtocol | None = None,
        enable_memory_profiling: bool = False,
    ):
        """
        Initialize batch processor.

        Args:
            engine: Backtest engine instance
            cache_manager: Optional cache manager
            enable_memory_profiling: Enable memory profiling
        """
        self.engine = engine
        self.cache_manager = cache_manager
        self.enable_memory_profiling = enable_memory_profiling

    async def run_batch_backtest(
        self,
        batch_configs: list[dict[str, Any]],
        max_workers: int = 6,
        chunk_size: int = 10,
        validate_data: bool = True,
        fail_fast: bool = False,
    ) -> dict[str, Any]:
        """
        Run multiple backtest strategies in parallel.

        Args:
            batch_configs: List of backtest configurations
            max_workers: Maximum concurrent workers
            chunk_size: Configs to process per batch
            validate_data: Whether to validate input
            fail_fast: Stop on first failure

        Returns:
            Dictionary with batch results and summary
        """
        start_time = time.time()
        batch_id = f"batch_{int(start_time)}"

        logger.info(
            f"Starting batch backtest {batch_id} with {len(batch_configs)} configurations"
        )

        # Validate configurations
        if validate_data:
            validation_errors = self._validate_batch_configs(batch_configs, fail_fast)
            if validation_errors and fail_fast:
                raise ValueError(f"Batch validation failed: {'; '.join(validation_errors)}")

        # Convert to execution contexts
        contexts = [
            ExecutionContext(
                strategy_id=f"{batch_id}_strategy_{i}",
                symbol=config["symbol"],
                strategy_type=config["strategy_type"],
                parameters=config["parameters"],
                start_date=config["start_date"],
                end_date=config["end_date"],
                initial_capital=config.get("initial_capital", 10000.0),
                fees=config.get("fees", 0.001),
                slippage=config.get("slippage", 0.001),
            )
            for i, config in enumerate(batch_configs)
        ]

        # Process in chunks
        all_results: list[ExecutionResult] = []
        successful_results: list[ExecutionResult] = []
        failed_results: list[ExecutionResult] = []

        semaphore = asyncio.BoundedSemaphore(max_workers)

        for chunk_start in range(0, len(contexts), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(contexts))
            chunk_contexts = contexts[chunk_start:chunk_end]

            logger.info(
                f"Processing chunk {chunk_start // chunk_size + 1} ({len(chunk_contexts)} items)"
            )

            # Execute chunk in parallel
            tasks = [
                self._execute_with_semaphore(semaphore, ctx)
                for ctx in chunk_contexts
            ]
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

            for ctx, result in zip(chunk_contexts, chunk_results):
                if isinstance(result, Exception):
                    exec_result = ExecutionResult(
                        context=ctx,
                        success=False,
                        error=str(result),
                    )
                    failed_results.append(exec_result)
                    if fail_fast:
                        break
                else:
                    all_results.append(result)
                    if result.success:
                        successful_results.append(result)
                    else:
                        failed_results.append(result)
                        if fail_fast:
                            break

            # Memory cleanup between chunks
            if self.enable_memory_profiling:
                gc.collect()

            if fail_fast and failed_results:
                break

        # Calculate summary
        total_execution_time = time.time() - start_time
        success_rate = len(successful_results) / len(all_results) if all_results else 0.0

        summary = {
            "batch_id": batch_id,
            "total_configs": len(batch_configs),
            "successful": len(successful_results),
            "failed": len(failed_results),
            "success_rate": success_rate,
            "total_execution_time": total_execution_time,
            "avg_execution_time": total_execution_time / len(all_results)
            if all_results
            else 0.0,
        }

        logger.info(f"Batch backtest {batch_id} completed: {summary}")

        return {
            "batch_id": batch_id,
            "summary": summary,
            "successful_results": [r.result for r in successful_results if r.result],
            "failed_results": [
                {
                    "strategy_id": r.context.strategy_id,
                    "symbol": r.context.symbol,
                    "strategy_type": r.context.strategy_type,
                    "error": r.error,
                }
                for r in failed_results
            ],
        }

    async def _execute_with_semaphore(
        self,
        semaphore: asyncio.BoundedSemaphore,
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Execute a single backtest with semaphore control."""
        async with semaphore:
            return await self._execute_single(context)

    async def _execute_single(self, context: ExecutionContext) -> ExecutionResult:
        """Execute a single backtest."""
        start_time = time.time()
        try:
            result = await self.engine.run_backtest(
                symbol=context.symbol,
                strategy_type=context.strategy_type,
                parameters=context.parameters,
                start_date=context.start_date,
                end_date=context.end_date,
                initial_capital=context.initial_capital,
            )

            return ExecutionResult(
                context=context,
                success=True,
                result=result,
                execution_time=time.time() - start_time,
            )

        except Exception as e:
            logger.error(f"Backtest failed for {context.strategy_id}: {e}")
            return ExecutionResult(
                context=context,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
            )

    async def batch_optimize_parameters(
        self,
        optimization_configs: list[dict[str, Any]],
        max_workers: int = 4,
        optimization_method: str = "grid_search",
        max_iterations: int = 100,
    ) -> dict[str, Any]:
        """
        Optimize strategy parameters for multiple configurations.

        Args:
            optimization_configs: List of optimization configurations
            max_workers: Maximum concurrent workers
            optimization_method: Optimization method
            max_iterations: Max iterations per config

        Returns:
            Optimization results dictionary
        """
        start_time = time.time()
        batch_id = f"optimize_batch_{int(start_time)}"

        logger.info(
            f"Starting batch optimization {batch_id} with {len(optimization_configs)} configurations"
        )

        # Process optimizations in parallel
        semaphore = asyncio.BoundedSemaphore(max_workers)

        async def limited_optimization(config: dict, opt_id: str) -> dict[str, Any]:
            async with semaphore:
                return await self._run_single_optimization(
                    config, opt_id, optimization_method, max_iterations
                )

        tasks = [
            limited_optimization(config, f"{batch_id}_opt_{i}")
            for i, config in enumerate(optimization_configs)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_optimizations = []
        failed_optimizations = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_optimizations.append({
                    "config_index": i,
                    "config": optimization_configs[i],
                    "error": str(result),
                })
            else:
                successful_optimizations.append(result)

        total_execution_time = time.time() - start_time
        success_rate = (
            len(successful_optimizations) / len(optimization_configs)
            if optimization_configs
            else 0.0
        )

        summary = {
            "batch_id": batch_id,
            "total_optimizations": len(optimization_configs),
            "successful": len(successful_optimizations),
            "failed": len(failed_optimizations),
            "success_rate": success_rate,
            "total_execution_time": total_execution_time,
            "optimization_method": optimization_method,
            "max_iterations": max_iterations,
        }

        logger.info(f"Batch optimization {batch_id} completed: {summary}")

        return {
            "batch_id": batch_id,
            "summary": summary,
            "successful_optimizations": successful_optimizations,
            "failed_optimizations": failed_optimizations,
        }

    async def batch_validate_strategies(
        self,
        validation_configs: list[dict[str, Any]],
        validation_start_date: str,
        validation_end_date: str,
        max_workers: int = 6,
    ) -> dict[str, Any]:
        """
        Validate strategies against out-of-sample data.

        Args:
            validation_configs: Configurations with optimized parameters
            validation_start_date: Validation period start
            validation_end_date: Validation period end
            max_workers: Maximum concurrent workers

        Returns:
            Validation results dictionary
        """
        start_time = time.time()
        batch_id = f"validate_batch_{int(start_time)}"

        logger.info(
            f"Starting batch validation {batch_id} with {len(validation_configs)} strategies"
        )

        # Create validation backtest configs
        validation_batch_configs = [
            {
                "symbol": config["symbol"],
                "strategy_type": config["strategy_type"],
                "parameters": config.get(
                    "optimized_parameters", config.get("parameters", {})
                ),
                "start_date": validation_start_date,
                "end_date": validation_end_date,
                "initial_capital": config.get("initial_capital", 10000.0),
                "fees": config.get("fees", 0.001),
                "slippage": config.get("slippage", 0.001),
            }
            for config in validation_configs
        ]

        # Run validation backtests
        validation_results = await self.run_batch_backtest(
            validation_batch_configs,
            max_workers=max_workers,
            validate_data=True,
            fail_fast=False,
        )

        # Calculate validation metrics
        validation_metrics = self._calculate_validation_metrics(
            validation_configs, validation_results["successful_results"]
        )

        total_execution_time = time.time() - start_time

        return {
            "batch_id": batch_id,
            "validation_period": {
                "start_date": validation_start_date,
                "end_date": validation_end_date,
            },
            "summary": {
                "total_strategies": len(validation_configs),
                "validated_strategies": len(validation_results["successful_results"]),
                "validation_success_rate": len(validation_results["successful_results"])
                / len(validation_configs)
                if validation_configs
                else 0.0,
                "total_execution_time": total_execution_time,
            },
            "validation_results": validation_results["successful_results"],
            "validation_metrics": validation_metrics,
            "failed_validations": validation_results["failed_results"],
        }

    def _validate_batch_configs(
        self,
        configs: list[dict[str, Any]],
        fail_fast: bool,
    ) -> list[str]:
        """Validate batch configurations."""
        errors = []
        required_fields = ["symbol", "strategy_type", "parameters", "start_date", "end_date"]

        for i, config in enumerate(configs):
            for field in required_fields:
                if field not in config:
                    errors.append(f"Config {i}: Missing required field '{field}'")
                    if fail_fast:
                        return errors

        return errors

    async def _run_single_optimization(
        self,
        config: dict[str, Any],
        optimization_id: str,
        method: str,
        max_iterations: int,
    ) -> dict[str, Any]:
        """Run optimization for a single configuration."""
        try:
            symbol = config["symbol"]
            strategy_type = config["strategy_type"]
            parameter_ranges = config["parameter_ranges"]
            start_date = config["start_date"]
            end_date = config["end_date"]
            optimization_metric = config.get("optimization_metric", "sharpe_ratio")
            initial_capital = config.get("initial_capital", 10000.0)

            # Simple parameter selection (middle of range)
            best_params = {}
            for param, ranges in parameter_ranges.items():
                if isinstance(ranges, list) and len(ranges) >= 2:
                    best_params[param] = ranges[len(ranges) // 2]
                elif isinstance(ranges, dict):
                    if "min" in ranges and "max" in ranges:
                        best_params[param] = (ranges["min"] + ranges["max"]) / 2

            # Run backtest with selected parameters
            backtest_result = await self.engine.run_backtest(
                symbol=symbol,
                strategy_type=strategy_type,
                parameters=best_params,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
            )

            best_score = backtest_result.get("metrics", {}).get(optimization_metric, 0.0)

            return {
                "optimization_id": optimization_id,
                "symbol": symbol,
                "strategy_type": strategy_type,
                "optimized_parameters": best_params,
                "best_score": best_score,
                "optimization_history": [
                    {"parameters": best_params, "score": best_score}
                ],
                "execution_time": 0.0,
            }

        except Exception as e:
            logger.error(f"Optimization failed for {optimization_id}: {e}")
            raise

    def _calculate_validation_metrics(
        self,
        original_configs: list[dict[str, Any]],
        validation_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Calculate validation metrics comparing in-sample vs out-of-sample."""
        metrics: dict[str, Any] = {
            "strategy_comparisons": [],
            "aggregate_metrics": {
                "avg_in_sample_sharpe": 0.0,
                "avg_out_of_sample_sharpe": 0.0,
                "sharpe_degradation": 0.0,
                "strategies_with_positive_validation": 0,
            },
        }

        if not original_configs or not validation_results:
            return metrics

        sharpe_ratios_in_sample = []
        sharpe_ratios_out_of_sample = []

        for i, (original, validation) in enumerate(
            zip(original_configs, validation_results, strict=False)
        ):
            in_sample_sharpe = original.get("best_score", 0.0)
            out_of_sample_sharpe = validation.get("metrics", {}).get("sharpe_ratio", 0.0)

            strategy_comparison = {
                "strategy_index": i,
                "symbol": original["symbol"],
                "strategy_type": original["strategy_type"],
                "in_sample_sharpe": in_sample_sharpe,
                "out_of_sample_sharpe": out_of_sample_sharpe,
                "sharpe_degradation": in_sample_sharpe - out_of_sample_sharpe,
                "validation_success": out_of_sample_sharpe > 0,
            }

            metrics["strategy_comparisons"].append(strategy_comparison)
            sharpe_ratios_in_sample.append(in_sample_sharpe)
            sharpe_ratios_out_of_sample.append(out_of_sample_sharpe)

        if sharpe_ratios_in_sample and sharpe_ratios_out_of_sample:
            metrics["aggregate_metrics"]["avg_in_sample_sharpe"] = float(
                np.mean(sharpe_ratios_in_sample)
            )
            metrics["aggregate_metrics"]["avg_out_of_sample_sharpe"] = float(
                np.mean(sharpe_ratios_out_of_sample)
            )
            metrics["aggregate_metrics"]["sharpe_degradation"] = (
                metrics["aggregate_metrics"]["avg_in_sample_sharpe"]
                - metrics["aggregate_metrics"]["avg_out_of_sample_sharpe"]
            )
            metrics["aggregate_metrics"]["strategies_with_positive_validation"] = sum(
                1 for comp in metrics["strategy_comparisons"] if comp["validation_success"]
            )

        return metrics


__all__ = [
    "ExecutionContext",
    "ExecutionResult",
    "BatchProcessor",
    "CacheManagerProtocol",
    "BacktestEngineProtocol",
]
