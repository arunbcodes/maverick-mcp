# Data API Reference

Data models, caching, and session management.

## Module: maverick_mcp.data.models

Database models for stock data, screening, and cache.

### Stock

Primary stock data model with S&P 500 pre-seeded data.

**Fields**:
- `id` (int): Primary key
- `ticker` (str): Stock symbol (e.g., "AAPL", "RELIANCE.NS")
- `name` (str): Company name
- `sector` (str): Industry sector
- `industry` (str): Specific industry
- `market_cap` (float): Market capitalization
- `price` (float): Current/last price
- `change_percent` (float): Daily change percentage
- `volume` (int): Trading volume
- `updated_at` (datetime): Last data update
- `market` (str): Market exchange (e.g., "US", "NSE", "BSE")

**Relationships**:
- `price_history`: One-to-many with StockPrice
- `screening_scores`: One-to-many with ScreeningScore

**Example**:
```python
from maverick_mcp.data.models import Stock
from maverick_mcp.data.session_management import get_session

session = get_session()
stock = session.query(Stock).filter_by(ticker="AAPL").first()
print(f"{stock.name}: ${stock.price}")
```

---

### StockPrice

Historical price data with OHLCV.

**Fields**:
- `id` (int): Primary key
- `stock_id` (int): Foreign key to Stock
- `date` (date): Trading date
- `open` (float): Opening price
- `high` (float): Highest price
- `low` (float): Lowest price
- `close` (float): Closing price
- `volume` (int): Trading volume
- `adjusted_close` (float): Split/dividend adjusted close

**Indexes**:
- Composite index on (stock_id, date) for fast queries
- Date index for time-series queries

**Example**:
```python
from maverick_mcp.data.models import Stock, StockPrice
from datetime import datetime, timedelta

# Get last 30 days of prices
thirty_days_ago = datetime.now() - timedelta(days=30)
prices = session.query(StockPrice).join(Stock).filter(
    Stock.ticker == "AAPL",
    StockPrice.date >= thirty_days_ago
).order_by(StockPrice.date).all()
```

---

### ScreeningScore

Pre-calculated screening strategy scores for S&P 500 stocks.

**Fields**:
- `id` (int): Primary key
- `stock_id` (int): Foreign key to Stock
- `strategy` (str): Strategy name (e.g., "maverick_bullish")
- `score` (float): Score 0-100
- `signals` (JSON): Strategy-specific signals
- `calculated_at` (datetime): Score calculation timestamp
- `metadata` (JSON): Additional strategy data

**Strategies**:
- `maverick_bullish`: High momentum stocks
- `maverick_bearish`: Weak stocks to avoid
- `supply_demand_breakout`: Breakout candidates

**Example**:
```python
from maverick_mcp.data.models import ScreeningScore

# Get top 10 bullish stocks
top_bullish = session.query(ScreeningScore).filter(
    ScreeningScore.strategy == "maverick_bullish"
).order_by(ScreeningScore.score.desc()).limit(10).all()

for score in top_bullish:
    print(f"{score.stock.ticker}: {score.score}/100")
```

---

### CacheEntry

Generic cache storage for API responses.

**Fields**:
- `id` (int): Primary key
- `key` (str): Cache key (unique)
- `value` (Text/JSON): Cached value
- `expires_at` (datetime): Expiration timestamp
- `created_at` (datetime): Creation timestamp

**TTL Settings**:
- Stock data: 1 hour
- Screening: 24 hours
- Research: 24 hours
- Conference calls: 7 days

---

## Module: maverick_mcp.data.cache

Multi-tier caching system.

### CacheManager

Unified caching interface with Redis + Database fallback.

**Class**: `CacheManager`

**Methods**:

#### get()

Retrieve cached value.

**Signature**:
```python
def get(self, key: str) -> Any | None
```

**Parameters**:
- `key` (str): Cache key

**Returns**:
- Any: Cached value if found and not expired
- None: If not found or expired

**Cache Tiers**:
1. Redis (L1): < 1ms
2. Database (L2): < 100ms
3. Miss: Returns None

**Example**:
```python
from maverick_mcp.data.cache import CacheManager

cache = CacheManager()
value = cache.get("stock:AAPL:quote")
if value is None:
    value = fetch_from_api()
    cache.set("stock:AAPL:quote", value, ttl=3600)
```

---

#### set()

Store value in cache.

**Signature**:
```python
def set(self, key: str, value: Any, ttl: int = 3600) -> bool
```

**Parameters**:
- `key` (str): Cache key
- `value` (Any): Value to cache (must be JSON-serializable)
- `ttl` (int, optional): Time-to-live in seconds. Default: 3600 (1 hour)

**Returns**:
- bool: True if successfully cached

**Storage**:
- Redis: Primary storage (if available)
- Database: Fallback storage (always)

---

#### delete()

Remove cached value.

**Signature**:
```python
def delete(self, key: str) -> bool
```

**Parameters**:
- `key` (str): Cache key to delete

**Returns**:
- bool: True if deleted

---

#### clear()

Clear all cache entries.

**Signature**:
```python
def clear(self, pattern: str = "*") -> int
```

