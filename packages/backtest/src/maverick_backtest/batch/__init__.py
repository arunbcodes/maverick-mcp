"""
Batch Processing for Backtesting.

Provides parallel batch execution of backtests, parameter optimization,
and strategy validation.
"""

from maverick_backtest.batch.processor import (
    BacktestEngineProtocol,
    BatchProcessor,
    CacheManagerProtocol,
    ExecutionContext,
    ExecutionResult,
)

__all__ = [
    "ExecutionContext",
    "ExecutionResult",
    "BatchProcessor",
    "CacheManagerProtocol",
    "BacktestEngineProtocol",
]
