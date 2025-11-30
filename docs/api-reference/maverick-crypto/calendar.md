# Calendar Service

24/7 market handling for cryptocurrencies.

## CryptoCalendarService

Handles the continuous nature of cryptocurrency markets.

::: maverick_crypto.calendar.CryptoCalendarService
    options:
      show_root_heading: true
      members:
        - is_market_open
        - get_trading_days
        - get_market_hours
        - get_volatility_params

## Overview

Unlike stock markets, cryptocurrency markets operate 24/7/365:

| Aspect | Stocks | Crypto |
|--------|--------|--------|
| Trading Hours | 9:30-4:00 ET | 24/7 |
| Weekends | Closed | Open |
| Holidays | Closed | Open |
| Circuit Breakers | Yes (10% limits) | No |

## Example Usage

```python
from maverick_crypto.calendar import CryptoCalendarService

calendar = CryptoCalendarService()

# Check if market is open
is_open = calendar.is_market_open("BTC")  # Always True

# Get trading days (all days in range)
days = calendar.get_trading_days(
    start="2024-01-01",
    end="2024-01-31"
)
# Returns all 31 days

# Get market hours
hours = calendar.get_market_hours("BTC")
# Returns: {"open": "00:00", "close": "23:59", "timezone": "UTC"}

# Get volatility parameters for crypto
params = calendar.get_volatility_params()
# Returns crypto-specific volatility adjustments
```

## Volatility Parameters

Crypto-specific parameters for backtesting and analysis:

```python
{
    "rsi_oversold": 25,      # vs 30 for stocks
    "rsi_overbought": 75,    # vs 70 for stocks
    "bollinger_std": 2.5,    # vs 2.0 for stocks
    "stop_loss_pct": 0.10,   # vs 0.03 for stocks
    "position_size": 0.02,   # vs 0.05 for stocks
}
```

### Why Different Parameters?

Crypto is approximately 3-5x more volatile than stocks:

- **Bitcoin** 30-day volatility: ~60-80%
- **S&P 500** 30-day volatility: ~15-20%

This means:

1. **Wider RSI thresholds**: 25/75 vs 30/70
2. **Wider Bollinger Bands**: 2.5σ vs 2.0σ
3. **Larger stop losses**: 10% vs 3%
4. **Smaller positions**: 2% vs 5%

## Integration with Backtesting

The calendar service automatically applies 24/7 handling:

```python
from maverick_crypto.backtesting import CryptoBacktestEngine

engine = CryptoBacktestEngine()

# Backtests include weekends and holidays
results = await engine.run_backtest(
    symbol="BTC-USD",
    strategy="momentum",
    start_date="2024-01-01",  # Monday
    end_date="2024-01-31",    # Wednesday
)
# Uses all 31 days, not just ~22 trading days
```

## Comparison with Stock Calendar

```python
from maverick_data.services import MarketCalendarService
from maverick_crypto.calendar import CryptoCalendarService

stock_cal = MarketCalendarService()
crypto_cal = CryptoCalendarService()

# January 2024
start = "2024-01-01"
end = "2024-01-31"

stock_days = stock_cal.get_trading_days(start, end)
crypto_days = crypto_cal.get_trading_days(start, end)

print(f"Stock trading days: {len(stock_days)}")   # ~21
print(f"Crypto trading days: {len(crypto_days)}") # 31
```

## Best Practices

### Time Zones

- Use UTC for all crypto timestamps
- Don't assume any "market open" or "close" times
- Be aware of regional volume patterns

### Weekend/Holiday Trading

- Weekends often have lower liquidity
- Major holidays may see reduced volume
- Flash crashes more common during low-volume periods

### Continuous Data

- No gaps in OHLCV data for crypto
- 1-minute to daily granularity available
- Use daily data for backtesting to reduce noise

