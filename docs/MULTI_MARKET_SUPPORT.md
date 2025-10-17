# Multi-Market Support Documentation

## Overview

MaverickMCP now supports multiple stock exchanges, enabling analysis of stocks from:
- **US Markets**: NASDAQ, NYSE (default)
- **Indian Markets**: NSE (National Stock Exchange of India), BSE (Bombay Stock Exchange)

This Phase 1 implementation provides the foundation for multi-market functionality, with automatic market detection, market-specific trading calendars, and proper currency/timezone handling.

## Features

### Automatic Market Detection
The system automatically detects which market a stock belongs to based on its ticker symbol suffix:

- **No suffix** or **US tickers** → US Market (e.g., `AAPL`, `MSFT`, `GOOGL`)
- **.NS suffix** → Indian NSE Market (e.g., `RELIANCE.NS`, `TCS.NS`, `INFY.NS`)
- **.BO suffix** → Indian BSE Market (e.g., `SENSEX.BO`, `TCS.BO`)

### Market-Specific Configurations

Each market has its own configuration including:

| Market | Currency | Trading Hours (Local) | Circuit Breaker | Settlement | Timezone |
|--------|----------|----------------------|-----------------|------------|----------|
| US | USD | 9:30 AM - 4:00 PM | 7% | T+2 | America/New_York |
| NSE (India) | INR | 9:15 AM - 3:30 PM | 10% | T+1 | Asia/Kolkata |
| BSE (India) | INR | 9:15 AM - 3:30 PM | 10% | T+1 | Asia/Kolkata |

### Market-Aware Trading Calendars

The system uses appropriate trading calendars for each market:
- **US**: NYSE calendar (includes US holidays and weekends)
- **India**: NSE calendar (includes Indian holidays and weekends)

This ensures accurate cache handling on market-specific non-trading days.

## Usage

### For Developers

#### Importing Market Configuration

```python
from maverick_mcp.config.markets import (
    Market,
    get_market_from_symbol,
    get_market_config,
    is_indian_market,
    is_us_market,
)

# Detect market from symbol
market = get_market_from_symbol("RELIANCE.NS")  # Returns Market.INDIA_NSE

# Get full market configuration
config = get_market_config("RELIANCE.NS")
print(config.currency)  # "INR"
print(config.trading_hours_start)  # time(9, 15)

# Quick market checks
is_indian_market("RELIANCE.NS")  # True
is_us_market("AAPL")  # True
```

#### Creating Stocks in Database

The `Stock.get_or_create()` method automatically detects and sets the market:

```python
from maverick_mcp.data.models import Stock, SessionLocal

with SessionLocal() as session:
    # US stock - market auto-detected as "US"
    us_stock = Stock.get_or_create(
        session,
        ticker_symbol="AAPL",
        company_name="Apple Inc.",
        sector="Technology"
    )
    print(us_stock.market)  # "US"
    print(us_stock.currency)  # "USD"
    
    # Indian NSE stock - market auto-detected as "NSE"
    indian_stock = Stock.get_or_create(
        session,
        ticker_symbol="RELIANCE.NS",
        company_name="Reliance Industries Ltd.",
        sector="Energy"
    )
    print(indian_stock.market)  # "NSE"
    print(indian_stock.currency)  # "INR"
```

#### Using Market-Aware Data Provider

The `EnhancedStockDataProvider` automatically uses the correct market calendar:

```python
from maverick_mcp.providers.stock_data import EnhancedStockDataProvider

provider = EnhancedStockDataProvider()

# Automatically uses NYSE calendar for US stocks
us_data = provider.get_stock_data("AAPL", start_date="2024-01-01", end_date="2024-12-31")

# Automatically uses NSE calendar for Indian stocks
indian_data = provider.get_stock_data("RELIANCE.NS", start_date="2024-01-01", end_date="2024-12-31")
```

### Database Schema

#### New Fields in `mcp_stocks` Table

| Field | Type | Description | Example Values |
|-------|------|-------------|----------------|
| `market` | String(10) | Market identifier | "US", "NSE", "BSE" |
| `ticker_symbol` | String(20) | Extended to support suffixes | "AAPL", "RELIANCE.NS" |
| `country` | String(2) | ISO 3166-1 alpha-2 code | "US", "IN" |
| `currency` | String(3) | ISO 4217 currency code | "USD", "INR" |

#### New Indexes

For efficient multi-market queries, the following composite indexes were added:
- `idx_stock_market_country` - Query by market and country
- `idx_stock_market_sector` - Query by market and sector
- `idx_stock_country_active` - Query by country and active status
- `idx_stock_market` - Quick market filtering

## Migration

### Applying the Migration

The database migration is included in `alembic/versions/014_add_multi_market_support.py`.

To apply it:

```bash
# Run migrations
make migrate

# Or manually
alembic upgrade head
```

### Migration Details

The migration:
1. ✅ Adds `market` column (defaults to "US" for existing stocks)
2. ✅ Extends `ticker_symbol` from String(10) to String(20)
3. ✅ Standardizes `country` to 2-letter ISO codes
4. ✅ Creates composite indexes for multi-market queries
5. ✅ **Backward Compatible**: All existing S&P 500 stocks remain functional

### Rollback

If needed, you can rollback the migration:

```bash
alembic downgrade -1
```

## Testing

