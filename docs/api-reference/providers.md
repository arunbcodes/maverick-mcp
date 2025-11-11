# Providers API Reference

External data providers and API integrations.

## Module: maverick_mcp.providers.stock_data

### StockDataProvider

Tiingo API integration for stock data.

**Class**: `StockDataProvider`

**Initialization**:
```python
from maverick_mcp.providers.stock_data import StockDataProvider

provider = StockDataProvider(api_key="your-tiingo-key")
```

**Methods**:

#### get_historical_data()

Fetch historical OHLCV data.

**Signature**:
```python
def get_historical_data(
    self,
    ticker: str,
    start_date: str | None = None,
    end_date: str | None = None,
    period: str | None = None
) -> pd.DataFrame
```

**Parameters**:
- `ticker` (str): Stock symbol (e.g., "AAPL", "RELIANCE.NS")
- `start_date` (str, optional): Start date (YYYY-MM-DD)
- `end_date` (str, optional): End date (YYYY-MM-DD)
- `period` (str, optional): Quick period ("1d", "5d", "1mo", "3mo", "6mo", "1y", "5y")

**Returns**:
- pd.DataFrame: Columns: Date (index), Open, High, Low, Close, Volume

**Raises**:
- ValueError: Invalid ticker or date range
- APIError: Tiingo API error

**Example**:
```python
provider = StockDataProvider()

# Get last year of data
data = provider.get_historical_data("AAPL", period="1y")

# Get specific date range
data = provider.get_historical_data(
    "AAPL",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

---

#### get_quote()

Get current stock quote.

**Signature**:
```python
def get_quote(self, ticker: str) -> dict
```

**Parameters**:
- `ticker` (str): Stock symbol

**Returns**:
- dict: Contains:
  - `ticker`: Stock symbol
  - `price`: Current price
  - `change`: Price change
  - `change_percent`: Percentage change
  - `volume`: Trading volume
  - `market_cap`: Market capitalization
  - `high`: Day's high
  - `low`: Day's low
  - `open`: Opening price
  - `previous_close`: Previous close

**Example**:
```python
quote = provider.get_quote("AAPL")
print(f"Price: ${quote['price']}")
print(f"Change: {quote['change_percent']}%")
```

---

#### get_company_info()

Get company fundamentals.

**Signature**:
```python
def get_company_info(self, ticker: str) -> dict
```

**Parameters**:
- `ticker` (str): Stock symbol

**Returns**:
- dict: Contains:
  - `name`: Company name
  - `description`: Business description
  - `sector`: Industry sector
  - `industry`: Specific industry
  - `pe_ratio`: Price-to-earnings ratio
  - `eps`: Earnings per share
  - `market_cap`: Market capitalization
  - `website`: Company website
  - `employees`: Number of employees

---

## Module: maverick_mcp.providers.market_data

### MarketDataProvider

Market indices and sector data.

**Class**: `MarketDataProvider`

**Methods**:

#### get_market_overview()

Get major indices and market breadth.

**Signature**:
```python
def get_market_overview(self) -> dict
```

**Returns**:
- dict: Contains:
  - `indices`: S&P 500, Nasdaq, Dow Jones, Russell 2000
  - `sectors`: Sector performance
  - `breadth`: Advance/decline ratio, new highs/lows
  - `vix`: Volatility index

**Example**:
```python
from maverick_mcp.providers.market_data import MarketDataProvider

provider = MarketDataProvider()
overview = provider.get_market_overview()

print(f"S&P 500: {overview['indices']['SPX']['change_percent']}%")
print(f"VIX: {overview['vix']}")
```

---

#### get_sector_performance()

Get sector-wise performance.

**Signature**:
```python
def get_sector_performance(self) -> list[dict]
```

**Returns**:
- list[dict]: Sectors with performance metrics

**Sectors**:
- Technology, Healthcare, Financial, Consumer, Energy, etc.

---

## Module: maverick_mcp.providers.indian_market_data

### IndianMarketDataProvider

Indian stock market data (NSE/BSE).

**Class**: `IndianMarketDataProvider`

**Methods**:

#### get_nifty_50()

Get Nifty 50 constituent stocks.

**Signature**:
```python
def get_nifty_50(self) -> list[str]
```

**Returns**:
- list[str]: List of Nifty 50 tickers with .NS suffix

**Example**:
```python
from maverick_mcp.providers.indian_market_data import IndianMarketDataProvider

