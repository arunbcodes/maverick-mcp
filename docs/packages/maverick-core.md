# maverick-core

Core domain logic, interfaces, and utilities for Maverick MCP.

## Overview

`maverick-core` is the foundation package containing:

- **Domain Entities**: Portfolio, Position, and other business objects
- **Interfaces**: Protocol-based contracts for all services
- **Technical Analysis**: Pure functions for indicators
- **Configuration**: Centralized settings management
- **Exceptions**: Comprehensive exception hierarchy
- **Resilience**: Circuit breakers and fallback strategies
- **Logging**: Structured logging with correlation IDs
- **Validation**: Input validation utilities

!!! info "Zero Framework Dependencies"
    This package has minimal external dependencies (numpy, pandas, pydantic) and no framework dependencies like SQLAlchemy or Redis.

## Installation

```bash
pip install maverick-core
```

## Configuration

### Settings Management

```python
from maverick_core import Settings, get_settings

# Get singleton settings
settings = get_settings()

# Access configuration
print(settings.database_url)
print(settings.redis_url)
print(settings.tiingo_api_key)
print(settings.log_level)
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `sqlite:///maverick.db` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENVIRONMENT` | Environment name | `development` |
| `TIINGO_API_KEY` | Stock data API key | Required |
| `OPENROUTER_API_KEY` | LLM API key | Optional |
| `EXA_API_KEY` | Web search API key | Optional |

### Custom Settings

```python
from maverick_core import Settings

# Create with custom values
settings = Settings(
    database_url="postgresql://user:pass@localhost/db",
    log_level="DEBUG",
    environment="production"
)
```

## Domain Entities

### Portfolio & Position

```python
from maverick_core.domain import Portfolio, Position
from decimal import Decimal
from datetime import datetime, UTC

# Create a portfolio
portfolio = Portfolio(
    portfolio_id="my-portfolio",
    user_id="default",
    name="My Investments"
)

# Add positions
portfolio.add_position(
    ticker="AAPL",
    shares=Decimal("10"),
    price=Decimal("150.00"),
    date=datetime.now(UTC)
)

portfolio.add_position(
    ticker="MSFT",
    shares=Decimal("5"),
    price=Decimal("400.00"),
    date=datetime.now(UTC)
)

# Get position
position = portfolio.get_position("AAPL")
print(f"AAPL: {position.shares} shares @ ${position.cost_basis}")

# Calculate metrics with current prices
metrics = portfolio.calculate_portfolio_metrics({
    "AAPL": Decimal("175.00"),
    "MSFT": Decimal("420.00")
})

print(f"Total Value: ${metrics['total_current_value']:,.2f}")
print(f"Total P&L: ${metrics['total_pnl']:,.2f}")
print(f"P&L %: {metrics['total_pnl_percent']:.2f}%")
```

### Position Operations

```python
# Add to existing position (averages cost)
position = position.add_shares(
    shares=Decimal("5"),
    price=Decimal("160.00")
)

# Remove shares
remaining = position.remove_shares(Decimal("3"))

# Calculate current value
pnl = position.calculate_current_value(Decimal("175.00"))
print(f"Unrealized P&L: ${pnl['pnl']:,.2f}")
```

## Interfaces

All services implement interfaces for testability and flexibility.

### Stock Data Interface

```python
from maverick_core.interfaces import IStockDataFetcher
import pandas as pd

class MyDataProvider(IStockDataFetcher):
    """Custom data provider implementation."""
    
    async def get_stock_data(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        # Your implementation
        ...
    
    async def get_stock_info(self, symbol: str) -> dict:
        # Your implementation
        ...
```

### Available Interfaces

| Interface | Package | Purpose |
|-----------|---------|---------|
| `IStockDataFetcher` | maverick-data | Stock data fetching |
| `IStockScreener` | maverick-data | Stock screening |
| `ICacheProvider` | maverick-data | Cache operations |
| `IRepository` | maverick-data | Data persistence |
| `IStockRepository` | maverick-data | Stock-specific persistence |
| `IPortfolioRepository` | maverick-data | Portfolio persistence |
| `ITechnicalAnalyzer` | maverick-backtest | Technical analysis |
| `IMarketCalendar` | maverick-data | Market hours/holidays |
| `ILLMProvider` | maverick-agents | LLM access |
| `IResearchAgent` | maverick-agents | Research operations |
| `IBacktestEngine` | maverick-backtest | Backtesting |
| `IStrategy` | maverick-backtest | Trading strategies |

## Technical Analysis

Pure functions for calculating technical indicators.

