# maverick-backtest

Backtesting engine and trading strategies for Maverick MCP.

## Overview

`maverick-backtest` provides:

- **Backtesting Engine**: VectorBT-powered strategy execution
- **Trading Strategies**: SMA, RSI, MACD, Bollinger, and more
- **ML Strategies**: Machine learning enhanced trading
- **Optimization**: Parameter optimization with grid search
- **Analysis**: Walk-forward analysis and Monte Carlo simulation
- **Workflows**: LangGraph-based intelligent backtesting

## Installation

```bash
pip install maverick-backtest
```

## Quick Start

```python
from maverick_backtest import BacktestEngine, run_backtest

# Simple backtest
results = run_backtest(
    symbol="AAPL",
    strategy="sma_cross",
    fast_period=10,
    slow_period=20
)

print(f"Total Return: {results['total_return']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2%}")
```

## Backtesting Engine

### Basic Usage

```python
from maverick_backtest import BacktestEngine

engine = BacktestEngine()

# Run backtest
results = engine.run_backtest(
    symbol="AAPL",
    strategy="sma_cross",
    start_date="2023-01-01",
    end_date="2024-01-01",
    initial_capital=10000,
    fast_period=10,
    slow_period=20
)
```

### Results Structure

```python
{
    "symbol": "AAPL",
    "strategy": "sma_cross",
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 10000,
    "final_value": 12500,
    
    # Performance metrics
    "total_return": 0.25,          # 25%
    "annualized_return": 0.28,     # 28% annualized
    "sharpe_ratio": 1.85,
    "sortino_ratio": 2.10,
    "max_drawdown": -0.12,         # -12%
    "win_rate": 0.58,              # 58%
    
    # Trade statistics
    "total_trades": 45,
    "winning_trades": 26,
    "losing_trades": 19,
    "avg_win": 250.00,
    "avg_loss": -150.00,
    "profit_factor": 1.65,
    
    # Trades list
    "trades": [
        {"entry_date": "2023-01-15", "exit_date": "2023-02-01", "pnl": 150},
        # ...
    ]
}
```

## Trading Strategies

### SMA Crossover

Classic moving average crossover strategy.

```python
results = engine.run_backtest(
    symbol="AAPL",
    strategy="sma_cross",
    fast_period=10,    # Fast MA period
    slow_period=20     # Slow MA period
)
```

**Signal Logic:**
- **BUY**: Fast SMA crosses above Slow SMA
- **SELL**: Fast SMA crosses below Slow SMA

### RSI Strategy

Relative Strength Index overbought/oversold strategy.

```python
results = engine.run_backtest(
    symbol="AAPL",
    strategy="rsi",
    period=14,         # RSI period
    oversold=30,       # Buy threshold
    overbought=70      # Sell threshold
)
```

**Signal Logic:**
- **BUY**: RSI falls below `oversold` level
- **SELL**: RSI rises above `overbought` level

### MACD Strategy

Moving Average Convergence Divergence strategy.

```python
results = engine.run_backtest(
    symbol="AAPL",
    strategy="macd",
    fast_period=12,    # Fast EMA period
    slow_period=26,    # Slow EMA period
    signal_period=9    # Signal line period
)
```

**Signal Logic:**
- **BUY**: MACD line crosses above Signal line
- **SELL**: MACD line crosses below Signal line

### Bollinger Bands Strategy

Volatility-based mean reversion strategy.

```python
results = engine.run_backtest(
    symbol="AAPL",
    strategy="bollinger",
    period=20,         # Moving average period
    std_dev=2          # Standard deviation multiplier
)
```

**Signal Logic:**
- **BUY**: Price touches lower Bollinger Band
- **SELL**: Price touches upper Bollinger Band

### Momentum Strategy

Price momentum strategy.

```python
results = engine.run_backtest(
    symbol="AAPL",
    strategy="momentum",
    lookback=10,       # Lookback period
    threshold=0.02     # Momentum threshold (2%)
)
```

**Signal Logic:**
- **BUY**: Momentum > threshold
- **SELL**: Momentum < -threshold

### Mean Reversion Strategy

Statistical mean reversion using z-scores.

```python
results = engine.run_backtest(
    symbol="AAPL",
    strategy="mean_reversion",
    lookback=20,              # Lookback period
    z_score_threshold=2.0     # Z-score threshold
)
```

**Signal Logic:**
- **BUY**: Z-score < -threshold (price below mean)
- **SELL**: Z-score > threshold (price above mean)

### Breakout Strategy

