# Stock Analysis

Comprehensive stock data and analysis for US and Indian markets.

## Supported Markets

### US Markets
- **NASDAQ**: Technology and growth stocks
- **NYSE**: Traditional blue-chip companies
- **Symbol Format**: Simple ticker (e.g., `AAPL`, `MSFT`)

### Indian Markets
- **NSE (National Stock Exchange)**: `.NS` suffix (e.g., `RELIANCE.NS`)
- **BSE (Bombay Stock Exchange)**: `.BO` suffix (e.g., `TCS.BO`)

## Features

### Real-Time Data
```
Get current price for AAPL
```

Returns:
- Current price
- Day's high/low
- Volume
- Previous close
- Change and % change
- Market cap
- P/E ratio

### Historical Data
```
Get AAPL historical prices from Jan 2024 to Dec 2024
```

Returns:
- OHLCV data (Open, High, Low, Close, Volume)
- Adjusted close prices
- Date range filtering
- Automatic timezone handling

### Company Information
```
Get company info for RELIANCE.NS
```

Returns:
- Company name and description
- Sector and industry
- Market cap
- Key executives
- Exchange and currency
- Fundamental metrics

### Batch Operations
```
Compare prices for AAPL, MSFT, and GOOGL
```

- Fetch multiple stocks in one request
- Efficient parallel processing
- Automatic rate limiting

## Data Quality

### Accuracy
- Real-time quotes (15-min delay for free tier)
- Daily updates for historical data
- Validated against exchange data
- Automatic data cleaning

### Coverage
- 520+ S&P 500 stocks pre-seeded
- All US-listed stocks available
- Major Indian NSE/BSE stocks
- International ADRs

### Freshness
- Intraday updates every 15 minutes
- EOD updates within 30 minutes
- Historical data back to IPO date
- Corporate actions adjusted

## Caching

Multi-tier caching for optimal performance:

### L1 Cache (Redis/Memory)
- Duration: 5 minutes for real-time
- Duration: 24 hours for historical
- Speed: 1-5ms response time

### L2 Cache (Database)
- Duration: 1 hour for real-time
- Duration: 7 days for historical  
- Speed: 10-50ms response time

### L3 Source (Tiingo API)
- Rate limit: 500 requests/day (free tier)
- Speed: 500-2000ms response time
- Automatic retry on failure

## Usage Examples

### Basic Quote
```
What is the current price of AAPL?
```

### Historical Analysis
```
Show me RELIANCE.NS price history for Q1 2025
```

### Multi-Stock Comparison
```
Compare year-to-date performance of AAPL, MSFT, GOOGL
```

### Fundamental Data
```
Get fundamentals for TCS.NS including P/E ratio and market cap
```

## Market-Specific Features

### US Markets
- Extended hours trading data
- Options data (coming soon)
- Earnings dates
- Dividend history

### Indian Markets
- NSE circuit breaker tracking (10%)
- Corporate actions (splits, bonuses)
- Delivery percentage
- FII/DII activity

## API Reference

See [Stock Data Tools](../user-guide/mcp-tools.md#stock-data) for complete API reference.

## Configuration

Required:
```ini
TIINGO_API_KEY=your-key-here
```

Optional:
```ini
# Redis caching (recommended)
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Limitations

### Free Tier
- 500 API requests per day
- 15-minute delayed quotes
- Limited to EOD data
- No Level 2 data

### Upgrade Options
See [Tiingo Pricing](https://tiingo.com/pricing) for:
- Real-time data
- Unlimited requests
- Options & futures
- Institutional features
