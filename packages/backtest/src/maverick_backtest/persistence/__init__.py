"""
Backtesting Persistence.

Database operations for backtest results using repository pattern.
Supports SQLAlchemy and other database implementations through protocols.
"""

from maverick_backtest.persistence.protocols import (
    BacktestPersistenceRepository,
    BacktestResultProtocol,
    BacktestTradeProtocol,
    DatabaseSessionProtocol,
    OptimizationResultProtocol,
    WalkForwardTestProtocol,
)
from maverick_backtest.persistence.repository import (
    BacktestPersistenceError,
    SQLAlchemyBacktestRepository,
)

__all__ = [
    # Protocols
    "BacktestResultProtocol",
    "BacktestTradeProtocol",
    "OptimizationResultProtocol",
    "WalkForwardTestProtocol",
    "DatabaseSessionProtocol",
    "BacktestPersistenceRepository",
    # Implementations
    "BacktestPersistenceError",
    "SQLAlchemyBacktestRepository",
]
