# Phase 2: Indian Market Data Integration

## Overview

Phase 2 extends MaverickMCP with comprehensive support for Indian stock markets (NSE and BSE), building on the multi-market infrastructure established in Phase 1.

## Features

### 1. Indian Market Data Provider

A specialized data provider for Indian stock markets with the following capabilities:

- **Symbol Validation**: Validates NSE (.NS) and BSE (.BO) symbols
- **Data Fetching**: Retrieves historical and real-time data for Indian stocks
- **Market Status**: Checks if Indian markets are currently open/closed
- **Index Constituents**: Built-in lists for Nifty 50 and Sensex stocks

###2. Key Components

#### IndianMarketDataProvider

Located in `maverick_mcp/providers/indian_market_data.py`, this provider offers:

```python
from maverick_mcp.providers.indian_market_data import IndianMarketDataProvider

# Initialize provider
provider = IndianMarketDataProvider()

# Fetch NSE stock data
nse_data = provider.get_nse_stock_data("RELIANCE", period="1mo")

# Fetch BSE stock data
bse_data = provider.get_bse_stock_data("RELIANCE", period="1mo")

# Get stock information
info = provider.get_stock_info("RELIANCE.NS")

# Check market status
status = provider.get_indian_market_status()
```

#### Convenience Functions

Quick-access functions for common operations:

```python
from maverick_mcp.providers.indian_market_data import fetch_nse_data, fetch_bse_data

# Quick NSE data fetch
df = fetch_nse_data("RELIANCE", period="1mo")

# Quick BSE data fetch
df = fetch_bse_data("TCS", period="3mo")
```

### 3. Symbol Formatting

The provider automatically handles symbol formatting:

```python
provider = IndianMarketDataProvider()

# Auto-formats to RELIANCE.NS
nse_symbol = provider.format_nse_symbol("RELIANCE")

# Auto-formats to TCS.BO
bse_symbol = provider.format_bse_symbol("TCS")

# Already formatted symbols remain unchanged
symbol = provider.format_nse_symbol("INFY.NS")  # Returns "INFY.NS"
```

### 4. Symbol Validation

Validates Indian market symbols before data fetching:

```python
is_valid, market, error = provider.validate_indian_symbol("RELIANCE.NS")
# Returns: (True, Market.INDIA_NSE, None)

is_valid, market, error = provider.validate_indian_symbol("AAPL")
# Returns: (False, None, "Not an Indian market symbol (must end with .NS or .BO)")
```

### 5. Index Constituents

Pre-configured lists of major Indian index stocks:

```python
# Get Nifty 50 stocks (50 companies)
nifty50 = provider.get_nifty50_constituents()
# Returns: ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", ...]

# Get Sensex stocks (30 companies)
sensex = provider.get_sensex_constituents()
# Returns: ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", ...]
```

### 6. Market Status

Check if Indian markets are currently trading:

```python
status = provider.get_indian_market_status()
# Returns:
# {
#     "status": "OPEN" | "CLOSED" | "HOLIDAY",
#     "is_open": bool,
#     "is_trading_day": bool,
#     "current_time": "HH:MM:SS",
#     "market_open": "09:15",
#     "market_close": "15:30",
#     "timezone": "Asia/Kolkata",
#     "date": "YYYY-MM-DD"
# }
```

## Database Seeding

### Seed Indian Stocks

A dedicated script to populate the database with major Indian stocks:

```bash
# Run the seed script
./scripts/seed_indian_stocks.py
```

The script includes:
- **50 Nifty 50 constituents**: Major NSE-listed companies
- **30 Sensex constituents**: Major BSE-listed companies (using NSE symbols)
- **Automatic metadata**: Fetches sector, industry, market cap from yfinance

### Stock Coverage

Major Indian companies included:
- **Banking & Finance**: HDFC Bank, ICICI Bank, Kotak Mahindra Bank, SBI
- **Technology**: TCS, Infosys, Wipro, HCL Tech, Tech Mahindra
- **Energy**: Reliance Industries, ONGC, BPCL, IOC
- **Consumer Goods**: Hindustan Unilever, ITC, Nestle India, Britannia
- **Automotive**: Maruti Suzuki, Tata Motors, Mahindra & Mahindra, Bajaj Auto
- **Pharmaceuticals**: Sun Pharma, Dr. Reddy's, Cipla, Divi's Labs
- **Industrials**: Larsen & Toubro, UltraTech Cement, JSW Steel, Tata Steel
- **And many more**...

## API Integration

The Indian market provider integrates seamlessly with existing MaverickMCP APIs:

### Stock Data Endpoints

```python
# All existing endpoints now support Indian stocks
GET /api/stocks?market=NSE
GET /api/stocks/{ticker}  # Works with RELIANCE.NS
GET /api/data/{ticker}/historical  # Fetches Indian stock data
```

### Market-Aware Queries

```python
from maverick_mcp.data.models import Stock, SessionLocal

session = SessionLocal()

# Query Indian stocks
nse_stocks = session.query(Stock).filter(Stock.market == "NSE").all()
bse_stocks = session.query(Stock).filter(Stock.market == "BSE").all()

# Query by country
indian_stocks = session.query(Stock).filter(Stock.country == "IN").all()
```

## Testing

### Unit Tests

Comprehensive unit tests in `tests/test_indian_market.py` cover:

- ✅ Symbol validation (NSE, BSE, invalid symbols)
- ✅ Symbol formatting (NSE, BSE, case handling)
- ✅ Constituent lists (Nifty 50, Sensex)
- ✅ Market status checks
- ✅ Error handling
- ✅ Convenience functions