### Moving Averages

```python
from maverick_core.technical import calculate_sma, calculate_ema
import pandas as pd

# Sample data
df = pd.DataFrame({
    'Close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
})

# Simple Moving Average
df['SMA_5'] = calculate_sma(df['Close'], period=5)

# Exponential Moving Average
df['EMA_5'] = calculate_ema(df['Close'], period=5)
```

### RSI

```python
from maverick_core.technical import calculate_rsi

# RSI (default period=14)
df['RSI'] = calculate_rsi(df['Close'], period=14)

# Overbought/oversold signals
df['Signal'] = df['RSI'].apply(
    lambda x: 'Overbought' if x > 70 else ('Oversold' if x < 30 else 'Neutral')
)
```

### MACD

```python
from maverick_core.technical import calculate_macd

# Calculate MACD
macd = calculate_macd(
    df['Close'],
    fast_period=12,
    slow_period=26,
    signal_period=9
)

df['MACD'] = macd['macd']
df['MACD_Signal'] = macd['signal']
df['MACD_Histogram'] = macd['histogram']
```

### Bollinger Bands

```python
from maverick_core.technical import calculate_bollinger_bands

# Calculate Bollinger Bands
bb = calculate_bollinger_bands(df['Close'], period=20, std_dev=2)

df['BB_Upper'] = bb['upper']
df['BB_Middle'] = bb['middle']
df['BB_Lower'] = bb['lower']
```

### All Available Indicators

| Function | Parameters | Returns |
|----------|-----------|---------|
| `calculate_sma` | prices, period | Series |
| `calculate_ema` | prices, period | Series |
| `calculate_rsi` | prices, period | Series |
| `calculate_macd` | prices, fast, slow, signal | Dict |
| `calculate_bollinger_bands` | prices, period, std_dev | Dict |
| `calculate_atr` | high, low, close, period | Series |
| `calculate_stochastic` | high, low, close, k, d | Dict |
| `calculate_momentum` | prices, period | Series |
| `calculate_obv` | close, volume | Series |
| `calculate_support_resistance` | high, low, close | Dict |
| `calculate_trend_strength` | prices, period | Series |

## Exceptions

Comprehensive exception hierarchy for error handling.

### Exception Hierarchy

```
MaverickException (base)
├── ValidationError
│   ├── ParameterValidationError
│   └── DataValidationError
├── StockDataError
│   ├── SymbolNotFoundError
│   └── DataProviderError
├── CacheError
│   └── CacheConnectionError
├── DatabaseError
│   ├── DatabaseConnectionError
│   └── DataIntegrityError
├── StrategyError
│   └── BacktestError
├── AgentError
│   ├── AgentInitializationError
│   └── AgentExecutionError
├── LLMError
├── RateLimitError
│   └── APIRateLimitError
├── CircuitBreakerError
└── ExternalServiceError
```

### Usage

```python
from maverick_core import (
    MaverickException,
    ValidationError,
    StockDataError,
    SymbolNotFoundError,
)

def get_stock_data(ticker: str) -> dict:
    if not ticker:
        raise ValidationError("Ticker symbol is required")
    
    if ticker not in valid_tickers:
        raise SymbolNotFoundError(f"Symbol not found: {ticker}")
    
    try:
        return fetch_data(ticker)
    except APIError as e:
        raise StockDataError(f"Failed to fetch {ticker}: {e}") from e
```

### Error Codes

```python
from maverick_core.exceptions import ERROR_CODES, get_error_message

# Get human-readable message
message = get_error_message("VALIDATION_ERROR")
# "Invalid input parameters provided"
```

## Resilience

Circuit breakers and fallback strategies for robust APIs.

### Circuit Breaker

```python
from maverick_core.resilience import circuit_breaker, CircuitBreakerError

@circuit_breaker(
    name="stock_api",
    failure_threshold=3,
    recovery_timeout=60
)
def fetch_stock_data(ticker: str) -> dict:
    return external_api.get(ticker)

# Usage
try:
    data = fetch_stock_data("AAPL")
except CircuitBreakerError:
    # Circuit is open, use fallback
    data = get_cached_data("AAPL")
```

### Circuit Breaker Configuration

```python
from maverick_core.resilience import (
    EnhancedCircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    FailureDetectionStrategy
)

config = CircuitBreakerConfig(
    name="api_breaker",
    failure_threshold=5,
    recovery_timeout=30,
    half_open_max_calls=3,
    detection_strategy=FailureDetectionStrategy.CONSECUTIVE_FAILURES
)

breaker = EnhancedCircuitBreaker(config)

# Manual check
if breaker.is_closed:
    result = breaker.call_sync(lambda: api.get("AAPL"))
```