### Running Tests

```bash
# Run unit tests (fast, no database required)
pytest tests/test_multi_market.py -v -m "not integration"

# Run integration tests (requires database)
pytest tests/test_multi_market.py -v -m "integration"

# Run all tests
pytest tests/test_multi_market.py -v
```

### Test Coverage

The test suite covers:
- ✅ Market registry and configuration
- ✅ Market detection from symbols
- ✅ Market-specific helpers (is_indian_market, is_us_market)
- ✅ Symbol formatting and suffix handling
- ✅ Calendar loading and fallback behavior
- ✅ Database model integration
- ✅ Stock data provider integration
- ✅ End-to-end workflows for all markets

## Architecture

### Market Registry Pattern

The system uses a centralized **Market Registry** pattern (`maverick_mcp/config/markets.py`) that:
- Defines all supported markets in a single location
- Provides market-specific configurations
- Enables easy addition of new markets in the future
- Ensures consistency across the codebase

### Key Design Principles

1. **Backward Compatibility**: Existing US market functionality unchanged
2. **Auto-Detection**: Markets detected from symbol suffixes automatically
3. **Extensibility**: Easy to add new markets (UK, EU, Japan, etc.)
4. **Type Safety**: Enum-based market selection prevents errors
5. **Performance**: Lazy-loaded calendars with caching

## Future Enhancements (Phase 2+)

### Phase 2: Indian Market Data Integration
- Seed Nifty 500 and BSE stocks into database
- Add Indian market screening strategies
- Integrate with yfinance for Indian stock data

### Phase 3: Indian Market Screening
- Adapt screening strategies for Indian market volatility
- Implement sector rotation for NIFTY sectors
- Add Indian-specific technical indicators

### Phase 4: Advanced Features
- RBI (Reserve Bank of India) economic data
- Indian news sentiment analysis
- Currency conversion (INR/USD)
- Market comparison tools (US vs India)

## Troubleshooting

### Common Issues

#### Calendar Not Loading

If you see warnings about calendar loading:

```
Could not load calendar 'NSE' for National Stock Exchange of India
```

**Solution**: The system automatically falls back to NYSE calendar. Indian market calendars may require additional `pandas_market_calendars` configuration.

#### Symbol Detection Issues

If market is not detected correctly:

```python
# Ensure proper symbol format
"RELIANCE.NS"  # ✅ Correct
"RELIANCE"     # ⚠️  Will be treated as US stock
"reliance.ns"  # ✅ Works (case insensitive)
```

#### Migration Conflicts

If migration fails due to conflicts:

```bash
# Check current migration status
alembic current

# View migration history
alembic history

# Resolve conflicts manually or reset
alembic stamp head
```

## API Changes

### Breaking Changes

**None** - This is a backward-compatible change. All existing code continues to work without modification.

### New APIs

```python
# New in maverick_mcp.config.markets
from maverick_mcp.config.markets import (
    Market,                    # Enum for markets
    MarketConfig,              # Market configuration class
    MARKET_CONFIGS,            # Dictionary of all configs
    get_market_from_symbol,    # Detect market from symbol
    get_market_config,         # Get config for symbol
    get_all_markets,           # List all markets
    get_markets_by_country,    # Filter by country
    is_indian_market,          # Quick check for Indian markets
    is_us_market,              # Quick check for US market
)
```

### Modified APIs

```python
# EnhancedStockDataProvider - No API changes, enhanced internally
provider = EnhancedStockDataProvider()
# Now automatically uses correct market calendar based on symbol
data = provider.get_stock_data("RELIANCE.NS")  # Uses NSE calendar

# Stock.get_or_create - Auto-detects market, country, currency
Stock.get_or_create(session, "RELIANCE.NS", company_name="Reliance")
# market="NSE", country="IN", currency="INR" set automatically
```

## Contributing

When adding support for new markets:

1. Add market to `Market` enum in `markets.py`
2. Create `MarketConfig` in `MARKET_CONFIGS`
3. Add tests in `tests/test_multi_market.py`
4. Update this documentation
5. Create appropriate seeding scripts (if needed)

Example for adding UK market:

```python
# In maverick_mcp/config/markets.py
class Market(Enum):
    US = "US"
    INDIA_NSE = "NSE"
    INDIA_BSE = "BSE"
    UK_LSE = "LSE"  # New market

MARKET_CONFIGS[Market.UK_LSE] = MarketConfig(
    name="London Stock Exchange",
    country="GB",
    currency="GBP",
    timezone="Europe/London",
    calendar_name="LSE",
    symbol_suffix=".L",
    trading_hours_start=time(8, 0),
    trading_hours_end=time(16, 30),
    circuit_breaker_percent=8.0,
    settlement_cycle="T+2",
    min_tick_size=0.01,
)
```

## Resources

- [pandas_market_calendars Documentation](https://pandas-market-calendars.readthedocs.io/)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [NSE India](https://www.nseindia.com/)
- [BSE India](https://www.bseindia.com/)

## Support

For issues or questions about multi-market support:
1. Check this documentation
2. Review test examples in `tests/test_multi_market.py`
3. Create a GitHub issue with [MULTI-MARKET] prefix

---

**Status**: Phase 1 Complete ✅  
**Next**: Phase 2 - Indian Market Data Integration  
**Last Updated**: January 17, 2025