**Parameters**:
- `pattern` (str, optional): Key pattern to clear. Default: "*" (all)

**Returns**:
- int: Number of entries cleared

**Example**:
```python
# Clear all stock data cache
cache.clear("stock:*")

# Clear specific ticker
cache.clear("stock:AAPL:*")
```

---

## Module: maverick_mcp.data.session_management

Database session handling.

### get_session()

Get database session (SQLAlchemy).

**Signature**:
```python
def get_session() -> Session
```

**Returns**:
- Session: SQLAlchemy database session

**Usage**:
```python
from maverick_mcp.data.session_management import get_session

session = get_session()
try:
    # Perform database operations
    stocks = session.query(Stock).all()
finally:
    session.close()
```

**Context Manager**:
```python
from maverick_mcp.data.session_management import session_scope

with session_scope() as session:
    stocks = session.query(Stock).filter_by(sector="Technology").all()
# Session automatically closed
```

---

### session_scope()

Context manager for database sessions.

**Signature**:
```python
@contextmanager
def session_scope() -> Iterator[Session]
```

**Yields**:
- Session: Database session

**Features**:
- Automatic commit on success
- Automatic rollback on error
- Automatic session cleanup

---

## Module: maverick_mcp.data.performance

Performance monitoring and optimization.

### PerformanceTracker

Track query performance and cache hit rates.

**Methods**:

#### track_query()

Record query execution time.

**Signature**:
```python
def track_query(self, query_type: str, duration: float)
```

**Parameters**:
- `query_type` (str): Query category (e.g., "stock_data", "screening")
- `duration` (float): Execution time in seconds

---

#### track_cache_hit()

Record cache hit.

**Signature**:
```python
def track_cache_hit(self, cache_key: str)
```

---

#### track_cache_miss()

Record cache miss.

**Signature**:
```python
def track_cache_miss(self, cache_key: str)
```

---

#### get_stats()

Get performance statistics.

**Signature**:
```python
def get_stats(self) -> dict
```

**Returns**:
- dict: Performance metrics including:
  - Average query times by type
  - Cache hit rate
  - Total queries
  - Total cache operations

---

## Module: maverick_mcp.data.validation

Data validation and sanitization.

### validate_ticker()

Validate stock ticker format.

**Signature**:
```python
def validate_ticker(ticker: str) -> str
```

**Parameters**:
- `ticker` (str): Stock symbol to validate

**Returns**:
- str: Validated and normalized ticker

**Raises**:
- ValueError: If ticker is invalid

**Rules**:
- 1-5 characters for US stocks
- Can include .NS (Indian NSE) or .BO (Indian BSE) suffix
- Uppercase only
- Alphanumeric plus hyphen and dot

**Example**:
```python
from maverick_mcp.data.validation import validate_ticker

ticker = validate_ticker("aapl")  # Returns "AAPL"
ticker = validate_ticker("reliance.ns")  # Returns "RELIANCE.NS"
ticker = validate_ticker("brk.b")  # Returns "BRK.B"
```

---

### validate_date_range()

Validate date range for historical data.

**Signature**:
```python
def validate_date_range(
    start_date: str | datetime,
    end_date: str | datetime
) -> tuple[datetime, datetime]
```

**Parameters**:
- `start_date`: Start date (YYYY-MM-DD string or datetime)
- `end_date`: End date (YYYY-MM-DD string or datetime)

**Returns**:
- tuple[datetime, datetime]: Validated start and end dates

**Raises**:
- ValueError: If dates are invalid or range is invalid

**Rules**:
- start_date must be before end_date
- Dates cannot be in the future
- Maximum range: 10 years

---

## Best Practices

### Database Sessions

**Always use context managers**:
```python
# Good
with session_scope() as session:
    stocks = session.query(Stock).all()

# Bad - may leak connections
session = get_session()
stocks = session.query(Stock).all()
session.close()  # Easy to forget
```

### Caching Strategy

**Cache expensive operations**:
```python
from maverick_mcp.data.cache import CacheManager

cache = CacheManager()

def get_stock_data(ticker: str):
    cache_key = f"stock:{ticker}:data"
    
    # Try cache first
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Fetch and cache
    data = expensive_api_call(ticker)
    cache.set(cache_key, data, ttl=3600)  # 1 hour
    return data
```

### Bulk Operations

**Use batch inserts for performance**:
```python
from maverick_mcp.data.models import StockPrice
from maverick_mcp.data.session_management import session_scope

# Good - batch insert
with session_scope() as session:
    prices = [StockPrice(stock_id=1, date=d, close=p) 
              for d, p in data]
    session.bulk_save_objects(prices)

# Bad - individual inserts
for d, p in data:
    with session_scope() as session:
        price = StockPrice(stock_id=1, date=d, close=p)
        session.add(price)
```

### Query Optimization

**Use eager loading for relationships**:
```python
from sqlalchemy.orm import joinedload

# Good - single query
stocks = session.query(Stock).options(
    joinedload(Stock.price_history)
).all()

# Bad - N+1 queries
stocks = session.query(Stock).all()
for stock in stocks:
    prices = stock.price_history  # Separate query each time
```
