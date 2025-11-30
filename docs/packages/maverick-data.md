# maverick-data

Data access, caching, and persistence for Maverick MCP.

## Overview

`maverick-data` provides:

- **Database Models**: SQLAlchemy models for stocks, prices, portfolios
- **Session Management**: Sync and async database connections
- **Cache Providers**: Redis and in-memory caching
- **Data Providers**: Stock data fetching (yfinance, Tiingo)
- **Repositories**: Repository pattern for data access
- **Services**: Business logic for data operations

## Installation

```bash
pip install maverick-data
```

## Quick Start

```python
from maverick_data import (
    # Session management
    get_session, init_db, SessionLocal,
    
    # Models
    Stock, PriceCache, MaverickStocks,
    
    # Providers
    StockDataProvider, EnhancedStockDataProvider,
    
    # Services
    ScreeningService, MarketCalendarService,
)

# Initialize database
init_db()

# Fetch stock data
provider = StockDataProvider()
df = provider.fetch_stock_data("AAPL", period="1y")

# Get screening results
service = ScreeningService()
results = service.get_maverick_recommendations(limit=10)
```

## Database Configuration

### Connection String

```python
# Environment variable
DATABASE_URL=postgresql://user:pass@localhost:5432/maverick_db

# Or SQLite for development
DATABASE_URL=sqlite:///maverick.db
```

### Session Management

```python
from maverick_data import get_session, get_db, get_async_db

# Simple session (auto-closes)
with get_session() as session:
    stocks = session.query(Stock).all()

# FastAPI dependency
@app.get("/stocks")
def list_stocks(db: Session = Depends(get_db)):
    return db.query(Stock).all()

# Async session
@app.get("/stocks")
async def list_stocks(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Stock))
    return result.scalars().all()
```

### Connection Pooling

```python
from maverick_data import engine, SessionLocal

# Engine with connection pooling (configured automatically)
# - pool_size: 20
# - max_overflow: 10
# - pool_timeout: 30
# - pool_recycle: 3600
```

## Models

### Stock Model

```python
from maverick_data import Stock

# Query stocks
with get_session() as session:
    # Get by ticker
    stock = session.query(Stock).filter_by(ticker_symbol="AAPL").first()
    
    # Get all S&P 500
    sp500 = session.query(Stock).filter_by(is_sp500=True).all()
    
    # Get Indian stocks
    indian = session.query(Stock).filter(
        Stock.ticker_symbol.like("%.NS")
    ).all()
```

### Price Cache Model

```python
from maverick_data import PriceCache
from datetime import date

# Query cached prices
with get_session() as session:
    prices = session.query(PriceCache).filter(
        PriceCache.ticker_symbol == "AAPL",
        PriceCache.date >= date(2024, 1, 1)
    ).order_by(PriceCache.date).all()
    
    for price in prices:
        print(f"{price.date}: ${price.close:.2f}")
```

### Screening Models

```python
from maverick_data import (
    MaverickStocks,
    MaverickBearStocks,
    SupplyDemandBreakoutStocks
)

# Get Maverick bullish picks
with get_session() as session:
    bullish = session.query(MaverickStocks).filter(
        MaverickStocks.combined_score >= 80
    ).order_by(MaverickStocks.combined_score.desc()).limit(10).all()
    
    for stock in bullish:
        print(f"{stock.ticker_symbol}: {stock.combined_score}")
```

### Portfolio Models

```python
from maverick_data import UserPortfolio, PortfolioPosition

# Create portfolio
with get_session() as session:
    portfolio = UserPortfolio(
        user_id="default",
        name="My Portfolio"
    )
    session.add(portfolio)
    
    # Add position
    position = PortfolioPosition(
        portfolio_id=portfolio.id,
        ticker="AAPL",
        shares=10,
        cost_basis=150.00
    )
    session.add(position)
    session.commit()
```

### All Available Models

