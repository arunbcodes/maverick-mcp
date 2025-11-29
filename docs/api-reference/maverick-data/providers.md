# maverick-data: Providers

Data providers for fetching stock information from external sources.

## StockDataProvider

Primary interface for fetching stock data.

```python
from maverick_data.providers import StockDataProvider

provider = StockDataProvider()

# Fetch historical data
df = provider.fetch_stock_data(
    ticker="AAPL",
    start_date="2024-01-01",
    end_date="2024-06-30"
)

# Get stock info
info = provider.get_stock_info("AAPL")
print(f"Company: {info['longName']}")
print(f"Sector: {info['sector']}")
```

### Methods

#### fetch_stock_data

Fetch historical OHLCV data.

```python
df = provider.fetch_stock_data(
    ticker="AAPL",
    start_date="2024-01-01",  # Optional
    end_date="2024-06-30",    # Optional
    period="1y",              # Alternative to dates
    interval="1d"             # 1d, 1h, 5m, etc.
)
```

**Returns:** `pandas.DataFrame` with columns:
- `Open`, `High`, `Low`, `Close`, `Volume`
- Index: `DatetimeIndex`

#### get_stock_info

Get company information.

```python
info = provider.get_stock_info("AAPL")
```

**Returns:** `dict` with keys:
- `longName`, `sector`, `industry`
- `marketCap`, `previousClose`
- `exchange`, `currency`

---

## EnhancedStockDataProvider

Extended provider with caching and resilience.

```python
from maverick_data.providers import EnhancedStockDataProvider

provider = EnhancedStockDataProvider()

# Automatically uses cache and circuit breaker
df = provider.fetch_stock_data("AAPL", period="1y")
```

### Features

- **Database Caching**: Stores fetched data in PriceCache
- **Circuit Breaker**: Protects against API failures
- **Automatic Retry**: Retries on transient failures
- **Rate Limiting**: Respects API rate limits

### Cache Behavior

```python
# First call: Fetches from API, stores in cache
df1 = provider.fetch_stock_data("AAPL", period="1y")

# Second call: Returns from cache (fast)
df2 = provider.fetch_stock_data("AAPL", period="1y")

# Force refresh
df3 = provider.fetch_stock_data("AAPL", period="1y", force_refresh=True)
```

---

## YFinancePool

Connection pooling for yfinance API calls.

```python
from maverick_data.providers import YFinancePool, get_yfinance_pool

# Get singleton pool
pool = get_yfinance_pool()

# Use pool for API calls
history = pool.get_history("AAPL", period="1mo")
info = pool.get_info("AAPL")
```

### Benefits

- **Connection Reuse**: Reduces API overhead
- **Thread Safety**: Safe for concurrent use
- **Rate Limiting**: Built-in rate limiting
- **Error Handling**: Graceful error recovery

---

## Multi-Market Support

Providers support multiple markets:

```python
# US Market (default)
provider.fetch_stock_data("AAPL")

# Indian NSE
provider.fetch_stock_data("RELIANCE.NS")

# Indian BSE
provider.fetch_stock_data("TCS.BO")
```

### Market Detection

The provider automatically detects the market from the symbol:

| Suffix | Market | Exchange |
|--------|--------|----------|
| (none) | US | NASDAQ/NYSE |
| `.NS` | India | NSE |
| `.BO` | India | BSE |

---

## Error Handling

```python
from maverick_core import DataFetchError, ValidationError

try:
    df = provider.fetch_stock_data("INVALID_TICKER")
except ValidationError as e:
    print(f"Invalid ticker: {e}")
except DataFetchError as e:
    print(f"Failed to fetch data: {e}")
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `YFINANCE_RATE_LIMIT` | Requests per minute | 100 |
| `STOCK_CACHE_TTL` | Cache TTL in seconds | 3600 |

### Custom Configuration

```python
provider = EnhancedStockDataProvider(
    cache_ttl=7200,  # 2 hours
    enable_cache=True,
    circuit_breaker_enabled=True
)
```