### Manual Testing

```bash
# Test Indian market provider
python3 -c "
from maverick_mcp.providers.indian_market_data import IndianMarketDataProvider

provider = IndianMarketDataProvider()

# Test validation
is_valid, market, error = provider.validate_indian_symbol('RELIANCE.NS')
print(f'Validation: {is_valid}, Market: {market}')

# Test formatting
nse = provider.format_nse_symbol('RELIANCE')
print(f'NSE Symbol: {nse}')

# Test constituents
nifty50 = provider.get_nifty50_constituents()
print(f'Nifty 50 Count: {len(nifty50)}')

# Test market status
status = provider.get_indian_market_status()
print(f'Market Status: {status[\"status\"]}')
"
```

## Usage Examples

### Example 1: Fetch Indian Stock Data

```python
from maverick_mcp.providers.indian_market_data import IndianMarketDataProvider

provider = IndianMarketDataProvider()

# Fetch Reliance Industries NSE data
df = provider.get_nse_stock_data("RELIANCE", period="3mo")
print(df.head())
print(f"Latest close: ₹{df['close'].iloc[-1]:.2f}")
```

### Example 2: Analyze Nifty 50 Stocks

```python
from maverick_mcp.providers.indian_market_data import IndianMarketDataProvider

provider = IndianMarketDataProvider()

# Get all Nifty 50 stocks
nifty50 = provider.get_nifty50_constituents()

# Fetch data for each stock
for symbol in nifty50[:5]:  # First 5 for demo
    try:
        data = provider.get_stock_data(symbol, period="1d")
        latest_close = data['close'].iloc[-1]
        print(f"{symbol}: ₹{latest_close:.2f}")
    except Exception as e:
        print(f"{symbol}: Error - {e}")
```

### Example 3: Compare NSE and BSE Prices

```python
from maverick_mcp.providers.indian_market_data import IndianMarketDataProvider

provider = IndianMarketDataProvider()

# Fetch same stock from both exchanges
nse_data = provider.get_nse_stock_data("RELIANCE", period="1mo")
bse_data = provider.get_bse_stock_data("RELIANCE", period="1mo")

print(f"NSE Latest: ₹{nse_data['close'].iloc[-1]:.2f}")
print(f"BSE Latest: ₹{bse_data['close'].iloc[-1]:.2f}")
```

### Example 4: Market Hours Check

```python
from maverick_mcp.providers.indian_market_data import IndianMarketDataProvider

provider = IndianMarketDataProvider()

# Check if market is open
status = provider.get_indian_market_status()

if status["is_open"]:
    print(f"🟢 Indian market is OPEN")
    print(f"   Current time: {status['current_time']} IST")
else:
    print(f"🔴 Indian market is {status['status']}")
    if status["is_trading_day"]:
        print(f"   Opens at: {status['market_open']} IST")
```

## Architecture

### Data Flow

```
User Request
     ↓
IndianMarketDataProvider
     ↓
Symbol Validation
     ↓
Market-Aware Calendar (pandas_market_calendars)
     ↓
yfinance API (.NS / .BO symbols)
     ↓
Data Processing
     ↓
Response (pandas DataFrame)
```

### Market Configuration

Indian market configurations (from Phase 1):

```python
Market.INDIA_NSE: MarketConfig(
    name="National Stock Exchange of India",
    country="IN",
    currency="INR",
    timezone="Asia/Kolkata",
    calendar_name="BSE",  # pandas_market_calendars
    symbol_suffix=".NS",
    trading_hours_start=time(9, 15),
    trading_hours_end=time(15, 30),
    circuit_breaker_percent=10.0,
    settlement_cycle="T+1",
    min_tick_size=0.05,
)
```

## Limitations & Known Issues

1. **yfinance Dependency**: Data quality depends on Yahoo Finance API availability
2. **Calendar Approximation**: `pandas_market_calendars` uses BSE calendar for both NSE/BSE
3. **Real-time Data**: Market status is calculated based on schedule, not actual API status
4. **Search Functionality**: `search_indian_stocks()` is a placeholder (TODO)

## Future Enhancements (Phase 3+)

1. **Live Price Streams**: WebSocket integration for real-time Indian stock prices
2. **Corporate Actions**: Dividends, splits, bonuses for Indian stocks
3. **F&O Data**: Futures and Options data for Indian derivatives
4. **Intraday Data**: Minute-level data for day trading
5. **Alternative Data Sources**: Integration with NSE/BSE official APIs
6. **Stock Screener**: Filter stocks by Indian-specific criteria (P/E, dividend yield, etc.)

## Migration Guide

### For Existing US Stock Users

No changes required! US stock functionality remains unchanged. Indian markets are additive:

```python
# US stocks work as before
from maverick_mcp.providers.stock_data import EnhancedStockDataProvider

provider = EnhancedStockDataProvider()
us_data = provider.get_stock_data("AAPL", period="1mo")

# Indian stocks use the same provider or specialized one
indian_provider = IndianMarketDataProvider()
indian_data = indian_provider.get_nse_stock_data("RELIANCE", period="1mo")
```

## Summary

Phase 2 successfully integrates Indian stock market support into MaverickMCP with:

✅ NSE and BSE data fetching
✅ Symbol validation and formatting  
✅ Market status checking
✅ Nifty 50 and Sensex constituent lists
✅ Database seeding script for major Indian stocks
✅ Comprehensive unit tests
✅ Full backward compatibility with US stocks

The system is now ready for multi-market analysis and trading strategies across US and Indian markets!