Price breakout from consolidation.

```python
results = engine.run_backtest(
    symbol="AAPL",
    strategy="breakout",
    lookback=20,              # Consolidation period
    breakout_factor=1.02      # Breakout threshold (2% above high)
)
```

### All Available Strategies

| Strategy | Key Parameters | Description |
|----------|---------------|-------------|
| `sma_cross` | fast_period, slow_period | Moving average crossover |
| `rsi` | period, oversold, overbought | RSI overbought/oversold |
| `macd` | fast_period, slow_period, signal_period | MACD crossover |
| `bollinger` | period, std_dev | Bollinger band bounce |
| `momentum` | lookback, threshold | Price momentum |
| `mean_reversion` | lookback, z_score_threshold | Statistical mean reversion |
| `breakout` | lookback, breakout_factor | Price breakout |

## ML-Enhanced Strategies

### ML Predictor Strategy

Machine learning price prediction.

```python
results = engine.run_ml_backtest(
    symbol="AAPL",
    strategy_type="ml_predictor",
    model_type="random_forest",
    train_ratio=0.8,
    n_estimators=100,
    max_depth=10
)
```

### Adaptive Strategy

Self-adjusting parameters based on market conditions.

```python
results = engine.run_ml_backtest(
    symbol="AAPL",
    strategy_type="adaptive",
    adaptation_method="gradient",
    learning_rate=0.01
)
```

### Ensemble Strategy

Combine multiple strategies with weighted voting.

```python
from maverick_backtest import create_strategy_ensemble

results = create_strategy_ensemble(
    symbols=["AAPL", "MSFT"],
    base_strategies=["sma_cross", "rsi", "macd"],
    weighting_method="performance"  # or "equal", "volatility"
)
```

### Regime-Aware Strategy

Adapt strategy based on detected market regime.

```python
# First, analyze regimes
regimes = engine.analyze_market_regimes(
    symbol="AAPL",
    method="hmm",  # Hidden Markov Model
    n_regimes=3
)

# Then run regime-aware backtest
results = engine.run_ml_backtest(
    symbol="AAPL",
    strategy_type="regime_aware",
    regimes=regimes
)
```

### Train ML Model

```python
from maverick_backtest import train_ml_predictor

# Train model
model_results = train_ml_predictor(
    symbol="AAPL",
    start_date="2020-01-01",
    end_date="2024-01-01",
    model_type="random_forest",
    target_periods=5,        # Predict 5 days ahead
    return_threshold=0.02,   # 2% return threshold
    n_estimators=100,
    max_depth=10
)

print(f"Accuracy: {model_results['accuracy']:.2%}")
print(f"Precision: {model_results['precision']:.2%}")
print(f"Feature Importance: {model_results['feature_importance']}")
```

## Optimization

### Parameter Optimization

```python
from maverick_backtest import optimize_strategy

results = optimize_strategy(
    symbol="AAPL",
    strategy="sma_cross",
    optimization_metric="sharpe_ratio",  # or "total_return", "win_rate"
    optimization_level="medium",         # "coarse", "medium", "fine"
    top_n=10
)

print("Best Parameters:")
print(f"  Fast Period: {results['best_params']['fast_period']}")
print(f"  Slow Period: {results['best_params']['slow_period']}")
print(f"  Sharpe Ratio: {results['best_sharpe']:.2f}")
```

### Custom Parameter Grid

```python
results = optimize_strategy(
    symbol="AAPL",
    strategy="rsi",
    param_grid={
        "period": [10, 14, 20],
        "oversold": [25, 30, 35],
        "overbought": [65, 70, 75]
    },
    optimization_metric="sharpe_ratio"
)
```

### Walk-Forward Analysis

Test strategy robustness over time.

```python
from maverick_backtest import walk_forward_analysis

results = walk_forward_analysis(
    symbol="AAPL",
    strategy="sma_cross",
    window_size=252,    # 1 year training window
    step_size=63,       # Step forward 1 quarter
    start_date="2020-01-01",
    end_date="2024-01-01"
)

print(f"Average OOS Sharpe: {results['avg_oos_sharpe']:.2f}")
print(f"Consistency: {results['consistency']:.2%}")
```

### Monte Carlo Simulation

Statistical analysis of strategy performance.

