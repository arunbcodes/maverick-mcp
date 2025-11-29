# maverick-data: Services

Business logic services for stock data operations.

## StockDataFetcher

Low-level service for fetching data from external sources.

```python
from maverick_data.services import StockDataFetcher

fetcher = StockDataFetcher()

# Fetch historical data
df = fetcher.fetch_stock_data("AAPL", period="1y")

# Fetch real-time quote
quote = fetcher.fetch_realtime_data("AAPL")
print(f"Price: ${quote['price']}, Change: {quote['change_percent']}%")

# Fetch multiple symbols
quotes = fetcher.fetch_multiple_realtime(["AAPL", "GOOGL", "MSFT"])
```

### Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `fetch_stock_data()` | Historical OHLCV | DataFrame |
| `fetch_stock_info()` | Company info | dict |
| `fetch_realtime_data()` | Current quote | dict |
| `fetch_multiple_realtime()` | Multiple quotes | dict |
| `fetch_news()` | Stock news | DataFrame |
| `fetch_earnings()` | Earnings data | dict |
| `is_etf()` | Check if ETF | bool |

---

## StockCacheManager

Database-backed caching for stock data.

```python
from maverick_data.services import StockCacheManager

cache = StockCacheManager()

# Get cached data
df = cache.get_cached_data("AAPL", "2024-01-01", "2024-06-30")

if df is None:
    # Fetch and cache
    df = fetcher.fetch_stock_data("AAPL", ...)
    cache.cache_data("AAPL", df)
```

### Methods

#### get_cached_data

Retrieve cached price data.

```python
df = cache.get_cached_data(
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2024-06-30"
)
```

**Returns:** `DataFrame` or `None` if not cached

#### cache_data

Store price data in cache.

```python
rows_cached = cache.cache_data("AAPL", df)
print(f"Cached {rows_cached} rows")
```

#### invalidate_cache

Clear cached data.

```python
# Invalidate specific symbol
cache.invalidate_cache("AAPL")

# Invalidate all
cache.invalidate_cache(None)
```

---

## ScreeningService

Stock screening based on technical patterns.

```python
from maverick_data.services import ScreeningService

service = ScreeningService()

# Get bullish recommendations
bullish = service.get_maverick_recommendations(limit=20, min_score=80)

# Get bearish recommendations
bearish = service.get_maverick_bear_recommendations(limit=20)

# Get breakout candidates
breakouts = service.get_supply_demand_breakout_recommendations(limit=20)

# Get all screening results
all_results = service.get_all_screening_recommendations()
```

### Recommendation Format

```python
{
    "ticker_symbol": "AAPL",
    "combined_score": 95,
    "momentum_score": 92,
    "recommendation_type": "maverick_bullish",
    "reason": "Exceptional combined score (95), outstanding relative strength",
    "pattern_type": "VCP",
    "squeeze_status": "high"
}
```

---

## MarketCalendarService

Trading day and market hours detection.

```python
from maverick_data.services import MarketCalendarService

calendar = MarketCalendarService()

# Check if trading day
is_trading = calendar.is_trading_day("2024-01-15")

# Get trading days in range
trading_days = calendar.get_trading_days("2024-01-01", "2024-01-31")
print(f"Trading days: {len(trading_days)}")

# Get last trading day
last_day = calendar.get_last_trading_day("2024-01-07")  # Sunday -> Friday

# Check if market is open
is_open = calendar.is_market_open()
```

### Multi-Market Support

```python
# US market (default)
calendar.is_trading_day("2024-07-04")  # False (Independence Day)

# Indian market
calendar.is_trading_day("2024-01-26", symbol="RELIANCE.NS")  # False (Republic Day)
```

---

## Service Dependency Injection

For FastAPI applications:

```python
from fastapi import Depends
from maverick_data.services import (
    StockDataFetcher,
    StockCacheManager,
    ScreeningService,
)

def get_fetcher() -> StockDataFetcher:
    return StockDataFetcher()

def get_cache() -> StockCacheManager:
    return StockCacheManager()

@app.get("/stocks/{ticker}")
def get_stock(
    ticker: str,
    fetcher: StockDataFetcher = Depends(get_fetcher),
    cache: StockCacheManager = Depends(get_cache)
):
    # Try cache first
    df = cache.get_cached_data(ticker, ...)
    if df is None:
        df = fetcher.fetch_stock_data(ticker, ...)
        cache.cache_data(ticker, df)
    return df.to_dict()
```

---

## Best Practices

### 1. Use Caching for Repeated Queries

```python
# Good: Check cache first
df = cache.get_cached_data(ticker, start, end)
if df is None:
    df = fetcher.fetch_stock_data(ticker, start, end)
    cache.cache_data(ticker, df)
```

### 2. Batch Operations for Multiple Symbols

```python
# Good: Batch fetch
quotes = fetcher.fetch_multiple_realtime(["AAPL", "GOOGL", "MSFT"])

# Bad: Individual fetches
for symbol in symbols:
    quote = fetcher.fetch_realtime_data(symbol)
```

### 3. Handle Market Hours

```python
calendar = MarketCalendarService()

if calendar.is_market_open():
    # Fetch real-time data
    quote = fetcher.fetch_realtime_data(ticker)
else:
    # Use cached data
    df = cache.get_cached_data(ticker, ...)
```

