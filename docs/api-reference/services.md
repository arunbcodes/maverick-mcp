# Services API Reference

Business logic services for stock analysis and market data.

## Module: maverick_mcp.services.screening_service

### ScreeningService

Stock screening and strategy execution service.

**Class**: `ScreeningService`

**Methods**:

#### get_maverick_bullish()

Get stocks matching Maverick bullish criteria.

**Signature**:
```python
def get_maverick_bullish(
    self,
    limit: int = 10,
    min_score: float = 70.0
) -> list[dict]
```

**Parameters**:
- `limit` (int, optional): Maximum results. Default: 10
- `min_score` (float, optional): Minimum score (0-100). Default: 70.0

**Returns**:
- list[dict]: Stocks with scores and signals

**Criteria**:
- RSI 50-70 (strong momentum)
- MACD bullish
- Price above 20 SMA
- Volume above average

**Example**:
```python
from maverick_mcp.services.screening_service import ScreeningService

service = ScreeningService()
stocks = service.get_maverick_bullish(limit=5, min_score=75)

for stock in stocks:
    print(f"{stock['ticker']}: {stock['score']}/100")
```

---

#### get_maverick_bearish()

Get stocks matching Maverick bearish criteria.

**Signature**:
```python
def get_maverick_bearish(
    self,
    limit: int = 10,
    min_score: float = 70.0
) -> list[dict]
```

**Criteria**:
- RSI 30-50 (weak momentum)
- MACD bearish
- Price below 20 SMA
- Volume declining

---

#### get_breakout_candidates()

Get supply/demand breakout candidates.

**Signature**:
```python
def get_breakout_candidates(
    self,
    limit: int = 10,
    min_score: float = 75.0
) -> list[dict]
```

**Criteria**:
- Price above all major MAs (20, 50, 200)
- Volume surge
- Near 52-week high
- Strong relative strength

---

## Module: maverick_mcp.services.market_calendar_service

### MarketCalendarService

Market trading calendar and status service.

**Class**: `MarketCalendarService`

**Methods**:

#### is_market_open()

Check if market is currently open.

**Signature**:
```python
def is_market_open(self, market: str = "US") -> bool
```

**Parameters**:
- `market` (str, optional): Market code ("US", "NSE", "BSE"). Default: "US"

**Returns**:
- bool: True if market is currently open

**Trading Hours**:
- **US (NYSE)**: 9:30 AM - 4:00 PM EST (Mon-Fri)
- **NSE**: 9:15 AM - 3:30 PM IST (Mon-Fri)
- **BSE**: 9:15 AM - 3:30 PM IST (Mon-Fri)

**Example**:
```python
from maverick_mcp.services.market_calendar_service import MarketCalendarService

service = MarketCalendarService()

if service.is_market_open("US"):
    print("US market is open")

if service.is_market_open("NSE"):
    print("Indian NSE is open")
```

---

#### get_next_trading_day()

Get next trading day.

**Signature**:
```python
def get_next_trading_day(
    self,
    from_date: date | None = None,
    market: str = "US"
) -> date
```

**Parameters**:
- `from_date` (date, optional): Start date. Default: today
- `market` (str, optional): Market code. Default: "US"

**Returns**:
- date: Next trading day

**Example**:
```python
from datetime import date

next_day = service.get_next_trading_day()
print(f"Next US trading day: {next_day}")

next_nse = service.get_next_trading_day(market="NSE")
print(f"Next NSE trading day: {next_nse}")
```

---

#### get_trading_days()

Get trading days in date range.

**Signature**:
```python
def get_trading_days(
    self,
    start_date: date,
    end_date: date,
    market: str = "US"
) -> list[date]
```

**Parameters**:
- `start_date` (date): Range start
- `end_date` (date): Range end
- `market` (str, optional): Market code. Default: "US"

**Returns**:
- list[date]: List of trading days

---

#### is_trading_day()

Check if date is a trading day.

**Signature**:
```python
def is_trading_day(
    self,
    check_date: date,
    market: str = "US"
) -> bool
```

**Parameters**:
- `check_date` (date): Date to check
- `market` (str, optional): Market code. Default: "US"

**Returns**:
- bool: True if trading day

---

## Module: maverick_mcp.api.services.portfolio_service

### PortfolioService

Portfolio management and analysis service.

**Class**: `PortfolioService`

**Methods**:

#### optimize_portfolio()

Optimize portfolio weights using Modern Portfolio Theory.

**Signature**:
```python
def optimize_portfolio(
    self,
    tickers: list[str],
    target_return: float | None = None,
    risk_free_rate: float = 0.03
) -> dict
```

**Parameters**:
- `tickers` (list[str]): List of stock symbols
- `target_return` (float, optional): Target annual return
- `risk_free_rate` (float, optional): Risk-free rate. Default: 0.03

**Returns**:
- dict: Contains:
  - `optimal_weights` (dict): Asset allocation {ticker: weight}
  - `expected_return` (float): Expected annual return
  - `volatility` (float): Portfolio volatility
  - `sharpe_ratio` (float): Sharpe ratio

**Example**:
```python
from maverick_mcp.api.services.portfolio_service import PortfolioService

service = PortfolioService()

result = service.optimize_portfolio(
    tickers=["AAPL", "MSFT", "GOOGL", "AMZN"],
    target_return=0.15
)

print(f"Expected Return: {result['expected_return']:.2%}")
print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")

for ticker, weight in result['optimal_weights'].items():
    print(f"{ticker}: {weight:.2%}")
```

---

#### analyze_risk()

Analyze portfolio risk metrics.

