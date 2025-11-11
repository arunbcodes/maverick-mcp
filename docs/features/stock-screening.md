# Stock Screening

Pre-calculated screening strategies for finding trading opportunities.

## Pre-Seeded Database

520+ S&P 500 stocks with pre-calculated screening data:
- Instant results (no API calls needed)
- Daily updated screening scores
- Multiple strategy support
- Cached in database

## Screening Strategies

### Maverick Bullish
High momentum stocks with strong technical setup.

**Criteria**:
- RSI between 50-70 (strong but not overbought)
- MACD above signal line (bullish momentum)
- Price above 20-day SMA (uptrend)
- Volume above average (confirmation)
- Positive price momentum (rising)

**Use Case**: Finding strong trending stocks for swing trading

```
Show me top 10 Maverick bullish stocks
```

### Maverick Bearish
Weak stocks with potential for shorting or avoiding.

**Criteria**:
- RSI between 30-50 (weak but not oversold)
- MACD below signal line (bearish momentum)
- Price below 20-day SMA (downtrend)
- Volume declining (weakness)
- Negative price momentum

**Use Case**: Finding weak stocks for short positions

```
Show me Maverick bearish stocks to avoid
```

### Supply/Demand Breakouts
Stocks in confirmed uptrend with breakout patterns.

**Criteria**:
- Price above all major moving averages (20, 50, 200 SMA)
- Volume surge on breakout
- New 52-week high or near it
- Consolidation followed by expansion
- Strong relative strength

**Use Case**: Finding breakout candidates

```
Find supply/demand breakout opportunities
```

## Indian Market Screening

7 specialized strategies for NSE/BSE stocks:

### 1. Bullish Momentum (NSE/BSE)
- Adapted 10% circuit breakers
- INR currency formatting
- T+1 settlement consideration
- Nifty/Sensex correlation

### 2. Value Stocks (NSE/BSE)
- Low P/E ratios (< sector average)
- High dividend yield
- Strong fundamentals
- Book value considerations

### 3. Dividend Yield (NSE/BSE)
- Consistent dividend payers
- Yield > 3%
- Payout ratio sustainability
- Dividend growth history

### 4. Small-Cap Growth (NSE/BSE)
- Market cap < ₹5000 crore
- Revenue growth > 20% YoY
- Emerging sectors
- Management quality

### 5. Sector Rotation (NSE/BSE)
- Identify hot sectors
- Top performers within sector
- Sector momentum
- Relative strength

### 6. Breakout Candidates (NSE/BSE)
- 52-week high proximity
- Volume breakouts
- Chart pattern completion
- Support/resistance levels

### 7. Oversold Recovery (NSE/BSE)
- RSI < 30 (oversold)
- Fundamental strength intact
- No structural issues
- Reversal signals

## Usage Examples

### US Market Screening
```
Show me top 5 Maverick bullish stocks from S&P 500
```

### Indian Market Screening
```
Find dividend yield stocks from Nifty 50
```

### Sector-Specific
```
Screen for bullish tech stocks
```

### Custom Filters
```
Find stocks with RSI < 35 and price above 200-day SMA
```

## Screening Process

### Data Collection
1. Daily price and volume data
2. Technical indicator calculation
3. Fundamental data updates
4. Screening score computation

### Ranking System
Stocks ranked by:
- **Score (0-100)**: Composite screening score
- **Signal Strength**: How strongly criteria are met
- **Confidence**: Data quality and recency
- **Risk Level**: Volatility and beta

### Refresh Frequency
- **S&P 500**: Updated daily at market close
- **Indian Stocks**: Updated daily after NSE close
- **Cache**: Results cached for 24 hours
- **On-Demand**: Force refresh available

## Performance Metrics

Track screening strategy performance:
- Historical hit rate
- Average return per recommendation
- Time to target achievement
- Risk-adjusted returns

## API Reference

See [Screening Tools](../user-guide/mcp-tools.md#screening) for complete API documentation.

## Customization

While pre-calculated screens are instant, you can also:
- Combine multiple strategies
- Add custom filters
- Adjust threshold values
- Create sector-specific screens

Example:
```
Find Maverick bullish tech stocks with market cap > $10B
```
