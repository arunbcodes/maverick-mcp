# Phase 4: Advanced Indian Market Features

## Overview

Phase 4 adds advanced capabilities for Indian market analysis including economic data integration, news sentiment analysis, market comparison tools, and currency conversion utilities. This phase completes the Indian market support by providing comprehensive data sources and analytical tools.

## Scope

### Core Features

1. **RBI (Reserve Bank of India) Data Integration**

   - Monetary policy data (repo rate, CRR, SLR)
   - Economic indicators (GDP growth, inflation, IIP)
   - Foreign exchange reserves
   - Banking sector statistics

2. **Indian Financial News Sources**

   - MoneyControl integration
   - Economic Times integration
   - Additional Indian financial news sources
   - Sentiment analysis for Indian stocks

3. **Market Comparison Tools**

   - US vs India market correlation
   - Sector performance comparison
   - Currency-adjusted returns
   - Valuation metrics comparison

4. **Currency Conversion**

   - INR/USD real-time conversion
   - Historical exchange rates
   - Currency-adjusted portfolio valuation
   - Multi-currency reporting

5. **Comprehensive Testing**
   - Unit tests for all new components
   - Integration tests for data providers
   - End-to-end testing with MCP tools
   - Performance benchmarking

## Implementation Plan

### 1. RBI Data Provider

**File**: `maverick_mcp/providers/rbi_data.py`

#### Data Sources

1. **RBI Public API**

   - Base URL: `https://rbi.org.in/`
   - Economic indicators
   - Policy rates
   - Statistical releases

2. **Alternative Sources**
   - World Bank API for Indian economic data
   - Trading Economics API
   - FRED (Federal Reserve) for comparative data

#### Key Indicators

| Indicator         | Description                     | Update Frequency          |
| ----------------- | ------------------------------- | ------------------------- |
| Repo Rate         | RBI's key policy rate           | Bi-monthly (MPC meetings) |
| Reverse Repo Rate | Rate for RBI borrowing          | Bi-monthly                |
| CRR               | Cash Reserve Ratio              | As needed                 |
| SLR               | Statutory Liquidity Ratio       | As needed                 |
| GDP Growth        | Quarterly GDP growth rate       | Quarterly                 |
| CPI Inflation     | Consumer Price Index inflation  | Monthly                   |
| WPI Inflation     | Wholesale Price Index inflation | Monthly                   |
| IIP               | Index of Industrial Production  | Monthly                   |
| Forex Reserves    | Foreign exchange reserves       | Weekly                    |

#### Implementation

```python
class RBIDataProvider:
    """Provider for Reserve Bank of India economic data"""

    def __init__(self):
        self.base_url = "https://api.rbi.org.in/"  # If available
        self.cache_ttl = 3600  # 1 hour cache

    def get_policy_rates(self) -> Dict[str, float]:
        """Get current RBI policy rates"""

    def get_inflation_data(self, period: str = "1y") -> pd.DataFrame:
        """Get CPI and WPI inflation data"""

    def get_gdp_growth(self) -> Dict[str, Any]:
        """Get latest GDP growth figures"""

    def get_forex_reserves(self) -> Dict[str, float]:
        """Get current foreign exchange reserves"""

    def get_economic_calendar(self) -> List[Dict]:
        """Get upcoming RBI announcements and data releases"""
```

### 2. Indian News Integration

**File**: `maverick_mcp/providers/indian_news.py`

#### News Sources

1. **MoneyControl**

   - Base URL: `https://www.moneycontrol.com/`
   - Stock-specific news
   - Market news
   - Analysis articles

2. **Economic Times**

   - Base URL: `https://economictimes.indiatimes.com/`
   - Business news
   - Market analysis
   - Expert opinions

3. **Additional Sources**
   - LiveMint
   - Business Standard
   - Financial Express
   - Bloomberg Quint

#### Implementation

