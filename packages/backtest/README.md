# Maverick Backtest

Backtesting engine and strategies for Maverick stock analysis.

## Overview

This package provides:

- **Strategies**: 15+ built-in trading strategies including ML-powered adaptive strategies
- **Engine**: VectorBT-powered high-performance backtesting engine
- **Analysis**: Comprehensive performance analytics and visualization

## Installation

```bash
pip install maverick-backtest
```

Or with uv:

```bash
uv add maverick-backtest
```

## Features

### Built-in Strategies
- SMA/EMA crossover
- RSI overbought/oversold
- MACD signal crossover
- Bollinger Bands breakout
- Momentum strategies
- Mean reversion
- ML-based adaptive strategies

### Backtesting Engine
- VectorBT for vectorized execution
- Parameter optimization via grid search
- Walk-forward analysis
- Monte Carlo simulation
- Multi-asset portfolio backtesting

### Performance Analysis
- Risk-adjusted returns (Sharpe, Sortino, Calmar)
- Maximum drawdown analysis
- Win rate and profit factor
- Interactive chart generation
- HTML report export

## Dependencies

- maverick-core: Core interfaces
- maverick-data: Data fetching
- vectorbt: Backtesting engine
- scikit-learn: ML strategies
- matplotlib/plotly: Visualization

## Usage

```python
from maverick_backtest.engine import run_backtest
from maverick_backtest.strategies import SMAStrategy

# Run a backtest
results = run_backtest(
    symbol="AAPL",
    strategy=SMAStrategy(fast_period=10, slow_period=20),
    start_date="2023-01-01",
    end_date="2024-01-01"
)

print(f"Total Return: {results.total_return:.2%}")
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
```