provider = IndianMarketDataProvider()
nifty_stocks = provider.get_nifty_50()

for ticker in nifty_stocks:
    print(ticker)  # e.g., "RELIANCE.NS"
```

---

#### get_sensex()

Get Sensex constituent stocks.

**Signature**:
```python
def get_sensex(self) -> list[str]
```

**Returns**:
- list[str]: List of Sensex tickers with .BO suffix

---

#### is_market_open()

Check if Indian market is currently open.

**Signature**:
```python
def is_market_open(self) -> bool
```

**Returns**:
- bool: True if market is open

**Trading Hours**:
- NSE/BSE: 9:15 AM - 3:30 PM IST (Mon-Fri)
- Closed on exchange holidays

---

#### validate_ticker()

Validate and format Indian stock ticker.

**Signature**:
```python
def validate_ticker(self, ticker: str, exchange: str = "NSE") -> str
```

**Parameters**:
- `ticker` (str): Stock symbol
- `exchange` (str, optional): "NSE" or "BSE". Default: "NSE"

**Returns**:
- str: Formatted ticker with .NS or .BO suffix

**Example**:
```python
ticker = provider.validate_ticker("RELIANCE")  # Returns "RELIANCE.NS"
ticker = provider.validate_ticker("TCS", exchange="BSE")  # Returns "TCS.BO"
```

---

## Module: maverick_mcp.providers.rbi_data

### RBIDataProvider

Reserve Bank of India economic data.

**Class**: `RBIDataProvider`

**Methods**:

#### get_policy_rates()

Get RBI policy rates.

**Signature**:
```python
def get_policy_rates(self) -> dict
```

**Returns**:
- dict: Contains:
  - `repo_rate`: RBI repo rate (%)
  - `reverse_repo_rate`: Reverse repo rate (%)
  - `crr`: Cash Reserve Ratio (%)
  - `slr`: Statutory Liquidity Ratio (%)
  - `bank_rate`: Bank rate (%)
  - `last_updated`: Update date

**Example**:
```python
from maverick_mcp.providers.rbi_data import RBIDataProvider

provider = RBIDataProvider()
rates = provider.get_policy_rates()

print(f"Repo Rate: {rates['repo_rate']}%")
print(f"CRR: {rates['crr']}%")
```

---

#### get_inflation_data()

Get inflation metrics.

**Signature**:
```python
def get_inflation_data(self) -> dict
```

**Returns**:
- dict: CPI, WPI, and food inflation

---

#### get_gdp_growth()

Get GDP growth data.

**Signature**:
```python
def get_gdp_growth(self) -> dict
```

**Returns**:
- dict: Quarterly and annual GDP growth rates

---

## Module: maverick_mcp.providers.exchange_rate

### ExchangeRateProvider

Currency conversion (INR/USD).

**Class**: `ExchangeRateProvider`

**Methods**:

#### get_current_rate()

Get current INR/USD exchange rate.

**Signature**:
```python
def get_current_rate(self) -> float
```

**Returns**:
- float: Current INR per USD rate

**Example**:
```python
from maverick_mcp.providers.exchange_rate import ExchangeRateProvider

provider = ExchangeRateProvider()
rate = provider.get_current_rate()

usd_amount = 100
inr_amount = usd_amount * rate
print(f"${usd_amount} = ₹{inr_amount}")
```

---

#### convert()

Convert between INR and USD.

**Signature**:
```python
def convert(
    self,
    amount: float,
    from_currency: str,
    to_currency: str
) -> float
```

**Parameters**:
- `amount` (float): Amount to convert
- `from_currency` (str): "INR" or "USD"
- `to_currency` (str): "INR" or "USD"

**Returns**:
- float: Converted amount

---

## Module: maverick_mcp.providers.openrouter_provider

### OpenRouterProvider

AI model access via OpenRouter.

**Class**: `OpenRouterProvider`

**Initialization**:
```python
from maverick_mcp.providers.openrouter_provider import OpenRouterProvider