```python
class IndianNewsProvider:
    """Provider for Indian financial news sources"""

    def __init__(self):
        self.sources = {
            "moneycontrol": MoneyControlScraper(),
            "economic_times": EconomicTimesScraper(),
            "livemint": LiveMintScraper(),
            "business_standard": BusinessStandardScraper()
        }

    def get_stock_news(
        self,
        symbol: str,
        limit: int = 10,
        days: int = 7
    ) -> List[Dict]:
        """Get news for specific Indian stock"""

    def get_market_news(
        self,
        category: str = "all",
        limit: int = 20
    ) -> List[Dict]:
        """Get general market news"""

    def analyze_sentiment(
        self,
        symbol: str,
        period: str = "7d"
    ) -> Dict[str, Any]:
        """Analyze news sentiment for stock"""

    def get_trending_topics(self, limit: int = 10) -> List[str]:
        """Get trending topics in Indian financial news"""
```

#### Sentiment Analysis

Use existing sentiment analysis framework with Indian market context:

- Market-specific terminology
- Indian company names and sectors
- Regulatory news impact
- Government policy implications

### 3. Market Comparison Tools

**File**: `maverick_mcp/analysis/market_comparison.py`

#### Features

1. **Cross-Market Correlation**

   - S&P 500 vs Nifty 50 correlation
   - Sector correlation (US Tech vs Indian IT)
   - Individual stock correlation

2. **Performance Metrics**

   - Returns comparison (currency-adjusted)
   - Volatility comparison
   - Risk-adjusted returns (Sharpe ratio)

3. **Valuation Comparison**
   - P/E ratio comparison
   - Market cap comparisons
   - Sector valuations

#### Implementation

```python
class MarketComparisonAnalyzer:
    """Tools for comparing US and Indian markets"""

    def compare_indices(
        self,
        us_index: str = "^GSPC",  # S&P 500
        indian_index: str = "^NSEI",  # Nifty 50
        period: str = "1y"
    ) -> Dict[str, Any]:
        """Compare major indices"""

    def compare_sectors(
        self,
        sector: str,
        period: str = "1y"
    ) -> Dict[str, Any]:
        """Compare sector performance across markets"""

    def compare_stocks(
        self,
        us_symbol: str,
        indian_symbol: str,
        period: str = "1y",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Compare similar companies across markets"""

    def calculate_correlation(
        self,
        symbols: List[str],
        period: str = "1y"
    ) -> pd.DataFrame:
        """Calculate correlation matrix for cross-market stocks"""
```

### 4. Currency Conversion

**File**: `maverick_mcp/utils/currency_converter.py`

#### Data Sources

1. **Primary**: Exchange Rate API

   - API: https://exchangerate-api.com/
   - Real-time rates
   - Historical data

2. **Fallback**: Reserve Bank of India

   - Official RBI reference rates
   - Daily updates

3. **Alternative**: Currency Layer API

#### Implementation

```python
class CurrencyConverter:
    """INR/USD currency conversion with caching"""

    def __init__(self):
        self.api_key = settings.EXCHANGE_RATE_API_KEY
        self.cache_ttl = 3600  # 1 hour
        self.fallback_providers = [
            RBICurrencyProvider(),
            YahooCurrencyProvider()
        ]

    def get_exchange_rate(
        self,
        from_currency: str = "INR",
        to_currency: str = "USD"
    ) -> float:
        """Get current exchange rate"""

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> float:
        """Convert amount between currencies"""

    def get_historical_rates(
        self,
        from_currency: str,
        to_currency: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Get historical exchange rates"""

    def convert_timeseries(
        self,
        amounts: pd.Series,
        from_currency: str,
        to_currency: str,
        dates: pd.DatetimeIndex
    ) -> pd.Series:
        """Convert time series data with appropriate historical rates"""
```

#### Currency-Adjusted Analysis

```python
def adjust_for_currency(
    df: pd.DataFrame,
    from_currency: str,
    to_currency: str
) -> pd.DataFrame:
    """Adjust OHLCV data for currency conversion"""

def compare_returns_currency_adjusted(
    us_stock: str,
    indian_stock: str,
    period: str,
    base_currency: str = "USD"
) -> Dict[str, Any]:
    """Compare stock returns in common currency"""
```