```python
from maverick_backtest import monte_carlo_simulation

results = monte_carlo_simulation(
    symbol="AAPL",
    strategy="sma_cross",
    num_simulations=1000,
    fast_period=10,
    slow_period=20
)

print(f"Mean Return: {results['mean_return']:.2%}")
print(f"5th Percentile: {results['percentile_5']:.2%}")
print(f"95th Percentile: {results['percentile_95']:.2%}")
print(f"Probability of Profit: {results['prob_profit']:.2%}")
```

## Strategy Comparison

Compare multiple strategies on the same symbol.

```python
from maverick_backtest import compare_strategies

results = compare_strategies(
    symbol="AAPL",
    strategies=["sma_cross", "rsi", "macd", "bollinger"],
    start_date="2023-01-01",
    end_date="2024-01-01"
)

# Ranked by Sharpe Ratio
for rank, strategy in enumerate(results['rankings'], 1):
    print(f"{rank}. {strategy['name']}: Sharpe {strategy['sharpe_ratio']:.2f}")
```

## Portfolio Backtesting

Backtest across multiple symbols.

```python
from maverick_backtest import backtest_portfolio

results = backtest_portfolio(
    symbols=["AAPL", "MSFT", "GOOGL", "AMZN"],
    strategy="sma_cross",
    initial_capital=100000,
    position_size=0.25,   # 25% per position
    fast_period=10,
    slow_period=20
)

print(f"Portfolio Return: {results['total_return']:.2%}")
print(f"Portfolio Sharpe: {results['sharpe_ratio']:.2f}")
```

## Market Regime Analysis

Detect market regimes for strategy adaptation.

```python
from maverick_backtest import analyze_market_regimes

results = analyze_market_regimes(
    symbol="SPY",
    method="hmm",           # "hmm", "kmeans", "threshold"
    n_regimes=3,            # Bull, Bear, Sideways
    lookback_period=50
)

# Current regime
print(f"Current Regime: {results['current_regime']}")
print(f"Regime Probabilities: {results['regime_probabilities']}")

# Historical regimes
for regime in results['regimes']:
    print(f"{regime['name']}: {regime['avg_return']:.2%} return, {regime['volatility']:.2%} vol")
```

## Chart Generation

Generate visual analysis charts.

```python
from maverick_backtest import (
    generate_backtest_charts,
    generate_optimization_charts
)

# Backtest charts
charts = generate_backtest_charts(
    symbol="AAPL",
    strategy="sma_cross",
    theme="dark"  # or "light"
)

# Returns base64-encoded images
# - equity_curve
# - drawdown_chart
# - trade_analysis
# - indicator_chart

# Optimization heatmap
opt_charts = generate_optimization_charts(
    symbol="AAPL",
    strategy="sma_cross"
)
```

## LangGraph Workflows

Intelligent backtesting with AI agents.

```python
from maverick_backtest import BacktestingWorkflow

workflow = BacktestingWorkflow()

# Run intelligent backtest
results = await workflow.run({
    "symbol": "AAPL",
    "user_goal": "Find the best momentum strategy for AAPL",
    "risk_tolerance": "moderate"
})

# Workflow steps:
# 1. Market Analyzer - Determine market regime
# 2. Strategy Selector - Select appropriate strategies
# 3. Optimizer - Optimize parameters
# 4. Validator - Validate with walk-forward analysis
```

## Natural Language Parsing

Parse strategy descriptions.

```python
from maverick_backtest import parse_strategy

# Natural language to strategy
config = parse_strategy(
    "Buy when RSI is below 30 and sell when above 70"
)
# {"strategy": "rsi", "period": 14, "oversold": 30, "overbought": 70}

config = parse_strategy(
    "Use 10-day and 20-day moving average crossover"
)
# {"strategy": "sma_cross", "fast_period": 10, "slow_period": 20}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKTEST_CACHE_TTL` | Results cache TTL | `3600` |
| `VBT_PARALLEL` | Enable parallel execution | `true` |

### Engine Configuration

```python
engine = BacktestEngine(
    cache_enabled=True,
    parallel_enabled=True,
    max_workers=4
)
```

## Testing

```python
import pytest
from maverick_backtest import BacktestEngine
import pandas as pd

def test_sma_crossover():
    engine = BacktestEngine()
    
    results = engine.run_backtest(
        symbol="AAPL",
        strategy="sma_cross",
        start_date="2023-01-01",
        end_date="2023-12-31",
        fast_period=10,
        slow_period=20
    )
    
    assert results['total_trades'] > 0
    assert 'sharpe_ratio' in results
    assert 'max_drawdown' in results
```

## API Reference

For detailed API documentation, see:

- [Backtesting Engine API](../api-reference/maverick-backtest/engine.md)

