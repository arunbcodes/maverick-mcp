# maverick-india: Market

Indian stock market support for NSE and BSE exchanges.

## Quick Start

```python
from maverick_india import IndianMarket, INDIAN_MARKET_CONFIG

# Get market configuration
nse_config = INDIAN_MARKET_CONFIG["NSE"]
print(f"Currency: {nse_config['currency']}")
print(f"Trading Hours: {nse_config['trading_hours']}")

# Check if Indian symbol
market = IndianMarket()
is_indian = market.is_indian_symbol("RELIANCE.NS")  # True
```

---

## Supported Markets

### NSE (National Stock Exchange)

```python
# Symbol format
symbol = "RELIANCE.NS"

# Configuration
{
    "exchange": "NSE",
    "country": "IN",
    "currency": "INR",
    "trading_hours": "09:15-15:30",
    "timezone": "Asia/Kolkata",
    "circuit_breaker": 0.10  # 10%
}
```

### BSE (Bombay Stock Exchange)

```python
# Symbol format
symbol = "TCS.BO"

# Configuration
{
    "exchange": "BSE",
    "country": "IN",
    "currency": "INR",
    "trading_hours": "09:15-15:30",
    "timezone": "Asia/Kolkata"
}
```

---

## Market Configuration

```python
from maverick_india.market import INDIAN_MARKET_CONFIG, get_market_for_symbol

# Get config for symbol
config = get_market_for_symbol("RELIANCE.NS")
print(f"Exchange: {config['exchange']}")
print(f"Currency: {config['currency']}")

# All NSE stocks
NSE_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
    "ICICIBANK.NS", "HINDUNILVR.NS", "ITC.NS", "SBIN.NS"
]
```

---

## Indian Stock Screening

```python
from maverick_india.screening import (
    get_maverick_bullish_india,
    get_nifty50_momentum,
    get_nifty_sector_rotation
)

# Bullish Indian stocks
bullish = get_maverick_bullish_india(limit=10)

# Nifty 50 momentum plays
momentum = get_nifty50_momentum(limit=15)

# Sector rotation analysis
sectors = get_nifty_sector_rotation(lookback_days=90)
for sector in sectors['top_sectors'][:3]:
    print(f"{sector['name']}: {sector['avg_return']:.2%}")
```

---

## Economic Indicators

```python
from maverick_india.economic import RBIDataProvider

rbi = RBIDataProvider()

# Get RBI policy rates
rates = rbi.get_policy_rates()
print(f"Repo Rate: {rates['repo_rate']}%")
print(f"Reverse Repo: {rates['reverse_repo_rate']}%")
print(f"CRR: {rates['crr']}%")
print(f"SLR: {rates['slr']}%")

# Get GDP data
gdp = rbi.get_gdp_growth()
print(f"GDP Growth: {gdp['current']}%")

# Get forex reserves
forex = rbi.get_forex_reserves()
print(f"Reserves: ${forex['total_reserves_usd']:.2f}B")
```

---

## Currency Conversion

```python
from maverick_india.currency import CurrencyConverter

converter = CurrencyConverter()

# INR to USD
usd = converter.convert(100000, "INR", "USD")
print(f"₹1,00,000 = ${usd:.2f}")

# USD to INR
inr = converter.convert(1000, "USD", "INR")
print(f"$1,000 = ₹{inr:.2f}")

# Get exchange rate
rate = converter.get_exchange_rate("USD", "INR")
print(f"1 USD = ₹{rate:.2f}")
```

---

## Indian News

```python
from maverick_india.news import IndianNewsProvider

news = IndianNewsProvider()

# Get stock news
articles = news.get_stock_news("RELIANCE.NS", limit=10)
for article in articles:
    print(f"{article['title']} - {article['sentiment']}")

# Analyze sentiment
sentiment = news.analyze_sentiment("TCS.NS", period="7d")
print(f"Overall: {sentiment['overall_sentiment']}")
print(f"Score: {sentiment['sentiment_score']:.2f}")
```

---

## Market Comparison

```python
from maverick_india.comparison import MarketComparisonAnalyzer

analyzer = MarketComparisonAnalyzer()

# Compare US and Indian indices
comparison = analyzer.compare_indices(period="1y")
print(f"S&P 500: {comparison['sp500']['return_pct']:.2%}")
print(f"Nifty 50: {comparison['nifty50']['return_pct']:.2%}")
print(f"Correlation: {comparison['correlation']:.2f}")

# Compare similar companies
comp = analyzer.compare_stocks("MSFT", "TCS.NS", currency="USD")
print(f"MSFT Return: {comp['us_stock']['return_pct']:.2%}")
print(f"TCS Return: {comp['indian_stock']['return_pct']:.2%}")
```

---

## Best Practices

### Symbol Formatting

```python
# ✅ Correct
"RELIANCE.NS"  # NSE
"TCS.BO"       # BSE

# ❌ Incorrect
"RELIANCE"     # Missing suffix (treated as US stock)
"reliance.ns"  # Should be uppercase
```

### Market Hours

Indian markets: 9:15 AM - 3:30 PM IST

```python
from maverick_india.market import is_market_open

if is_market_open():
    # Fetch real-time data
    pass
else:
    # Use cached data
    pass
```

### Volume Thresholds

Indian markets have lower liquidity than US:

```python
# US default: 1,000,000 shares
# India default: 500,000 shares

bullish = get_maverick_bullish_india(
    limit=10,
    min_volume=250000  # Lower for small caps
)
```