### Fallback Strategies

```python
from maverick_core.resilience import FallbackChain, FallbackStrategy

class CacheFallback(FallbackStrategy):
    def can_execute(self, context: dict) -> bool:
        return "ticker" in context
    
    def execute_sync(self, context: dict) -> dict:
        return cache.get(f"stock:{context['ticker']}")

class DefaultFallback(FallbackStrategy):
    def can_execute(self, context: dict) -> bool:
        return True
    
    def execute_sync(self, context: dict) -> dict:
        return {"error": "Data unavailable"}

# Chain fallbacks
chain = FallbackChain([
    CacheFallback(),
    DefaultFallback()
])

result = chain.execute_sync({"ticker": "AAPL"})
```

## Logging

Structured logging with correlation IDs.

### Basic Usage

```python
from maverick_core import get_logger, setup_logging

# Setup logging
setup_logging(level="INFO", format="json")

# Get logger
logger = get_logger(__name__)

logger.info("Processing request", extra={
    "ticker": "AAPL",
    "action": "fetch_data"
})
```

### Correlation IDs

```python
from maverick_core.logging import (
    with_correlation_id,
    get_correlation_id,
    set_correlation_id
)

@with_correlation_id
def process_request(request_id: str):
    logger.info("Processing", extra={"request_id": request_id})
    # All logs in this context will have the correlation ID
    fetch_data()
    analyze_data()

# Manual correlation ID
set_correlation_id("req-12345")
logger.info("Manual correlation")
print(get_correlation_id())  # "req-12345"
```

### Structured Output

```python
# JSON format output:
{
    "timestamp": "2025-01-15T10:30:00.000Z",
    "level": "INFO",
    "message": "Processing request",
    "correlation_id": "req-12345",
    "ticker": "AAPL",
    "action": "fetch_data",
    "module": "maverick_data.providers"
}
```

## Validation

Input validation utilities.

### Built-in Validators

```python
from maverick_core.validation import (
    validate_symbol,
    validate_date_range,
    validate_positive_number,
    validate_in_range,
    validate_percentage,
)

# Symbol validation
validate_symbol("AAPL")           # OK
validate_symbol("RELIANCE.NS")    # OK
validate_symbol("invalid@sym")    # Raises ValidationError

# Date range validation
validate_date_range("2024-01-01", "2024-12-31")  # OK
validate_date_range("2024-12-31", "2024-01-01")  # Raises ValidationError

# Number validation
validate_positive_number(100)     # OK
validate_positive_number(-1)      # Raises ValidationError

# Range validation
validate_in_range(50, 0, 100)     # OK
validate_percentage(150)          # Raises ValidationError
```

### Pydantic Models

```python
from maverick_core.validation import (
    BaseRequest,
    TickerSymbol,
    DateString,
    PositiveFloat,
    Percentage
)

class StockRequest(BaseRequest):
    ticker: TickerSymbol
    start_date: DateString | None = None
    end_date: DateString | None = None
    confidence: Percentage = 0.95
    amount: PositiveFloat = 10000.0

# Automatic validation
request = StockRequest(
    ticker="AAPL",
    start_date="2024-01-01",
    confidence=0.95
)
```

## Testing

### Unit Tests

```python
from maverick_core.domain import Portfolio
from decimal import Decimal

def test_portfolio_add_position():
    portfolio = Portfolio("test", "user1", "Test Portfolio")
    
    portfolio.add_position("AAPL", Decimal("10"), Decimal("150"))
    
    position = portfolio.get_position("AAPL")
    assert position.shares == Decimal("10")
    assert position.cost_basis == Decimal("150")
```

### Mocking Interfaces

```python
from unittest.mock import Mock
from maverick_core.interfaces import IStockDataFetcher
import pandas as pd

def test_with_mock_provider():
    # Create mock
    mock_provider = Mock(spec=IStockDataFetcher)
    mock_provider.get_stock_data.return_value = pd.DataFrame({
        "Close": [100, 101, 102]
    })
    
    # Use in tests
    result = mock_provider.get_stock_data("AAPL")
    assert len(result) == 3
```

## API Reference

For detailed API documentation, see:

- [Configuration API](../api-reference/maverick-core/config.md)
- [Logging API](../api-reference/maverick-core/logging.md)
- [Exceptions API](../api-reference/maverick-core/exceptions.md)
- [Resilience API](../api-reference/maverick-core/resilience.md)