### 5. MCP Tools

Add to `maverick_mcp/api/server.py`:

```python
@mcp.tool()
async def get_indian_economic_indicators() -> dict[str, Any]:
    """Get current Indian economic indicators (RBI data)"""

@mcp.tool()
async def get_indian_stock_news(
    symbol: str,
    limit: int = 10
) -> dict[str, Any]:
    """Get news and sentiment for Indian stock"""

@mcp.tool()
async def compare_us_indian_markets(
    period: str = "1y"
) -> dict[str, Any]:
    """Compare US and Indian market performance"""

@mcp.tool()
async def convert_currency(
    amount: float,
    from_currency: str = "INR",
    to_currency: str = "USD"
) -> dict[str, Any]:
    """Convert between INR and USD"""

@mcp.tool()
async def compare_similar_companies(
    us_symbol: str,
    indian_symbol: str,
    currency: str = "USD"
) -> dict[str, Any]:
    """Compare similar companies across markets"""
```

## Testing Strategy

### Unit Tests

**File**: `tests/test_rbi_data.py`

- Test RBI data fetching
- Test data parsing and validation
- Test caching behavior
- Test error handling

**File**: `tests/test_indian_news.py`

- Test news scraping from each source
- Test sentiment analysis
- Test deduplication
- Test rate limiting

**File**: `tests/test_market_comparison.py`

- Test correlation calculations
- Test performance metrics
- Test currency-adjusted comparisons
- Test data alignment

**File**: `tests/test_currency_conversion.py`

- Test real-time conversion
- Test historical rate fetching
- Test fallback providers
- Test cache invalidation
- Test time series conversion

### Integration Tests

**File**: `tests/integration/test_phase4_integration.py`

- End-to-end MCP tool testing
- Cross-provider data consistency
- Performance benchmarks
- Error recovery scenarios

### Test Coverage Goals

- Unit test coverage: > 85%
- Integration test coverage: > 70%
- All critical paths tested
- Edge cases and error conditions covered

## Performance Considerations

### Caching Strategy

1. **RBI Data**: Cache for 1 hour (updates infrequent)
2. **News Articles**: Cache for 15 minutes
3. **Currency Rates**: Cache for 1 hour
4. **Market Data**: Use existing stock data cache

### Rate Limiting

1. **News Scraping**: Respect robots.txt, implement delays
2. **API Calls**: Track quota usage, implement backoff
3. **Concurrent Requests**: Limit parallel requests per source

### Data Storage

- Store historical economic indicators in database
- Cache frequent currency conversions
- Maintain news article deduplication index

## Configuration

### Environment Variables

```bash
# RBI Data (if API key required)
RBI_API_KEY=your_rbi_api_key

# Currency Exchange API
EXCHANGE_RATE_API_KEY=your_exchange_rate_api_key

# News APIs (if using official APIs)
MONEYCONTROL_API_KEY=your_moneycontrol_api_key
ECONOMIC_TIMES_API_KEY=your_et_api_key

# Optional: Trading Economics
TRADING_ECONOMICS_API_KEY=your_te_api_key
```

### Configuration File

```python
# maverick_mcp/config/indian_data_sources.py

INDIAN_NEWS_SOURCES = {
    "moneycontrol": {
        "base_url": "https://www.moneycontrol.com/",
        "rate_limit": 10,  # requests per second
        "timeout": 30
    },
    "economic_times": {
        "base_url": "https://economictimes.indiatimes.com/",
        "rate_limit": 5,
        "timeout": 30
    },
    # ... more sources
}

RBI_DATA_CONFIG = {
    "cache_ttl": 3600,
    "fallback_providers": ["worldbank", "tradingeconomics"],
    "update_frequency": {
        "policy_rates": "daily",
        "inflation": "monthly",
        "gdp": "quarterly"
    }
}
```

## Dependencies

### New Requirements

