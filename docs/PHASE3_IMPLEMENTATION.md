# Phase 3: Indian Market Screening Strategies

## Overview

Phase 3 implements seven screening strategies specifically adapted for the Indian stock market (NSE and BSE exchanges). These strategies account for Indian market characteristics including 10% circuit breakers, INR denomination, Nifty sector structure, and lower liquidity compared to US markets.

## Implementation

### Core Module

**Location**: `maverick_mcp/application/screening/indian_market.py`

**Total Lines**: 812

### Screening Strategies

#### 1. Maverick Bullish India (`get_maverick_bullish_india`)

Identifies bullish momentum opportunities in Indian stocks.

**Criteria**:

- Volume > 500,000 shares (adjusted for smaller Indian market)
- RSI between 30-70 (momentum without overbought condition)
- Price above 50-day moving average
- Weekly price increase > 2%
- Market cap > ₹5,000 crores
- Respects 10% circuit breaker limits

**Parameters**:

- `min_volume` (int): Minimum daily volume (default: 500,000)
- `rsi_low` (int): Lower RSI threshold (default: 30)
- `rsi_high` (int): Upper RSI threshold (default: 70)
- `lookback_days` (int): Analysis period (default: 30)
- `limit` (int): Maximum results (default: 20)

#### 2. Maverick Bearish India (`get_maverick_bearish_india`)

Identifies potential short opportunities in Indian stocks.

**Criteria**:

- Volume > 500,000 shares
- RSI > 70 (overbought condition)
- Price below 50-day moving average
- Recent price decrease
- High debt-to-equity ratio (when available)

#### 3. Nifty 50 Momentum (`get_nifty50_momentum`)

Finds momentum plays within Nifty 50 constituents.

**Criteria**:

- Stock must be in Nifty 50
- Weekly price change > 2%
- RSI between 50-70
- Volume above average
- Price above 50-day MA

#### 4. Nifty Sector Rotation (`get_nifty_sector_rotation`)

Analyzes sector performance and identifies strongest sectors.

**Returns**: Sector rankings with:

- Average sector returns over analysis period
- Stock count per sector
- Top 3 performing stocks in each sector

**Parameters**:

- `lookback_days` (int): Analysis period (default: 90)
- `top_n` (int): Number of top sectors to highlight (default: 3)

#### 5. Value Picks India (`get_value_picks_india`)

Identifies undervalued stocks using technical proxies.

**Criteria**:

- Trading in lower 30% of 52-week range
- Low volatility (< 5%)
- Market cap > ₹5,000 crores

**Note**: This is a technical proxy implementation. Full fundamental analysis would require P/E, dividend yield, and debt-to-equity data.

#### 6. High Dividend India (`get_high_dividend_india`)

Identifies stocks from dividend-paying sectors with price stability.

**Target Sectors**:

- Banking & Financial Services
- Oil & Gas
- Power & Utilities
- FMCG

**Criteria**:

- Market cap > ₹10,000 crores
- Price stability score > 0.7
- Sector known for dividend payments

#### 7. Small-Cap Breakouts India (`get_smallcap_breakouts_india`)

Identifies small-cap stocks with breakout potential.

**Criteria**:

- Volume spike > 150% above 30-day average
- Strong price momentum (> 3% weekly gain)
- Price above 20-day and 50-day MAs
- Breakout from consolidation

### Utility Functions

#### Circuit Breaker Limits

```python
calculate_circuit_breaker_limits(current_price: float, market: Market) -> Dict
```

Calculates upper and lower circuit breaker limits for Indian stocks (10% movement limit).

**Returns**:

```python
{
    "upper_limit": float,
    "lower_limit": float,
    "circuit_breaker_pct": 10.0
}
```

#### Currency Formatting

```python
format_indian_currency(amount: float) -> str
```

Formats amounts using Indian numbering system.

**Examples**:

- `format_indian_currency(100000)` → "₹1.00 L" (lakh)
- `format_indian_currency(10000000)` → "₹1.00 Cr" (crore)
- `format_indian_currency(50000)` → "₹50,000.00"

#### Nifty Sectors

```python
get_nifty_sectors() -> List[str]
```

Returns list of 14 major Nifty sectors:

- Banking & Financial Services
- Information Technology
- Oil & Gas
- Fast Moving Consumer Goods
- Automobile
- Pharmaceuticals
- Metals & Mining
- Infrastructure
- Telecom
- Power
- Consumer Durables
- Cement
- Real Estate
- Media & Entertainment

## MCP Tools

Three MCP tools were added to `maverick_mcp/api/server.py` for Claude Desktop integration:

### 1. get_indian_market_recommendations

```python
async def get_indian_market_recommendations(
    strategy: str = "bullish",
    limit: int = 20
) -> dict[str, Any]
```

**Strategies**: `bullish`, `bearish`, `momentum`, `value`, `dividend`, `smallcap`, `sector_rotation`

**Usage**:

```
"Show me bullish Indian stock recommendations"
"Find momentum plays in Nifty 50"
```

### 2. analyze_nifty_sectors

```python
async def analyze_nifty_sectors() -> dict[str, Any]
```

Returns sector rotation analysis with 90-day performance rankings.

**Usage**:

```
"Which Nifty sectors are performing well?"
"Analyze Indian sector rotation"
```

### 3. get_indian_market_overview

```python
async def get_indian_market_overview() -> dict[str, Any]
```

Provides comprehensive market overview including:

- Market status (open/closed/holiday)
- Stock counts (NSE/BSE)
- Index constituents (Nifty 50, Sensex)
- Trading hours and market info

