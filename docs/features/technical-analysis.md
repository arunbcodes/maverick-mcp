# Technical Analysis

Comprehensive technical indicators and analysis tools.

## Available Indicators

### Moving Averages
- **Simple Moving Average (SMA)**: Basic trend indicator
- **Exponential Moving Average (EMA)**: Weighted recent prices
- **Common Periods**: 20, 50, 100, 200 days

### Momentum Indicators
- **RSI (Relative Strength Index)**: Overbought/oversold (0-100)
- **MACD**: Trend following momentum (MACD, Signal, Histogram)
- **Stochastic Oscillator**: %K and %D lines

### Volatility Indicators
- **Bollinger Bands**: Price volatility bands (Upper, Middle, Lower)
- **ATR (Average True Range)**: Volatility measurement
- **Standard Deviation**: Price dispersion

### Volume Indicators
- **OBV (On-Balance Volume)**: Volume-price relationship
- **Volume MA**: Average volume trends
- **Money Flow Index**: Volume-weighted RSI

### Trend Indicators
- **ADX (Average Directional Index)**: Trend strength
- **Parabolic SAR**: Stop and reverse points
- **Ichimoku Cloud**: Comprehensive trend system

## Full Technical Analysis

```
Get full technical analysis for AAPL
```

Returns comprehensive analysis including:
- All major indicators calculated
- Support and resistance levels
- Trend direction and strength
- Buy/sell/hold signals
- Chart patterns detected

## Usage Examples

### Single Indicator
```
Calculate 20-day SMA for AAPL
```

### Multiple Indicators
```
Get RSI, MACD, and Bollinger Bands for RELIANCE.NS
```

### Complete Analysis
```
Provide full technical analysis for TCS.NS
```

## Indicator Details

### RSI (Relative Strength Index)
**Formula**: RSI = 100 - (100 / (1 + RS))
- **Period**: 14 days (default)
- **Overbought**: Above 70
- **Oversold**: Below 30
- **Divergence**: Price vs RSI trends

**Signals**:
- RSI > 70: Overbought, consider selling
- RSI < 30: Oversold, consider buying
- Bullish divergence: Price lower, RSI higher
- Bearish divergence: Price higher, RSI lower

### MACD (Moving Average Convergence Divergence)
**Components**:
- MACD Line: 12 EMA - 26 EMA
- Signal Line: 9 EMA of MACD
- Histogram: MACD - Signal

**Signals**:
- MACD crosses above Signal: Bullish
- MACD crosses below Signal: Bearish
- Histogram expansion: Trend strengthening
- Histogram contraction: Trend weakening

### Bollinger Bands
**Formula**:
- Middle Band: 20-day SMA
- Upper Band: Middle + (2 × SD)
- Lower Band: Middle - (2 × SD)

**Signals**:
- Price touches upper band: Overbought
- Price touches lower band: Oversold
- Band squeeze: Low volatility, breakout coming
- Band expansion: High volatility, trend in motion

## Support and Resistance

Automatic calculation of:
- **Support Levels**: Price floors (recent lows)
- **Resistance Levels**: Price ceilings (recent highs)
- **Pivot Points**: Daily/weekly/monthly pivots
- **Fibonacci Retracements**: Key reversal levels

## Pattern Recognition

Detects common chart patterns:
- Head and Shoulders
- Double Top/Bottom
- Triangles (Ascending, Descending, Symmetrical)
- Flags and Pennants
- Cup and Handle

## Backtesting Integration

Technical indicators can be used in [backtesting strategies](backtesting.md):
```
Backtest RSI strategy on AAPL: Buy when RSI < 30, Sell when RSI > 70
```

## Performance

All technical indicators are calculated using:
- **pandas_ta library**: Fast, reliable calculations
- **Vectorized operations**: Efficient numpy arrays
- **Caching**: Results cached for 1 hour
- **Batch processing**: Multiple stocks in parallel

## API Reference

See [Technical Analysis Tools](../user-guide/mcp-tools.md#technical-analysis) for complete API documentation.
