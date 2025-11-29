# maverick-backtest: Engine

VectorBT-powered backtesting engine for strategy evaluation.

## VectorBTEngine

Core backtesting engine with multiple strategy support.

```python
from maverick_backtest import VectorBTEngine

engine = VectorBTEngine()

# Run a simple backtest
result = engine.run_backtest(
    symbol="AAPL",
    strategy="sma_cross",
    start_date="2023-01-01",
    end_date="2024-01-01",
    initial_capital=10000,
    fast_period=10,
    slow_period=20
)

print(f"Total Return: {result['total_return']:.2%}")
print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {result['max_drawdown']:.2%}")
```

---

## Available Strategies

### SMA Crossover

```python
result = engine.run_backtest(
    symbol="AAPL",
    strategy="sma_cross",
    fast_period=10,
    slow_period=20
)
```

### RSI

```python
result = engine.run_backtest(
    symbol="AAPL",
    strategy="rsi",
    period=14,
    oversold=30,
    overbought=70
)
```

### MACD

```python
result = engine.run_backtest(
    symbol="AAPL",
    strategy="macd",
    fast_period=12,
    slow_period=26,
    signal_period=9
)
```

### Bollinger Bands

```python
result = engine.run_backtest(
    symbol="AAPL",
    strategy="bollinger",
    period=20,
    std_dev=2.0
)
```

### Momentum

```python
result = engine.run_backtest(
    symbol="AAPL",
    strategy="momentum",
    lookback=20,
    threshold=0.02
)
```

---

## Result Structure

```python
{
    # Performance Metrics
    "total_return": 0.25,           # 25% return
    "annual_return": 0.22,          # 22% annualized
    "sharpe_ratio": 1.5,            # Risk-adjusted return
    "sortino_ratio": 2.1,           # Downside risk-adjusted
    "max_drawdown": -0.15,          # Maximum drawdown
    "calmar_ratio": 1.47,           # Return / Max Drawdown
    
    # Trade Statistics
    "total_trades": 24,
    "win_rate": 0.625,              # 62.5% winners
    "profit_factor": 1.8,           # Gross profit / Gross loss
    "avg_trade_return": 0.01,       # Average return per trade
    "avg_win": 0.025,               # Average winning trade
    "avg_loss": -0.012,             # Average losing trade
    
    # Time Analysis
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "trading_days": 252,
    
    # Equity Curve
    "equity_curve": [...],          # Daily equity values
    "trades": [...]                 # Individual trade details
}
```

---

## Portfolio Backtesting

Test strategies across multiple symbols:

```python
result = engine.backtest_portfolio(
    symbols=["AAPL", "GOOGL", "MSFT", "AMZN"],
    strategy="sma_cross",
    start_date="2023-01-01",
    end_date="2024-01-01",
    initial_capital=100000,
    position_size=0.25  # 25% per position
)

print(f"Portfolio Return: {result['portfolio_return']:.2%}")
for symbol, metrics in result['symbol_metrics'].items():
    print(f"  {symbol}: {metrics['return']:.2%}")
```

---

## Strategy Optimization

Find optimal parameters:

```python
from maverick_backtest import StrategyOptimizer

optimizer = StrategyOptimizer()

result = optimizer.optimize(
    symbol="AAPL",
    strategy="sma_cross",
    start_date="2023-01-01",
    end_date="2024-01-01",
    optimization_metric="sharpe_ratio",
    optimization_level="medium"  # coarse, medium, fine
)

print(f"Best Parameters: {result['best_params']}")
print(f"Best Sharpe: {result['best_metric']:.2f}")
```

---

## Walk-Forward Analysis

Test strategy robustness:

```python
from maverick_backtest import WalkForwardAnalyzer

analyzer = WalkForwardAnalyzer()

result = analyzer.analyze(
    symbol="AAPL",
    strategy="sma_cross",
    start_date="2020-01-01",
    end_date="2024-01-01",
    window_size=252,  # 1 year training
    step_size=63      # Quarterly steps
)

print(f"Out-of-Sample Return: {result['oos_return']:.2%}")
print(f"Consistency: {result['consistency_score']:.2%}")
```

---

## Monte Carlo Simulation

Assess strategy risk:

```python
result = engine.monte_carlo_simulation(
    symbol="AAPL",
    strategy="sma_cross",
    num_simulations=1000,
    fast_period=10,
    slow_period=20
)

print(f"Median Return: {result['median_return']:.2%}")
print(f"5th Percentile: {result['percentile_5']:.2%}")
print(f"95th Percentile: {result['percentile_95']:.2%}")
```

---

## Strategy Comparison

Compare multiple strategies:

```python
result = engine.compare_strategies(
    symbol="AAPL",
    strategies=["sma_cross", "rsi", "macd", "bollinger"],
    start_date="2023-01-01",
    end_date="2024-01-01"
)

# Ranked by Sharpe ratio
for strategy in result['rankings']:
    print(f"{strategy['name']}: Sharpe={strategy['sharpe_ratio']:.2f}")
```

