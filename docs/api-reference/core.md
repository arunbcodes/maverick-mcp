# Core API Reference

Core financial analysis functions and technical indicators.

## Module: maverick_mcp.core.technical_analysis

### calculate_sma()

Calculate Simple Moving Average.

**Signature**:
```python
def calculate_sma(
    data: pd.DataFrame,
    period: int = 20,
    price_col: str = "Close"
) -> pd.DataFrame
```

**Parameters**:
- `data` (pd.DataFrame): DataFrame with OHLCV data
- `period` (int, optional): Moving average period. Default: 20
- `price_col` (str, optional): Column to use for calculation. Default: "Close"

**Returns**:
- pd.DataFrame: Input data with added SMA column

**Example**:
```python
from maverick_mcp.core.technical_analysis import calculate_sma
import pandas as pd

# Sample data
data = pd.DataFrame({
    'Close': [100, 102, 101, 103, 105]
})

# Calculate 3-period SMA
result = calculate_sma(data, period=3)
print(result['SMA_3'])
```

---

### calculate_ema()

Calculate Exponential Moving Average.

**Signature**:
```python
def calculate_ema(
    data: pd.DataFrame,
    period: int = 20,
    price_col: str = "Close"
) -> pd.DataFrame
```

**Parameters**:
- `data` (pd.DataFrame): DataFrame with OHLCV data
- `period` (int, optional): EMA period. Default: 20
- `price_col` (str, optional): Column to use. Default: "Close"

**Returns**:
- pd.DataFrame: Input data with added EMA column

**Formula**:
```
EMA = Price(t) × k + EMA(y) × (1 − k)
where k = 2 / (period + 1)
```

---

### calculate_rsi()

Calculate Relative Strength Index.

**Signature**:
```python
def calculate_rsi(
    data: pd.DataFrame,
    period: int = 14,
    price_col: str = "Close"
) -> pd.DataFrame
```

**Parameters**:
- `data` (pd.DataFrame): DataFrame with OHLCV data
- `period` (int, optional): RSI period. Default: 14
- `price_col` (str, optional): Column to use. Default: "Close"

**Returns**:
- pd.DataFrame: Input data with added RSI column

**Formula**:
```
RSI = 100 - (100 / (1 + RS))
where RS = Average Gain / Average Loss over period
```

**Interpretation**:
- RSI > 70: Overbought
- RSI < 30: Oversold
- RSI = 50: Neutral

---

### calculate_macd()

Calculate Moving Average Convergence Divergence.

**Signature**:
```python
def calculate_macd(
    data: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    price_col: str = "Close"
) -> pd.DataFrame
```

**Parameters**:
- `data` (pd.DataFrame): DataFrame with OHLCV data
- `fast_period` (int, optional): Fast EMA period. Default: 12
- `slow_period` (int, optional): Slow EMA period. Default: 26
- `signal_period` (int, optional): Signal line period. Default: 9
- `price_col` (str, optional): Column to use. Default: "Close"

**Returns**:
- pd.DataFrame: Input data with MACD, Signal, and Histogram columns

**Formula**:
```
MACD Line = EMA(12) - EMA(26)
Signal Line = EMA(9) of MACD Line
Histogram = MACD Line - Signal Line
```

**Signals**:
- MACD crosses above Signal: Bullish
- MACD crosses below Signal: Bearish
- Histogram expanding: Trend strengthening
- Histogram contracting: Trend weakening

---

### calculate_bollinger_bands()

Calculate Bollinger Bands.

**Signature**:
```python
def calculate_bollinger_bands(
    data: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0,
    price_col: str = "Close"
) -> pd.DataFrame
```

**Parameters**:
- `data` (pd.DataFrame): DataFrame with OHLCV data
- `period` (int, optional): Moving average period. Default: 20
- `std_dev` (float, optional): Standard deviations for bands. Default: 2.0
- `price_col` (str, optional): Column to use. Default: "Close"

**Returns**:
- pd.DataFrame: Input data with Upper_Band, Middle_Band, Lower_Band columns

**Formula**:
```
Middle Band = SMA(period)
Upper Band = Middle Band + (std_dev × standard deviation)
Lower Band = Middle Band - (std_dev × standard deviation)
```

**Interpretation**:
- Price touches upper band: Overbought
- Price touches lower band: Oversold
- Band width: Volatility indicator

---

### get_support_resistance()

Identify support and resistance levels.

**Signature**:
```python
def get_support_resistance(
    data: pd.DataFrame,
    lookback: int = 20
) -> dict
```

**Parameters**:
- `data` (pd.DataFrame): DataFrame with OHLCV data
- `lookback` (int, optional): Period for level detection. Default: 20

**Returns**:
- dict: Contains 'support' and 'resistance' price levels

**Algorithm**:
- Identifies local minima for support
- Identifies local maxima for resistance
- Uses pivot point detection

---

## Module: maverick_mcp.core.visualization

### plot_stock_chart()

Create interactive stock price chart.

**Signature**:
```python
def plot_stock_chart(
    data: pd.DataFrame,
    ticker: str,
    show_volume: bool = True
) -> str
```

**Parameters**:
- `data` (pd.DataFrame): DataFrame with OHLCV data
- `ticker` (str): Stock symbol for chart title
- `show_volume` (bool, optional): Include volume subplot. Default: True

**Returns**:
- str: HTML string with Plotly chart

---

### plot_technical_indicators()

Plot technical indicators with price chart.

**Signature**:
```python
def plot_technical_indicators(
    data: pd.DataFrame,
    ticker: str,
    indicators: list[str]
) -> str
```

**Parameters**:
- `data` (pd.DataFrame): DataFrame with price and indicator data
- `ticker` (str): Stock symbol
- `indicators` (list[str]): List of indicator names to plot

**Returns**:
- str: HTML string with multi-panel chart

**Supported Indicators**:
- SMA, EMA (overlaid on price)
- RSI (separate panel)
- MACD (separate panel with histogram)
- Bollinger Bands (overlaid on price)

---

## Best Practices

### Data Requirements

All technical analysis functions expect DataFrames with:
- **Date index**: DatetimeIndex or date column
- **OHLCV columns**: Open, High, Low, Close, Volume
- **Clean data**: No missing values in critical columns

### Error Handling

```python
try:
    result = calculate_rsi(data, period=14)
except ValueError as e:
    print(f"Invalid data: {e}")
except KeyError as e:
    print(f"Missing column: {e}")
```

### Performance Tips

- Pre-sort data by date before calculations
- Use vectorized operations (pandas/numpy)
- Cache results for repeated calculations
- Batch process multiple indicators

### Common Patterns

**Combine Multiple Indicators**:
```python
data = calculate_sma(data, period=20)
data = calculate_ema(data, period=12)
data = calculate_rsi(data, period=14)
data = calculate_macd(data)
data = calculate_bollinger_bands(data)
```

**Check for Signals**:
```python
# RSI oversold
oversold = data[data['RSI'] < 30]

# MACD bullish crossover
bullish = data[data['MACD'] > data['Signal']]

# Price above upper Bollinger Band
overbought = data[data['Close'] > data['Upper_Band']]
```
