# Indian Market Support - Complete Guide

Complete guide to analyzing Indian stocks (NSE and BSE) using MaverickMCP.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Supported Markets](#supported-markets)
- [Stock Screening Strategies](#stock-screening-strategies)
- [Economic Indicators](#economic-indicators)
- [News & Sentiment Analysis](#news--sentiment-analysis)
- [Market Comparison](#market-comparison)
- [Currency Conversion](#currency-conversion)
- [Examples](#examples)
- [Advanced Usage](#advanced-usage)
- [Best Practices](#best-practices)

---

## Quick Start

### Analyzing an Indian Stock

```python
from maverick_mcp.providers.indian_market_data import IndianMarketDataProvider

# Initialize provider
provider = IndianMarketDataProvider()

# Get Reliance Industries data (NSE)
reliance_data = provider.get_stock_data("RELIANCE.NS", period="1y")

# Get TCS data (BSE)
tcs_data = provider.get_stock_data("TCS.BO", period="6m")
```

### Using with Claude Desktop

Simply ask Claude:

```
"Show me bullish Indian stock recommendations"
"What are the RBI policy rates?"
"Compare Apple stock with TCS"
"Convert 10000 INR to USD"
```

---

## Supported Markets

### NSE (National Stock Exchange)

- **Symbol Suffix**: `.NS`
- **Examples**: `RELIANCE.NS`, `TCS.NS`, `INFY.NS`
- **Trading Hours**: 9:15 AM - 3:30 PM IST
- **Circuit Breakers**: 10% daily limit
- **Settlement**: T+1

### BSE (Bombay Stock Exchange)

- **Symbol Suffix**: `.BO`
- **Examples**: `RELIANCE.BO`, `TCS.BO`, `INFY.BO`
- **Trading Hours**: 9:15 AM - 3:30 PM IST
- **Circuit Breakers**: 10% daily limit
- **Settlement**: T+1

### Major Indices

- **Nifty 50**: `^NSEI` - Top 50 companies by market cap
- **Sensex**: `^BSESN` - BSE 30 most traded stocks
- **Nifty Bank**: `^NSEBANK` - Banking sector index
- **Nifty IT**: `^CNXIT` - IT sector index

---

## Stock Screening Strategies

### 1. Maverick Bullish India

High-momentum stocks with strong technical indicators.

**Criteria:**
- Volume > 500,000 shares
- RSI 30-70 (momentum without overbought)
- Price above 20-day SMA
- Positive price momentum (> 2%)

**Usage:**
```python
from maverick_mcp.application.screening.indian_market import get_maverick_bullish_india

recommendations = get_maverick_bullish_india(limit=10)
```

**Claude Desktop:**
```
"Show me bullish Indian stocks"
"Get me maverick bullish recommendations for India"
```

### 2. Maverick Bearish India

Weak stocks with bearish indicators for short opportunities.

**Criteria:**
- Volume > 500,000 shares
- RSI > 70 (overbought)
- Price below 20-day SMA
- Negative momentum

**Usage:**
```python
from maverick_mcp.application.screening.indian_market import get_maverick_bearish_india

recommendations = get_maverick_bearish_india(limit=10)
```

### 3. Nifty 50 Momentum

High-momentum stocks from Nifty 50 constituents.

**Criteria:**
- Must be in Nifty 50
- Weekly price change > 2%
- Strong volume
- Positive trend

**Usage:**
```python
from maverick_mcp.application.screening.indian_market import get_nifty50_momentum

recommendations = get_nifty50_momentum(limit=15)
```

### 4. Nifty Sector Rotation

Identify which sectors are performing best.

**Returns:**
- Average sector returns
- Stock count per sector
- Top 3 stocks in each sector

**Usage:**
```python
from maverick_mcp.application.screening.indian_market import get_nifty_sector_rotation

sector_analysis = get_nifty_sector_rotation(lookback_days=90, top_n=3)
```

**Claude Desktop:**
```
"Which Nifty sectors are hot right now?"
"Show me sector rotation analysis"
```

### 5. Value Picks India

Undervalued stocks trading in lower 30% of 52-week range.

**Target Sectors:**
- Banking & Financial Services
- Oil & Gas
- Consumer Goods

**Usage:**
```python
from maverick_mcp.application.screening.indian_market import get_value_picks_india

value_stocks = get_value_picks_india(limit=15)
```

### 6. High Dividend India

Stable, high-dividend yielding stocks.

**Criteria:**
- Market cap > ₹10,000 crores
- Price stability score > 0.7
- Sector diversification

**Usage:**
```python
from maverick_mcp.application.screening.indian_market import get_high_dividend_india

dividend_stocks = get_high_dividend_india(limit=15)
```

### 7. Small-Cap Breakouts India

High-potential small-cap stocks with breakout signals.

**Criteria:**
- Volume spike > 150% of 30-day average
- Strong momentum (> 3% weekly gain)
- Low to mid cap range

**Usage:**
```python
from maverick_mcp.application.screening.indian_market import get_smallcap_breakouts_india

breakouts = get_smallcap_breakouts_india(limit=10)
```

---

## Economic Indicators

### RBI Policy Rates

Get current Reserve Bank of India monetary policy rates.

```python
from maverick_mcp.providers.rbi_data import RBIDataProvider

provider = RBIDataProvider()
rates = provider.get_policy_rates()

print(f"Repo Rate: {rates['repo_rate']}%")
print(f"Reverse Repo Rate: {rates['reverse_repo_rate']}%")
print(f"CRR: {rates['crr']}%")
print(f"SLR: {rates['slr']}%")
```

**Claude Desktop:**
```
"What are the current RBI policy rates?"
"Show me Indian economic indicators"
```

### GDP Growth

```python
gdp_data = provider.get_gdp_growth()
print(f"Current GDP Growth: {gdp_data['current']}%")
```

### Foreign Exchange Reserves

```python
forex = provider.get_forex_reserves()
print(f"Total Reserves: ${forex['total_reserves_usd']:.2f} billion")
```

### Economic Calendar

```python
calendar = provider.get_economic_calendar(days_ahead=30)
for event in calendar:
    print(f"{event['date']}: {event['event']} ({event['importance']})")
```

### All Indicators at Once

```python
all_indicators = provider.get_all_indicators()
# Returns: policy_rates, gdp_growth, forex_reserves, economic_calendar
```

---

## News & Sentiment Analysis

### Get Stock News

```python
from maverick_mcp.providers.indian_news import IndianNewsProvider

provider = IndianNewsProvider()

# Get news for specific stock
news = provider.get_stock_news("RELIANCE.NS", limit=10)

for article in news:
    print(f"{article['title']} - {article['sentiment']}")
    print(f"Source: {article['source']}")
```

**Claude Desktop:**
```
"Get news for Reliance Industries"
"Show me TCS stock news"
```

### Sentiment Analysis

```python
sentiment = provider.analyze_sentiment("TCS.NS", period="7d")

print(f"Overall Sentiment: {sentiment['overall_sentiment']}")
print(f"Sentiment Score: {sentiment['sentiment_score']}")
print(f"Articles Analyzed: {sentiment['article_count']}")
```

**Claude Desktop:**
```
"What's the sentiment on TCS?"
"Analyze news sentiment for Infosys"
```

### Market News

```python
# Get general market news
market_news = provider.get_market_news(category="all", limit=20)

# Get trending topics
trending = provider.get_trending_topics(limit=10)
```

---

## Market Comparison

### Compare US and Indian Markets

```python
from maverick_mcp.analysis.market_comparison import MarketComparisonAnalyzer

analyzer = MarketComparisonAnalyzer()

# Compare S&P 500 and Nifty 50
comparison = analyzer.compare_indices(period="1y")

print(f"S&P 500 Return: {comparison['sp500']['return_pct']}%")
print(f"Nifty 50 Return: {comparison['nifty50']['return_pct']}%")
print(f"Correlation: {comparison['correlation']}")
```

**Claude Desktop:**
```
"Compare US and Indian markets"
"How is Nifty 50 performing vs S&P 500?"
```

### Compare Similar Companies

```python
# Compare Microsoft (US) with TCS (India)
comparison = analyzer.compare_stocks(
    "MSFT",
    "TCS.NS",
    period="1y",
    currency="USD"
)

print(f"MSFT Return: {comparison['us_stock']['return_pct']}%")
print(f"TCS Return: {comparison['indian_stock']['return_pct']}%")
print(f"Correlation: {comparison['correlation']}")
```

**Claude Desktop:**
```
"Compare Microsoft with TCS"
"Compare Apple with Infosys in INR"
```

### Cross-Market Correlation

```python
# Calculate correlation matrix for multiple stocks
correlation = analyzer.calculate_correlation(
    ["AAPL", "MSFT", "RELIANCE.NS", "TCS.NS"],
    period="1y"
)
```

---

## Currency Conversion

### Basic Conversion

```python
from maverick_mcp.utils.currency_converter import CurrencyConverter

converter = CurrencyConverter()

# INR to USD
usd_amount = converter.convert(10000, "INR", "USD")
print(f"₹10,000 = ${usd_amount:.2f}")

# USD to INR
inr_amount = converter.convert(100, "USD", "INR")
print(f"$100 = ₹{inr_amount:.2f}")
```

**Claude Desktop:**
```
"Convert 50000 INR to USD"
"How much is 1000 USD in Indian Rupees?"
```

### Get Exchange Rate

```python
rate = converter.get_exchange_rate("USD", "INR")
print(f"1 USD = ₹{rate}")
```

### Convert Price Series

```python
# Convert historical stock prices
usd_prices = converter.convert_timeseries(
    inr_prices,
    "INR",
    "USD"
)
```

---

## Examples

### Example 1: Complete Indian Market Analysis

```python
from maverick_mcp.providers.indian_market_data import IndianMarketDataProvider
from maverick_mcp.application.screening.indian_market import get_maverick_bullish_india
from maverick_mcp.providers.rbi_data import RBIDataProvider
from maverick_mcp.providers.indian_news import IndianNewsProvider

# 1. Get market status
provider = IndianMarketDataProvider()
status = provider.get_market_status()
print(f"Market Status: {status['status']}")

# 2. Get bullish stock recommendations
stocks = get_maverick_bullish_india(limit=5)
print(f"\nTop 5 Bullish Stocks:")
for stock in stocks[:5]:
    print(f"  {stock['symbol']}: ₹{stock['price']:.2f}")

# 3. Check economic indicators
rbi = RBIDataProvider()
rates = rbi.get_policy_rates()
print(f"\nRepo Rate: {rates['repo_rate']}%")

# 4. Get news sentiment for top stock
if stocks:
    news_provider = IndianNewsProvider()
    sentiment = news_provider.analyze_sentiment(stocks[0]['symbol'])
    print(f"\nTop Stock Sentiment: {sentiment['overall_sentiment']}")
```

### Example 2: Cross-Market Portfolio Analysis

```python
from maverick_mcp.analysis.market_comparison import MarketComparisonAnalyzer
from maverick_mcp.utils.currency_converter import CurrencyConverter

analyzer = MarketComparisonAnalyzer()
converter = CurrencyConverter()

# Portfolio: 50% US, 50% India
us_stocks = ["AAPL", "MSFT", "GOOGL"]
indian_stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

# Compare markets
market_comp = analyzer.compare_indices("1y")
print(f"Market Correlation: {market_comp['correlation']}")

# Calculate portfolio value in USD
portfolio_value_inr = 500000  # ₹5 lakhs in Indian stocks
portfolio_value_usd = 10000   # $10k in US stocks

indian_portion_usd = converter.convert(portfolio_value_inr, "INR", "USD")
total_portfolio_usd = portfolio_value_usd + indian_portion_usd

print(f"Total Portfolio Value: ${total_portfolio_usd:.2f}")
```

### Example 3: Sector Rotation Strategy

```python
from maverick_mcp.application.screening.indian_market import (
    get_nifty_sector_rotation,
    get_nifty_sectors
)

# Analyze sector performance
sector_analysis = get_nifty_sector_rotation(lookback_days=90, top_n=3)

print("Top Performing Sectors:")
for sector in sector_analysis['top_sectors'][:3]:
    print(f"\n{sector['name']}:")
    print(f"  Average Return: {sector['avg_return']:.2f}%")
    print(f"  Top Stocks:")
    for stock in sector['top_stocks']:
        print(f"    - {stock['symbol']}: {stock['return']:.2f}%")
```

---

## Advanced Usage

### Custom Screening with Circuit Breakers

```python
from maverick_mcp.application.screening.indian_market import calculate_circuit_breaker_limits

# Calculate circuit breaker limits for a stock
price = 1500.00
limits = calculate_circuit_breaker_limits(price)

print(f"Current Price: ₹{price}")
print(f"Upper Circuit: ₹{limits['upper_limit']}")
print(f"Lower Circuit: ₹{limits['lower_limit']}")
```

### Format Indian Currency

```python
from maverick_mcp.application.screening.indian_market import format_indian_currency

print(format_indian_currency(100000))      # ₹1.00 L (lakh)
print(format_indian_currency(10000000))    # ₹1.00 Cr (crore)
print(format_indian_currency(50000))       # ₹50,000.00
```

### Get Nifty Sectors

```python
from maverick_mcp.application.screening.indian_market import get_nifty_sectors

sectors = get_nifty_sectors()
# Returns list of 14 major Nifty sectors
```

### Historical Data with Market Calendars

```python
from maverick_mcp.config.markets import get_market_config

# Get NSE configuration
nse_config = get_market_config("RELIANCE.NS")

# Get trading calendar
calendar = nse_config.get_calendar()
trading_days = calendar.valid_days(start_date="2024-01-01", end_date="2024-12-31")

print(f"Trading days in 2024: {len(trading_days)}")
```

---

## Best Practices

### 1. Symbol Formatting

Always use correct suffixes:
- ✅ `"RELIANCE.NS"` (NSE)
- ✅ `"RELIANCE.BO"` (BSE)
- ❌ `"RELIANCE"` (will be treated as US stock)

### 2. Market Hours

Indian markets trade 9:15 AM - 3:30 PM IST:
- Check market status before analysis
- Use `get_market_status()` for real-time status

### 3. Currency Handling

Be explicit about currency:
```python
# Good: Specify currency
comparison = analyzer.compare_stocks("AAPL", "TCS.NS", currency="USD")

# Bad: Assumes default
comparison = analyzer.compare_stocks("AAPL", "TCS.NS")
```

### 4. Volume Thresholds

Indian market has lower liquidity:
- US default: 1,000,000 shares
- India default: 500,000 shares

Adjust for smaller stocks:
```python
recommendations = get_maverick_bullish_india(
    limit=10,
    min_volume=250000  # Lower threshold for small caps
)
```

### 5. Data Caching

Stock data is cached for performance:
- First call: Fetches from API
- Subsequent calls: Returns cached data
- Cache TTL: 15 minutes (trading hours), 1 hour (after hours)

### 6. Error Handling

```python
try:
    data = provider.get_stock_data("INVALID.NS")
except ValueError as e:
    print(f"Invalid symbol: {e}")
except Exception as e:
    print(f"Data fetch failed: {e}")
```

### 7. Batch Operations

Fetch multiple stocks efficiently:
```python
symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
data = {}

for symbol in symbols:
    try:
        data[symbol] = provider.get_stock_data(symbol, period="1m")
    except Exception as e:
        print(f"Failed to fetch {symbol}: {e}")
```

---

## MCP Tools Reference

All features available through Claude Desktop:

### Screening
- `get_indian_market_recommendations(strategy, limit)`
- `analyze_nifty_sectors()`
- `get_indian_market_overview()`

### Economic Data
- `get_indian_economic_indicators()`

### News & Sentiment
- `get_indian_stock_news(symbol, limit)`

### Market Comparison
- `compare_us_indian_markets(period)`
- `compare_similar_companies(us_symbol, indian_symbol, currency)`

### Currency
- `convert_currency(amount, from_currency, to_currency)`

---

## Troubleshooting

### Issue: "Invalid symbol format"

**Solution:** Ensure you're using correct suffixes (.NS or .BO)

### Issue: "Market closed"

**Solution:** Indian market is closed. Check market status first.

### Issue: "No data available"

**Solution:** Stock might be delisted or symbol incorrect. Verify on NSE/BSE website.

### Issue: "Rate limit exceeded"

**Solution:** Reduce frequency of API calls or wait a few minutes.

---

## Additional Resources

- **Phase 1**: Multi-market infrastructure - `docs/MULTI_MARKET_SUPPORT.md`
- **Phase 2**: Indian market data - `docs/PHASE2_INDIAN_MARKET.md`
- **Phase 3**: Screening strategies - `docs/PHASE3_IMPLEMENTATION.md`
- **Phase 4**: Economic indicators - `docs/PHASE4_IMPLEMENTATION.md`

---

## Support

For issues or questions:
1. Check existing documentation
2. Review examples in `examples/` directory
3. Open GitHub issue with details

---

**Last Updated:** Phase 5 - Polish & Documentation  
**Status:** Production Ready ✅