```txt
# Currency conversion
requests>=2.31.0
python-forex>=1.8

# Web scraping (for news)
beautifulsoup4>=4.12.0
lxml>=4.9.0
newspaper3k>=0.2.8  # For article extraction

# Sentiment analysis (existing)
textblob>=0.17.1
vaderSentiment>=3.3.2

# Economic data
pandas-datareader>=0.10.0  # For World Bank, FRED
```

### Installation

```bash
# Install new dependencies
pip install python-forex beautifulsoup4 lxml newspaper3k pandas-datareader

# Or with uv
uv add python-forex beautifulsoup4 lxml newspaper3k pandas-datareader
```

## Implementation Checklist

### Week 1: RBI Data Integration

- [ ] Create `rbi_data.py` provider
- [ ] Implement policy rates fetching
- [ ] Implement inflation data
- [ ] Implement GDP and economic indicators
- [ ] Add caching layer
- [ ] Create unit tests
- [ ] Add MCP tool

### Week 2: News Integration

- [ ] Create `indian_news.py` provider
- [ ] Implement MoneyControl scraper
- [ ] Implement Economic Times scraper
- [ ] Add sentiment analysis
- [ ] Implement rate limiting
- [ ] Create unit tests
- [ ] Add MCP tool

### Week 3: Market Comparison

- [ ] Create `market_comparison.py` analyzer
- [ ] Implement index comparison
- [ ] Implement sector comparison
- [ ] Implement stock comparison
- [ ] Add correlation analysis
- [ ] Create unit tests
- [ ] Add MCP tool

### Week 4: Currency Conversion

- [ ] Create `currency_converter.py` utility
- [ ] Implement real-time conversion
- [ ] Implement historical rates
- [ ] Add time series conversion
- [ ] Create unit tests
- [ ] Integrate with comparison tools
- [ ] Add MCP tool

### Week 5: Integration & Testing

- [ ] End-to-end integration tests
- [ ] Performance benchmarking
- [ ] Error handling verification
- [ ] Documentation updates
- [ ] Code review and refinement

## Success Criteria

### Functional Requirements

1. **RBI Data**

   - Successfully fetch policy rates
   - Retrieve inflation and GDP data
   - Cache working correctly
   - Fallback providers operational

2. **News Integration**

   - Scrape from multiple sources
   - Sentiment analysis produces scores
   - Deduplication working
   - Rate limiting respected

3. **Market Comparison**

   - Index correlation calculations accurate
   - Sector comparisons meaningful
   - Currency adjustments correct
   - Performance metrics comprehensive

4. **Currency Conversion**
   - Real-time rates within 1% of actual
   - Historical rates available for 5+ years
   - Time series conversion accurate
   - Fallback providers working

### Performance Requirements

- RBI data fetch: < 2 seconds
- News scraping: < 5 seconds for 10 articles
- Market comparison: < 3 seconds
- Currency conversion: < 500ms

### Quality Requirements

- Test coverage > 80%
- Zero linting errors
- Complete API documentation
- Usage examples for all features

## Future Enhancements

1. **Real-time News Feeds**: WebSocket integration for live news
2. **Advanced Sentiment**: NLP models trained on Indian financial text
3. **Predictive Analytics**: Correlation-based predictions
4. **Automated Alerts**: Notifications for key economic indicators
5. **Historical Analysis**: Long-term trend analysis
6. **Custom Dashboards**: Visualization of comparative data

## References

- [Reserve Bank of India](https://www.rbi.org.in/)
- [MoneyControl](https://www.moneycontrol.com/)
- [Economic Times](https://economictimes.indiatimes.com/)
- [Exchange Rate API](https://www.exchangerate-api.com/)
- [World Bank Data API](https://data.worldbank.org/)
- [FRED Economic Data](https://fred.stlouisfed.org/)

## Related Documentation

- [Phase 1: Multi-Market Infrastructure](./MULTI_MARKET_SUPPORT.md)
- [Phase 2: Indian Market Data Integration](./PHASE2_INDIAN_MARKET.md)
- [Phase 3: Indian Market Screening](./PHASE3_IMPLEMENTATION.md)
