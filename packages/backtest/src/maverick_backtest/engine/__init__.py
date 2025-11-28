"""
Backtesting Engine.

VectorBT-powered backtesting engine with support for:
- Strategy execution
- Parameter optimization
- Walk-forward analysis
- Monte Carlo simulation
"""

from maverick_backtest.engine.vectorbt_engine import IDataProvider, VectorBTEngine

__all__ = [
    "VectorBTEngine",
    "IDataProvider",
]
