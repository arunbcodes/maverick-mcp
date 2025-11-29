# maverick-data: Models

SQLAlchemy models for stock data, screening, and caching.

## Quick Start

```python
from maverick_data import Stock, PriceCache, SessionLocal

# Get database session
with SessionLocal() as session:
    # Query stocks
    stock = session.query(Stock).filter_by(ticker_symbol="AAPL").first()
    print(f"{stock.company_name}: ${stock.price}")
```

---

## Stock Model

Primary model for stock information.

```python
from maverick_data import Stock

# Get or create stock
stock = Stock.get_or_create(
    session,
    ticker_symbol="AAPL",
    company_name="Apple Inc.",
    sector="Technology",
    industry="Consumer Electronics"
)
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `ticker_symbol` | str | Stock symbol (e.g., "AAPL") |
| `company_name` | str | Company name |
| `sector` | str | Industry sector |
| `industry` | str | Specific industry |
| `exchange` | str | Exchange (NASDAQ, NYSE, NSE) |
| `country` | str | Country code (US, IN) |
| `currency` | str | Currency (USD, INR) |
| `market_cap` | float | Market capitalization |
| `is_active` | bool | Active trading status |

### Methods

```python
# Get or create
stock = Stock.get_or_create(session, ticker_symbol="AAPL", ...)

# Convert to dict
stock_dict = stock.to_dict()
```

---

## PriceCache Model

Cached historical price data.

```python
from maverick_data import PriceCache

# Get cached prices
prices = PriceCache.get_price_data(
    session,
    ticker="AAPL",
    start_date="2024-01-01",
    end_date="2024-01-31"
)
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `stock_id` | int | Foreign key to Stock |
| `date` | date | Trading date |
| `open` | float | Opening price |
| `high` | float | Highest price |
| `low` | float | Lowest price |
| `close` | float | Closing price |
| `volume` | int | Trading volume |

---

## Screening Models

### MaverickStocks

High-momentum bullish stocks.

```python
from maverick_data import MaverickStocks

# Get top bullish stocks
top_stocks = session.query(MaverickStocks)\
    .order_by(MaverickStocks.combined_score.desc())\
    .limit(10)\
    .all()
```

**Key Fields:**
- `combined_score`: Overall score (0-100)
- `momentum_score`: Momentum strength
- `pattern_type`: Detected pattern (VCP, breakout, etc.)
- `squeeze_status`: TTM squeeze status

### MaverickBearStocks

Weak stocks for bearish opportunities.

```python
from maverick_data import MaverickBearStocks

# Get weakest stocks
weak_stocks = session.query(MaverickBearStocks)\
    .order_by(MaverickBearStocks.score.desc())\
    .limit(10)\
    .all()
```

**Key Fields:**
- `score`: Bear score (0-100)
- `rsi_14`: RSI value
- `atr_contraction`: ATR contracting flag
- `dist_days_20`: Distribution days

### SupplyDemandBreakoutStocks

Stocks breaking out from accumulation.

```python
from maverick_data import SupplyDemandBreakoutStocks

# Get breakout candidates
breakouts = session.query(SupplyDemandBreakoutStocks)\
    .filter(SupplyDemandBreakoutStocks.momentum_score > 80)\
    .all()
```

---

## Session Management

### SessionLocal

Create database sessions:

```python
from maverick_data import SessionLocal

# Context manager (recommended)
with SessionLocal() as session:
    stocks = session.query(Stock).all()

# Manual management
session = SessionLocal()
try:
    stocks = session.query(Stock).all()
    session.commit()
finally:
    session.close()
```

### get_session / get_db

Dependency injection helpers:

```python
from maverick_data import get_session, get_db

# Simple function
def fetch_stocks():
    session = get_session()
    return session.query(Stock).all()

# FastAPI dependency
@app.get("/stocks")
def list_stocks(db: Session = Depends(get_db)):
    return db.query(Stock).all()
```

---

## Bulk Operations

Efficient bulk insert operations:

```python
from maverick_data import bulk_insert_price_data, bulk_insert_screening_data

# Bulk insert price data
count = bulk_insert_price_data(session, "AAPL", price_dataframe)
print(f"Inserted {count} records")

# Bulk insert screening data
count = bulk_insert_screening_data(session, MaverickStocks, screening_data)
```

---

## Database URL

The database URL is configured via environment variable:

```python
from maverick_data import DATABASE_URL, engine

print(f"Database: {DATABASE_URL}")
```

**Environment Variable:** `DATABASE_URL`

**Default:** `sqlite:///maverick.db`

**Production:** `postgresql://user:pass@host:port/dbname`