| Model | Purpose |
|-------|---------|
| `Stock` | Stock master data |
| `PriceCache` | Historical price data |
| `TechnicalCache` | Technical indicator cache |
| `MaverickStocks` | Bullish screening results |
| `MaverickBearStocks` | Bearish screening results |
| `SupplyDemandBreakoutStocks` | Breakout patterns |
| `UserPortfolio` | User portfolios |
| `PortfolioPosition` | Portfolio positions |
| `BacktestResult` | Backtest results |
| `BacktestTrade` | Individual trades |
| `OptimizationResult` | Parameter optimization |
| `ExchangeRate` | Currency exchange rates |
| `NewsArticle` | News articles |

## Providers

### StockDataProvider

Basic stock data fetching.

```python
from maverick_data.providers import StockDataProvider

provider = StockDataProvider()

# Fetch historical data
df = provider.fetch_stock_data(
    ticker="AAPL",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Get stock info
info = provider.get_stock_info("AAPL")
print(f"Name: {info['longName']}")
print(f"Sector: {info['sector']}")
print(f"Market Cap: ${info['marketCap']:,.0f}")
```

### EnhancedStockDataProvider

Production-ready provider with caching and resilience.

```python
from maverick_data.providers import EnhancedStockDataProvider

provider = EnhancedStockDataProvider()

# Automatically uses cache and circuit breaker
df = provider.fetch_stock_data("AAPL", period="1y")

# Force refresh from API
df = provider.fetch_stock_data("AAPL", period="1y", force_refresh=True)
```

### Multi-Market Support

```python
# US Market (default)
provider.fetch_stock_data("AAPL")
provider.fetch_stock_data("MSFT")

# Indian NSE
provider.fetch_stock_data("RELIANCE.NS")
provider.fetch_stock_data("TCS.NS")

# Indian BSE
provider.fetch_stock_data("RELIANCE.BO")
```

### MarketDataProvider

Market indices and sector data.

```python
from maverick_data.providers import MarketDataProvider

market = MarketDataProvider()

# Get market overview
overview = market.get_market_overview()

# Get sector performance
sectors = market.get_sector_performance()

# Get market breadth
breadth = market.get_market_breadth()
```

### MacroDataProvider

Economic indicators and macro data.

```python
from maverick_data.providers import MacroDataProvider

macro = MacroDataProvider()

# Get economic indicators
gdp = macro.get_gdp_growth()
inflation = macro.get_inflation_rate()
unemployment = macro.get_unemployment_rate()

# Get interest rates
rates = macro.get_interest_rates()
```

## Services

### ScreeningService

Stock screening with multiple strategies.

```python
from maverick_data.services import ScreeningService

service = ScreeningService()

# Maverick bullish picks
bullish = service.get_maverick_recommendations(limit=20)
for stock in bullish:
    print(f"{stock['ticker_symbol']}: Score {stock['combined_score']}")

# Maverick bearish picks
bearish = service.get_maverick_bear_recommendations(limit=20)

# Supply/demand breakouts
breakouts = service.get_supply_demand_breakouts(limit=20)
```

### MarketCalendarService

Market hours, holidays, and trading days.

```python
from maverick_data.services import MarketCalendarService

calendar = MarketCalendarService()

# Check if trading day
is_trading = calendar.is_trading_day("2024-01-15", "NYSE")

# Get trading days
trading_days = calendar.get_trading_days(
    "2024-01-01", "2024-01-31", "NYSE"
)

# Get market hours
hours = calendar.get_market_hours("NYSE")
print(f"Open: {hours['open']}, Close: {hours['close']}")

# NSE market
nse_hours = calendar.get_market_hours("NSE")
print(f"NSE: {nse_hours['open']} - {nse_hours['close']} IST")
```

### StockCacheManager

Database-backed caching for stock data.

```python
from maverick_data.services import StockCacheManager

cache = StockCacheManager()

# Get cached data
df = cache.get_cached_data("AAPL", "2024-01-01", "2024-12-31")

if df is None:
    # Fetch and cache
    df = provider.fetch_stock_data("AAPL", ...)
    cache.cache_data("AAPL", df)
```

### StockDataFetcher

Low-level data fetching with circuit breaker.

```python
from maverick_data.services import StockDataFetcher

fetcher = StockDataFetcher()

# Fetch with automatic retry and circuit breaker
df = await fetcher.fetch_data("AAPL", period="1y")
```

## Cache Providers

