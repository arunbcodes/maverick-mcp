# Backtesting

Cryptocurrency backtesting with VectorBT.

## CryptoBacktestEngine

Main backtesting engine for crypto strategies.

::: maverick_crypto.backtesting.CryptoBacktestEngine
    options:
      show_root_heading: true
      members:
        - run_backtest
        - compare_strategies
        - optimize_strategy

### Example Usage

```python
from maverick_crypto.backtesting import CryptoBacktestEngine

engine = CryptoBacktestEngine()

# Run backtest
results = await engine.run_backtest(
    symbol="BTC-USD",
    strategy="momentum",
    start_date="2023-01-01",
    end_date="2024-01-01",
    initial_capital=10000,
)

print(f"Total Return: {results['total_return']}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']}")
print(f"Max Drawdown: {results['max_drawdown']}%")

# Compare all strategies
comparison = await engine.compare_strategies(
    symbol="ETH-USD",
    start_date="2023-01-01"
)

# Optimize parameters
optimized = await engine.optimize_strategy(
    symbol="SOL-USD",
    strategy="rsi",
    start_date="2023-01-01"
)
```

## StrategyRegistry

Registry of available backtesting strategies.

::: maverick_crypto.backtesting.StrategyRegistry
    options:
      show_root_heading: true
      members:
        - get_strategy
        - list_strategies
        - register_strategy

## Strategies

### MomentumStrategy

Multi-timeframe momentum strategy.

::: maverick_crypto.backtesting.strategies.MomentumStrategy
    options:
      show_root_heading: true

**Parameters:**

| Name | Default | Description |
|------|---------|-------------|
| `lookback` | 20 | Lookback period in days |
| `threshold` | 0.02 | Return threshold (2%) |

**Signals:**

- **Buy**: Price momentum > threshold
- **Sell**: Price momentum < -threshold

### MeanReversionStrategy

Statistical mean reversion strategy.

::: maverick_crypto.backtesting.strategies.MeanReversionStrategy
    options:
      show_root_heading: true

**Parameters:**

| Name | Default | Description |
|------|---------|-------------|
| `period` | 20 | Rolling period |
| `z_threshold` | 2.0 | Z-score threshold |

**Signals:**

- **Buy**: Z-score < -threshold (oversold)
- **Sell**: Z-score > threshold (overbought)

### BreakoutStrategy

Volatility breakout strategy.

::: maverick_crypto.backtesting.strategies.BreakoutStrategy
    options:
      show_root_heading: true

**Parameters:**

| Name | Default | Description |
|------|---------|-------------|
| `period` | 20 | ATR period |
| `factor` | 2.0 | ATR multiplier |

**Signals:**

- **Buy**: Price breaks above upper band
- **Sell**: Price breaks below lower band

### RSIStrategy

RSI oversold/overbought strategy.

::: maverick_crypto.backtesting.strategies.RSIStrategy
    options:
      show_root_heading: true

**Parameters:**

| Name | Default | Description |
|------|---------|-------------|
| `period` | 14 | RSI period |
| `oversold` | 25 | Buy threshold |
| `overbought` | 75 | Sell threshold |

!!! note "Crypto-Optimized"
    Default thresholds (25/75) are wider than stocks (30/70) to account for higher volatility.

### MACDStrategy

MACD crossover strategy.

::: maverick_crypto.backtesting.strategies.MACDStrategy
    options:
      show_root_heading: true

**Parameters:**

| Name | Default | Description |
|------|---------|-------------|
| `fast_period` | 12 | Fast EMA period |
| `slow_period` | 26 | Slow EMA period |
| `signal_period` | 9 | Signal line period |

### BollingerStrategy

Bollinger Bands mean reversion.

::: maverick_crypto.backtesting.strategies.BollingerStrategy
    options:
      show_root_heading: true

**Parameters:**

| Name | Default | Description |
|------|---------|-------------|
| `period` | 20 | Rolling period |
| `std` | 2.5 | Standard deviations |

!!! note "Crypto-Optimized"
    Default std (2.5) is wider than stocks (2.0) for crypto volatility.

## Performance Metrics

All backtests return these metrics:

| Metric | Description |
|--------|-------------|
| `total_return` | Total percentage return |
| `sharpe_ratio` | Risk-adjusted return |
| `max_drawdown` | Maximum peak-to-trough decline |
| `win_rate` | Percentage of winning trades |
| `num_trades` | Total number of trades |
| `avg_trade` | Average return per trade |
| `best_trade` | Best single trade return |
| `worst_trade` | Worst single trade return |