**Signature**:
```python
def analyze_risk(
    self,
    holdings: dict[str, int],
    purchase_prices: dict[str, float] | None = None
) -> dict
```

**Parameters**:
- `holdings` (dict): {ticker: shares} pairs
- `purchase_prices` (dict, optional): {ticker: price} pairs

**Returns**:
- dict: Contains:
  - `volatility` (float): Annual volatility
  - `var_95` (float): Value at Risk (95%)
  - `cvar_95` (float): Conditional VaR (95%)
  - `max_drawdown` (float): Maximum drawdown
  - `beta` (float): Market sensitivity
  - `alpha` (float): Excess returns

**Example**:
```python
holdings = {
    "AAPL": 10,
    "MSFT": 5,
    "GOOGL": 3
}

risk = service.analyze_risk(holdings)
print(f"Volatility: {risk['volatility']:.2%}")
print(f"Max Drawdown: {risk['max_drawdown']:.2%}")
print(f"Beta: {risk['beta']:.2f}")
```

---

#### calculate_correlation_matrix()

Calculate asset correlation matrix.

**Signature**:
```python
def calculate_correlation_matrix(
    self,
    tickers: list[str],
    lookback_days: int = 365
) -> pd.DataFrame
```

**Parameters**:
- `tickers` (list[str]): Stock symbols
- `lookback_days` (int, optional): Historical period. Default: 365

**Returns**:
- pd.DataFrame: Correlation matrix

---

## Module: maverick_mcp.api.services.market_service

### MarketService

Market data and indices service.

**Class**: `MarketService`

**Methods**:

#### get_market_overview()

Get comprehensive market overview.

**Signature**:
```python
def get_market_overview(self) -> dict
```

**Returns**:
- dict: Contains:
  - `indices` (dict): Major indices (S&P 500, Nasdaq, Dow, etc.)
  - `sectors` (list): Sector performance
  - `breadth` (dict): Market breadth indicators
  - `vix` (float): Volatility index

**Example**:
```python
from maverick_mcp.api.services.market_service import MarketService

service = MarketService()
overview = service.get_market_overview()

print(f"S&P 500: {overview['indices']['SPX']['change_percent']}%")
print(f"VIX: {overview['vix']}")

for sector in overview['sectors']:
    print(f"{sector['name']}: {sector['change_percent']}%")
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

---

## Module: maverick_mcp.domain.services.technical_analysis_service

### TechnicalAnalysisService

Technical analysis computation service.

**Class**: `TechnicalAnalysisService`

**Methods**:

#### calculate_full_analysis()

Calculate all technical indicators for a stock.

**Signature**:
```python
def calculate_full_analysis(
    self,
    ticker: str,
    lookback_days: int = 365
) -> dict
```

**Parameters**:
- `ticker` (str): Stock symbol
- `lookback_days` (int, optional): Historical period. Default: 365

**Returns**:
- dict: Contains all indicators:
  - SMAs (20, 50, 200)
  - EMAs (12, 26)
  - RSI (14)
  - MACD
  - Bollinger Bands
  - Support/Resistance levels
  - Trend direction
  - Buy/Sell signals

**Example**:
```python
from maverick_mcp.domain.services.technical_analysis_service import TechnicalAnalysisService

service = TechnicalAnalysisService()
analysis = service.calculate_full_analysis("AAPL")

print(f"RSI: {analysis['rsi']['current']}")
print(f"MACD Signal: {analysis['macd']['signal']}")
print(f"Trend: {analysis['trend']['direction']}")

if analysis['signals']['buy']:
    print("Buy signals detected")
```

---

## Best Practices

### Service Initialization

```python
# Initialize services once, reuse
screening_service = ScreeningService()
market_calendar = MarketCalendarService()
portfolio_service = PortfolioService()
```

### Error Handling

```python
try:
    stocks = screening_service.get_maverick_bullish()
except ValueError as e:
    print(f"Invalid parameters: {e}")
except ServiceError as e:
    print(f"Service error: {e}")
```

### Caching Results

```python
from maverick_mcp.data.cache import CacheManager

cache = CacheManager()

def get_cached_screening(strategy: str, limit: int = 10):
    cache_key = f"screening:{strategy}:{limit}"
    
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    if strategy == "bullish":
        results = screening_service.get_maverick_bullish(limit)
    else:
        results = screening_service.get_maverick_bearish(limit)
    
    cache.set(cache_key, results, ttl=86400)  # 24 hours
    return results
```

### Market Hours Checking

```python
# Check before making data requests
if not market_calendar.is_market_open("US"):
    print("Market closed - using cached data")
    use_cached_data = True
```

### Multi-Market Support

```python
# Check different markets
us_open = market_calendar.is_market_open("US")
nse_open = market_calendar.is_market_open("NSE")
bse_open = market_calendar.is_market_open("BSE")

print(f"US: {'🟢' if us_open else '🔴'}")
print(f"NSE: {'🟢' if nse_open else '🔴'}")
print(f"BSE: {'🟢' if bse_open else '🔴'}")
```

### Portfolio Optimization Workflow

```python
# 1. Analyze current holdings
risk = portfolio_service.analyze_risk(current_holdings)

# 2. Calculate correlation
tickers = list(current_holdings.keys())
correlation = portfolio_service.calculate_correlation_matrix(tickers)

# 3. Optimize allocation
optimized = portfolio_service.optimize_portfolio(
    tickers,
    target_return=0.12
)

# 4. Compare
print(f"Current Sharpe: {risk['sharpe_ratio']:.2f}")
print(f"Optimized Sharpe: {optimized['sharpe_ratio']:.2f}")
```