### Redis Cache

```python
from maverick_data.cache import RedisCache

cache = RedisCache(url="redis://localhost:6379")

# Set with TTL
cache.set("key", {"data": "value"}, ttl=3600)

# Get
data = cache.get("key")

# Delete
cache.delete("key")
```

### Memory Cache

```python
from maverick_data.cache import MemoryCache

cache = MemoryCache(max_size=1000)

# Same interface as Redis
cache.set("key", {"data": "value"}, ttl=3600)
data = cache.get("key")
```

### Cache Manager

```python
from maverick_data import get_cache_manager

# Get singleton cache manager
cache = get_cache_manager()

# Uses Redis if available, falls back to memory
cache.set("stock:AAPL", df.to_dict(), ttl=3600)
data = cache.get("stock:AAPL")
```

## Repositories

Repository pattern for clean data access.

### StockRepository

```python
from maverick_data.repositories import StockRepository

repo = StockRepository(session)

# Get stock
stock = repo.get_by_ticker("AAPL")

# Get multiple
stocks = repo.get_by_tickers(["AAPL", "MSFT", "GOOGL"])

# Get S&P 500
sp500 = repo.get_sp500_stocks()

# Search
results = repo.search("Apple")
```

### PortfolioRepository

```python
from maverick_data.repositories import PortfolioRepository

repo = PortfolioRepository(session)

# Get user's portfolios
portfolios = repo.get_by_user("default")

# Get with positions
portfolio = repo.get_with_positions(portfolio_id)

# Add position
repo.add_position(portfolio_id, "AAPL", 10, 150.00)

# Calculate performance
performance = repo.calculate_performance(portfolio_id, current_prices)
```

### ScreeningRepository

```python
from maverick_data.repositories import ScreeningRepository

repo = ScreeningRepository(session)

# Get top stocks by strategy
maverick = repo.get_top_maverick(limit=20)
bearish = repo.get_top_bearish(limit=20)
breakouts = repo.get_top_breakouts(limit=20)

# Filter by criteria
filtered = repo.filter_by_criteria(
    min_score=80,
    max_price=100,
    sectors=["Technology", "Healthcare"]
)
```

## Bulk Operations

Efficient bulk data operations.

```python
from maverick_data import (
    bulk_insert_price_data,
    bulk_insert_screening_data,
    get_latest_maverick_screening
)

# Bulk insert prices
bulk_insert_price_data(session, [
    {"ticker": "AAPL", "date": "2024-01-15", "close": 185.50, ...},
    {"ticker": "AAPL", "date": "2024-01-16", "close": 186.20, ...},
])

# Bulk insert screening
bulk_insert_screening_data(session, "maverick", [
    {"ticker": "AAPL", "combined_score": 92, ...},
    {"ticker": "MSFT", "combined_score": 88, ...},
])

# Get latest screening date
latest = get_latest_maverick_screening(session)
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection | `sqlite:///maverick.db` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379` |
| `STOCK_CACHE_TTL` | Cache TTL in seconds | `3600` |
| `YFINANCE_RATE_LIMIT` | API rate limit | `100` |

### Custom Configuration

```python
from maverick_data.providers import EnhancedStockDataProvider

provider = EnhancedStockDataProvider(
    cache_ttl=7200,           # 2 hours
    enable_cache=True,
    circuit_breaker_enabled=True,
    max_retries=3
)
```

## Testing

### Test Fixtures

```python
import pytest
from maverick_data import init_db, get_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def test_session():
    """In-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
```

### Mocking Providers

```python
from unittest.mock import Mock, patch
import pandas as pd

def test_fetch_stock_data():
    with patch('maverick_data.providers.yfinance') as mock_yf:
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame({
            "Close": [100, 101, 102]
        })
        mock_yf.Ticker.return_value = mock_ticker
        
        provider = StockDataProvider()
        df = provider.fetch_stock_data("AAPL")
        
        assert len(df) == 3
```

## API Reference

For detailed API documentation, see:

- [Models API](../api-reference/maverick-data/models.md)
- [Providers API](../api-reference/maverick-data/providers.md)
- [Services API](../api-reference/maverick-data/services.md)