## Indian Market Adaptations

### Circuit Breakers

| Market          | Circuit Breaker | Implementation                     |
| --------------- | --------------- | ---------------------------------- |
| US              | 7%              | `MARKET_CONFIGS[Market.US]`        |
| India (NSE/BSE) | 10%             | `MARKET_CONFIGS[Market.INDIA_NSE]` |

### Volume Thresholds

Indian market has lower liquidity than US markets. Default volume thresholds adjusted:

- US: 1,000,000 shares
- India: 500,000 shares

### Price Denomination

All prices formatted in INR with Indian numbering:

- 1 Lakh (L) = 100,000 (1,00,000 in Indian notation)
- 1 Crore (Cr) = 10,000,000 (1,00,00,000 in Indian notation)

### Settlement Cycle

- US: T+2
- India: T+1

### Trading Hours

- US: 9:30 AM - 4:00 PM EST
- India: 9:15 AM - 3:30 PM IST

## Testing

**Location**: `tests/test_indian_screening.py` (193 lines)

### Test Coverage

1. **Utility Functions**

   - Circuit breaker calculations (10% validation)
   - Currency formatting (lakhs/crores)
   - Nifty sector list validation

2. **Strategy Structure**

   - All strategies return proper data structures
   - Respect limit parameters
   - Handle empty datasets gracefully

3. **Market Configuration**
   - Indian market config validation
   - Circuit breaker comparison (India vs US)
   - Market-specific settings verification

### Running Tests

```bash
# Run all Indian screening tests
pytest tests/test_indian_screening.py -v

# Run specific test class
pytest tests/test_indian_screening.py::TestUtilityFunctions -v

# Run with coverage
pytest tests/test_indian_screening.py --cov=maverick_mcp.application.screening.indian_market
```

## Usage Requirements

### Prerequisites

1. **Database Setup**: Multi-market schema from Phase 1
2. **Indian Stocks Seeded**: Run `scripts/seed_indian_stocks.py` to populate database
3. **Market Data Access**: yfinance configured for .NS and .BO symbols

### Example Usage

```python
from maverick_mcp.application.screening.indian_market import (
    get_maverick_bullish_india,
    get_nifty_sector_rotation,
    format_indian_currency
)

# Get bullish recommendations
results = get_maverick_bullish_india(limit=10)
for stock in results:
    print(f"{stock['symbol']}: Score {stock['score']}")

# Analyze sectors
sector_analysis = get_nifty_sector_rotation(lookback_days=90, top_n=3)
for sector in sector_analysis['top_sectors']:
    print(f"{sector['sector']}: {sector['avg_return']}% return")

# Format currency
print(format_indian_currency(50000000))  # "₹5.00 Cr"
```

## Performance Considerations

### Database Queries

- Initial stock query limited to 100 stocks for performance
- Uses indexed columns: `market`, `country`, `is_active`, `sector`
- Session properly closed after each strategy execution

### API Rate Limiting

- Strategies query yfinance for historical data
- Implement caching for frequently accessed stocks
- Consider batch processing for large screening operations

### Computation Optimization

- Technical indicators calculated once per stock
- Early exit conditions to avoid unnecessary processing
- Efficient pandas operations for data analysis

## Known Limitations

1. **Fundamental Data**: Limited access to P/E ratios, dividend yields, and debt-to-equity ratios through yfinance
2. **Real-time Data**: Market status calculated based on schedule, not actual exchange status
3. **Historical Data**: Dependent on yfinance data quality for Indian markets
4. **Search Functionality**: `search_indian_stocks()` not yet implemented

## Future Enhancements

1. **NSE/BSE Official APIs**: Direct integration with exchange APIs for real-time data
2. **Fundamental Analysis**: Full implementation with P/E, dividend, and debt metrics
3. **Intraday Screening**: Minute-level data analysis for day trading
4. **Custom Indicators**: India-specific technical indicators
5. **Backtesting**: Historical performance of screening strategies
6. **Alerts**: Real-time notifications for screening matches

## Dependencies

- `pandas`: Data manipulation and analysis
- `yfinance`: Stock data retrieval
- `sqlalchemy`: Database operations
- `maverick_mcp.config.markets`: Multi-market configuration
- `maverick_mcp.providers.indian_market_data`: Indian market data provider
- `maverick_mcp.core.technical_analysis`: RSI and SMA calculations

## Architecture Integration

Phase 3 builds on:

- **Phase 1**: Multi-market infrastructure and database schema
- **Phase 2**: Indian market data provider and constituent lists

Enables:

- **Phase 4**: Economic indicators, news integration, and currency conversion
- **Future Phases**: Advanced analytics and cross-market strategies

## Maintenance

### Adding New Strategies

1. Create function in `indian_market.py` following existing pattern
2. Add to MCP tools strategy mapping in `server.py`
3. Create tests in `test_indian_screening.py`
4. Update this documentation

### Updating Thresholds

Market-specific thresholds can be adjusted in strategy functions:

- Volume thresholds for liquidity changes
- RSI ranges for volatility adjustments
- Price change percentages for momentum detection
- Market cap minimums for risk management

### Sector Updates

Nifty sector list is maintained in `get_nifty_sectors()`. Update as NSE modifies sector classifications.

## References

- [NSE India](https://www.nseindia.com/)
- [BSE India](https://www.bseindia.com/)
- [Nifty 50 Index](https://www.nseindia.com/market-data/live-equity-market)
- [Indian Stock Market Regulations](https://www.sebi.gov.in/)