provider = OpenRouterProvider(api_key="your-openrouter-key")
```

**Methods**:

#### get_completion()

Get AI completion.

**Signature**:
```python
def get_completion(
    self,
    prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> str
```

**Parameters**:
- `prompt` (str): Input prompt
- `model` (str, optional): Model name (auto-selects if None)
- `temperature` (float, optional): Randomness (0-1). Default: 0.7
- `max_tokens` (int, optional): Max response length. Default: 1000

**Returns**:
- str: AI-generated response

**Supported Models**:
- Claude Opus 4.1, Claude Sonnet 4, Claude 3.5 Haiku
- GPT-5, GPT-5 Nano
- Gemini 2.5 Pro
- DeepSeek R1
- And 400+ more

**Auto-Selection**: Chooses optimal model based on:
- Task complexity
- Cost efficiency (40-60% savings)
- Response quality requirements

**Example**:
```python
provider = OpenRouterProvider()

# Auto-select model
response = provider.get_completion(
    "Summarize Apple's Q4 2024 earnings"
)

# Specific model
response = provider.get_completion(
    "Detailed financial analysis of Apple",
    model="anthropic/claude-opus-4"
)
```

---

## Module: maverick_mcp.providers.macro_data

### MacroDataProvider

FRED API integration for macroeconomic data.

**Class**: `MacroDataProvider`

**Methods**:

#### get_series()

Get economic data series.

**Signature**:
```python
def get_series(
    self,
    series_id: str,
    start_date: str | None = None,
    end_date: str | None = None
) -> pd.DataFrame
```

**Parameters**:
- `series_id` (str): FRED series ID (e.g., "GDP", "UNRATE", "CPIAUCSL")
- `start_date` (str, optional): Start date (YYYY-MM-DD)
- `end_date` (str, optional): End date (YYYY-MM-DD)

**Returns**:
- pd.DataFrame: Time series data

**Common Series IDs**:
- `GDP`: Gross Domestic Product
- `UNRATE`: Unemployment Rate
- `CPIAUCSL`: Consumer Price Index
- `DFF`: Federal Funds Rate
- `DGS10`: 10-Year Treasury Rate

**Example**:
```python
from maverick_mcp.providers.macro_data import MacroDataProvider

provider = MacroDataProvider()

# Get GDP data
gdp = provider.get_series("GDP", start_date="2020-01-01")

# Get unemployment rate
unemployment = provider.get_series("UNRATE")
```

---

## Module: maverick_mcp.providers.indian_news

### IndianNewsProvider

Multi-source Indian financial news.

**Class**: `IndianNewsProvider`

**Methods**:

#### get_news()

Fetch news articles.

**Signature**:
```python
def get_news(
    self,
    query: str | None = None,
    limit: int = 10
) -> list[dict]
```

**Parameters**:
- `query` (str, optional): Search query
- `limit` (int, optional): Max articles. Default: 10

**Returns**:
- list[dict]: Articles with title, url, source, published_date, sentiment

**Sources**:
- MoneyControl
- Economic Times
- Business Standard
- Livemint
- The Hindu Business Line

**Example**:
```python
from maverick_mcp.providers.indian_news import IndianNewsProvider

provider = IndianNewsProvider()

# Get general news
news = provider.get_news(limit=5)

# Search specific topic
reliance_news = provider.get_news(query="Reliance Industries", limit=10)

for article in reliance_news:
    print(f"{article['title']} - {article['sentiment']}")
```

---

## Best Practices

### API Key Management

```python
import os

# Use environment variables
api_key = os.getenv("TIINGO_API_KEY")
provider = StockDataProvider(api_key=api_key)
```

### Error Handling

```python
from maverick_mcp.providers.stock_data import StockDataProvider, APIError

provider = StockDataProvider()

try:
    data = provider.get_historical_data("AAPL")
except APIError as e:
    print(f"API error: {e}")
except ValueError as e:
    print(f"Invalid input: {e}")
```

### Rate Limiting

```python
import time

provider = StockDataProvider()

tickers = ["AAPL", "MSFT", "GOOGL"]
for ticker in tickers:
    data = provider.get_quote(ticker)
    time.sleep(0.5)  # Respect rate limits
```

### Caching

```python
from maverick_mcp.data.cache import CacheManager

cache = CacheManager()
provider = StockDataProvider()

def get_cached_quote(ticker: str) -> dict:
    cache_key = f"quote:{ticker}"
    
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    quote = provider.get_quote(ticker)
    cache.set(cache_key, quote, ttl=300)  # 5 minutes
    return quote
```

### Multi-Market Support

```python
# US stock
us_data = provider.get_historical_data("AAPL")

# Indian NSE stock
nse_data = provider.get_historical_data("RELIANCE.NS")

# Indian BSE stock
bse_data = provider.get_historical_data("TCS.BO")
```
