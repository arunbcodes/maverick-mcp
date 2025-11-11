# Code Style Guide

Code style conventions and best practices for Maverick MCP.

## Overview

Maverick MCP follows modern Python best practices:

- **PEP 8 Compliant**: Standard Python style guide
- **Type Hints**: Comprehensive type annotations
- **Google Docstrings**: Clear, structured documentation
- **Clean Code**: Readable, maintainable, self-documenting
- **Automated Formatting**: ruff for consistency
- **Type Checking**: ty (Astral's modern type checker)

## Quick Start

```bash
# Format code automatically
make format

# Check code quality
make lint

# Type checking
make typecheck

# Run all checks
make check
```

## Python Version

**Target**: Python 3.12+

**Why**: Modern features for cleaner code:
- Type hints with `|` union syntax
- Pattern matching with `match/case`
- Better error messages
- Performance improvements

```python
# ✅ Python 3.12+ syntax
def get_stock_data(ticker: str) -> dict | None:
    match ticker:
        case str() if ticker.endswith(".NS"):
            return fetch_nse_data(ticker)
        case str() if ticker.endswith(".BO"):
            return fetch_bse_data(ticker)
        case _:
            return fetch_us_data(ticker)

# ❌ Old syntax (don't use)
from typing import Union, Optional

def get_stock_data(ticker: str) -> Optional[dict]:
    if ticker.endswith(".NS"):
        return fetch_nse_data(ticker)
    elif ticker.endswith(".BO"):
        return fetch_bse_data(ticker)
    else:
        return fetch_us_data(ticker)
```

## Formatting

### Automated with ruff

**ruff** is an extremely fast Python linter and formatter written in Rust.

```bash
# Auto-format all code
ruff format .

# Or use make
make format

# Check formatting without modifying
ruff format --check .
```

### Configuration

**pyproject.toml**:
```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort (import sorting)
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by formatter)
    "B008",  # function calls in argument defaults
    "B904",  # raise without from inside except
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### Line Length

**Maximum**: 88 characters (Black/ruff standard)

```python
# ✅ Good - Under 88 characters
result = calculate_technical_indicators(
    data=stock_data,
    period=14,
    include_volume=True
)

# ❌ Bad - Over 88 characters, hard to read
result = calculate_technical_indicators(data=stock_data, period=14, include_volume=True, apply_smoothing=True)
```

### Quotes

**Use double quotes** for strings:

```python
# ✅ Good
message = "Stock data fetched successfully"
ticker = "AAPL"

# ❌ Bad
message = 'Stock data fetched successfully'
ticker = 'AAPL'
```

**Exception**: Triple quotes for docstrings (always double):
```python
"""This is a docstring."""
```

### Imports

**Order** (enforced by ruff):
1. Standard library
2. Third-party packages
3. Local application

**Format**:
```python
# ✅ Good - Organized and sorted
import asyncio
import logging
from datetime import datetime
from typing import Any

import pandas as pd
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from maverick_mcp.config.settings import settings
from maverick_mcp.data.models import Stock, StockPrice
from maverick_mcp.providers.stock_data import StockDataProvider

# ❌ Bad - Mixed and unsorted
from maverick_mcp.data.models import Stock
import pandas as pd
from typing import Any
import logging
from maverick_mcp.providers.stock_data import StockDataProvider
import numpy as np
```

**Avoid star imports**:
```python
# ❌ Bad - Pollutes namespace
from maverick_mcp.core.technical_analysis import *

# ✅ Good - Explicit imports
from maverick_mcp.core.technical_analysis import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
)
```

### Spacing

**Around operators**:
```python
# ✅ Good
x = 1 + 2
result = price * quantity
is_valid = value > 0 and value < 100

# ❌ Bad
x=1+2
result=price*quantity
is_valid=value>0 and value<100
```

**After commas**:
```python
# ✅ Good
stocks = ["AAPL", "MSFT", "GOOGL"]
data = {"ticker": "AAPL", "price": 150.0}

# ❌ Bad
stocks = ["AAPL","MSFT","GOOGL"]
data = {"ticker":"AAPL","price":150.0}
```

**Blank lines**:
```python
# ✅ Good - Clear separation
class StockAnalyzer:
    """Analyze stock data."""

    def __init__(self, ticker: str):
        self.ticker = ticker

    def fetch_data(self) -> pd.DataFrame:
        """Fetch historical stock data."""
        return self._provider.get_stock_data(self.ticker)

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators."""
        data = calculate_rsi(data, period=14)
        data = calculate_macd(data)
        return data


class PortfolioAnalyzer:
    """Analyze portfolio performance."""
    pass


# ❌ Bad - No separation
class StockAnalyzer:
    def __init__(self, ticker: str):
        self.ticker = ticker
    def fetch_data(self) -> pd.DataFrame:
        return self._provider.get_stock_data(self.ticker)
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        data = calculate_rsi(data, period=14)
        return data
class PortfolioAnalyzer:
    pass
```

## Type Hints

### Required

**All public functions** must have type hints:

```python
# ✅ Good - Complete type hints
def calculate_rsi(
    data: pd.DataFrame,
    period: int = 14,
    price_col: str = "Close"
) -> pd.DataFrame:
    """Calculate RSI indicator."""
    pass

# ❌ Bad - No type hints
def calculate_rsi(data, period=14, price_col="Close"):
    """Calculate RSI indicator."""
    pass
```

### Modern Syntax (Python 3.12+)

**Use `|` for unions**:
```python
# ✅ Good - Modern syntax
def get_stock_data(ticker: str) -> dict | None:
    pass

def process_value(value: int | float | str) -> str:
    pass

# ❌ Bad - Old syntax
from typing import Union, Optional

def get_stock_data(ticker: str) -> Optional[dict]:
    pass

def process_value(value: Union[int, float, str]) -> str:
    pass
```

### Complex Types

```python
from typing import Any, Literal

# ✅ Good - Precise types
def screen_stocks(
    strategy: Literal["bullish", "bearish", "breakout"],
    limit: int = 10,
    filters: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Screen stocks using specified strategy."""
    pass

# Return type aliases for clarity
StockData = dict[str, float | int | str]
ScreeningResult = list[StockData]

def get_recommendations() -> ScreeningResult:
    pass
```

### Type Checking with ty

**ty** is Astral's extremely fast type checker.

```bash
# Check types
ty check .

# Or use make
make typecheck

# Ultra-fast with uvx (no installation)
uvx ty check .
```

## Naming Conventions

### Variables and Functions

**snake_case** for variables and functions:

```python
# ✅ Good
stock_price = 150.0
calculated_rsi = 65.5
user_portfolio = []

def calculate_moving_average(data: pd.DataFrame) -> pd.DataFrame:
    pass

def get_stock_info(ticker: str) -> dict:
    pass

# ❌ Bad
stockPrice = 150.0
CalculatedRSI = 65.5
userPortfolio = []

def CalculateMovingAverage(data):
    pass
```

### Classes

**PascalCase** for classes:

```python
# ✅ Good
class StockAnalyzer:
    pass

class TechnicalIndicatorCalculator:
    pass

class PortfolioOptimizer:
    pass

# ❌ Bad
class stock_analyzer:
    pass

class technical_indicator_calculator:
    pass
```

### Constants

**UPPER_SNAKE_CASE** for constants:

```python
# ✅ Good
MAX_RETRIES = 3
API_TIMEOUT = 30
DEFAULT_CACHE_TTL = 3600
SUPPORTED_MARKETS = ["US", "NSE", "BSE"]

# ❌ Bad
max_retries = 3
apiTimeout = 30
```

### Private Members

**Leading underscore** for private/internal:

```python
class StockDataProvider:
    def __init__(self):
        self._api_key = settings.TIINGO_API_KEY  # Private
        self._cache = {}                         # Private

    def get_stock_data(self, ticker: str) -> dict:  # Public
        return self._fetch_from_api(ticker)

    def _fetch_from_api(self, ticker: str) -> dict:  # Private
        pass
```

### Descriptive Names

**Use meaningful, descriptive names**:

```python
# ✅ Good - Clear intent
def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.03
) -> float:
    """Calculate Sharpe ratio for portfolio."""
    annualized_return = returns.mean() * 252
    annualized_volatility = returns.std() * np.sqrt(252)
    return (annualized_return - risk_free_rate) / annualized_volatility

# ❌ Bad - Unclear abbreviations
def calc_sr(r: pd.Series, rfr: float = 0.03) -> float:
    ar = r.mean() * 252
    av = r.std() * np.sqrt(252)
    return (ar - rfr) / av
```

## Docstrings

### Google Style

**Use Google-style docstrings** for all public APIs:

```python
def optimize_portfolio(
    tickers: list[str],
    target_return: float | None = None,
    risk_tolerance: float = 0.5
) -> dict[str, Any]:
    """Optimize portfolio allocation using Modern Portfolio Theory.

    Calculates optimal asset weights to maximize Sharpe ratio or achieve
    target return with minimum variance.

    Args:
        tickers: List of stock symbols to include in portfolio.
        target_return: Target annual return (0.0-1.0). If None, maximizes
            Sharpe ratio instead.
        risk_tolerance: Risk preference (0.0=conservative, 1.0=aggressive).
            Affects constraint boundaries.

    Returns:
        Dictionary containing:
            - weights: Asset allocation percentages (dict[str, float])
            - expected_return: Projected annual return
            - volatility: Portfolio standard deviation
            - sharpe_ratio: Risk-adjusted return metric

    Raises:
        ValueError: If tickers list is empty or contains invalid symbols.
        APIError: If stock data cannot be fetched from provider.

    Example:
        >>> result = optimize_portfolio(["AAPL", "MSFT", "GOOGL"])
        >>> print(result["sharpe_ratio"])
        1.85
        >>> print(result["weights"])
        {"AAPL": 0.35, "MSFT": 0.40, "GOOGL": 0.25}

    Note:
        Uses historical data from past 5 years for correlation calculation.
        Results are for educational purposes only, not financial advice.
    """
    pass
```

### Module Docstrings

```python
"""Stock data provider for US and Indian markets.

This module provides a unified interface for fetching stock data from multiple
sources including Tiingo (US markets) and NSE/BSE (Indian markets).

Key Features:
    - Automatic market detection from ticker symbols
    - Multi-tier caching (Redis + Database + API)
    - Rate limiting and retry logic
    - Support for real-time and historical data

Example:
    >>> provider = StockDataProvider()
    >>> data = provider.get_stock_data("AAPL", period="1y")
    >>> indian_data = provider.get_stock_data("RELIANCE.NS", period="6mo")

See Also:
    - IndianMarketDataProvider for NSE/BSE specific features
    - CacheManager for caching configuration
"""
```

### Class Docstrings

```python
class ScreeningService:
    """Service for stock screening with multiple strategies.

    Provides pre-calculated screening results using various technical and
    fundamental strategies. Data is pre-seeded for S&P 500 stocks and
    updated daily.

    Attributes:
        _db_session: SQLAlchemy database session (optional)

    Available Strategies:
        - maverick_bullish: High momentum with strong technicals
        - maverick_bearish: Weak setups for short opportunities
        - supply_demand_breakout: Confirmed uptrend breakouts
        - indian_momentum: NSE/BSE momentum stocks

    Example:
        >>> service = ScreeningService()
        >>> results = service.get_maverick_recommendations(limit=10)
        >>> for stock in results:
        ...     print(f"{stock['ticker']}: {stock['combined_score']}")
    """

    def __init__(self, db_session: Session | None = None):
        """Initialize screening service.

        Args:
            db_session: Optional database session. If None, creates new
                session for each operation.
        """
        pass
```

### One-Line Docstrings

```python
# ✅ Good - Simple one-liners for obvious functions
def get_ticker_symbol(self) -> str:
    """Return the stock ticker symbol."""
    return self._ticker

# ✅ Good - More detail when needed
def validate_ticker_format(ticker: str) -> bool:
    """Validate ticker symbol format.

    Checks if ticker follows US (AAPL) or Indian (.NS, .BO) format.
    """
    pass
```

## Code Organization

### File Structure

```python
"""Module docstring at top."""

# Imports (sorted by ruff)
import standard_library
import third_party
from local_app import module

# Constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Type aliases
StockData = dict[str, Any]
ScreeningResult = list[StockData]

# Module-level variables (if needed)
logger = logging.getLogger(__name__)

# Functions and classes
def helper_function() -> None:
    """Helper function."""
    pass


class MainClass:
    """Main class."""
    pass


# Main execution (if applicable)
if __name__ == "__main__":
    main()
```

### Class Organization

```python
class StockAnalyzer:
    """Analyze stock data."""

    # Class constants
    DEFAULT_PERIOD = 14
    SUPPORTED_INDICATORS = ["RSI", "MACD", "BB"]

    # __init__ first
    def __init__(self, ticker: str):
        """Initialize analyzer."""
        self.ticker = ticker
        self._data: pd.DataFrame | None = None

    # Public methods next (alphabetically)
    def calculate_indicators(self) -> dict[str, Any]:
        """Calculate all technical indicators."""
        pass

    def fetch_data(self, period: str = "1y") -> pd.DataFrame:
        """Fetch historical stock data."""
        pass

    # Private methods last (alphabetically)
    def _validate_ticker(self, ticker: str) -> bool:
        """Validate ticker format."""
        pass

    # Special methods at end
    def __repr__(self) -> str:
        return f"StockAnalyzer(ticker={self.ticker})"
```

## Error Handling

### Explicit Exception Types

```python
# ✅ Good - Specific exceptions
try:
    data = fetch_stock_data(ticker)
except requests.HTTPError as e:
    logger.error(f"HTTP error fetching {ticker}: {e}")
    raise APIError(f"Failed to fetch {ticker}") from e
except ValueError as e:
    logger.error(f"Invalid ticker format: {ticker}")
    raise ValidationError(f"Invalid ticker: {ticker}") from e

# ❌ Bad - Bare except
try:
    data = fetch_stock_data(ticker)
except:
    logger.error("Error occurred")
    raise
```

### Custom Exceptions

```python
# Define custom exception hierarchy
class MaverickMCPError(Exception):
    """Base exception for Maverick MCP."""
    pass


class APIError(MaverickMCPError):
    """External API call failed."""
    pass


class ValidationError(MaverickMCPError):
    """Data validation failed."""
    pass


class CacheError(MaverickMCPError):
    """Cache operation failed."""
    pass
```

### Graceful Degradation

```python
# ✅ Good - Graceful fallback
def get_stock_data(ticker: str) -> dict | None:
    """Fetch stock data with fallback."""
    try:
        # Try Redis cache
        cached = cache.get(f"stock:{ticker}")
        if cached:
            return cached
    except CacheError as e:
        logger.warning(f"Cache unavailable: {e}")
        # Continue without cache

    try:
        # Try API
        data = api.fetch(ticker)
        return data
    except APIError as e:
        logger.error(f"API failed for {ticker}: {e}")
        return None  # Graceful failure
```

## Comments

### When to Comment

**Comment the "why", not the "what"**:

```python
# ✅ Good - Explains reasoning
# Use 252 trading days for annualization (US market standard)
annualized_return = daily_return * 252

# RSI values above 70 indicate overbought conditions per Wilder (1978)
if rsi > 70:
    signal = "overbought"

# ❌ Bad - States the obvious
# Multiply by 252
annualized_return = daily_return * 252

# Check if RSI is greater than 70
if rsi > 70:
    signal = "overbought"
```

### TODO Comments

```python
# TODO(username): Brief description of what needs to be done
# TODO(arun): Add support for sector-specific screening strategies

# FIXME(username): Brief description of the bug
# FIXME(arun): Race condition in parallel agent execution

# NOTE(username): Important information
# NOTE(arun): This endpoint rate limited to 500 calls/hour
```

### Financial Formulas

**Always document financial calculations**:

```python
def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.03
) -> float:
    """Calculate Sharpe ratio.

    Formula: (Portfolio Return - Risk-Free Rate) / Portfolio Volatility
    Reference: Sharpe, William F. (1966). "Mutual Fund Performance"

    Args:
        returns: Daily returns series
        risk_free_rate: Annual risk-free rate (default: 3%)

    Returns:
        Sharpe ratio (annualized)

    Note:
        - Returns are annualized using 252 trading days
        - Volatility is annualized using sqrt(252)
        - Risk-free rate should be annualized
    """
    # Annualize returns and volatility
    annual_return = returns.mean() * 252
    annual_volatility = returns.std() * np.sqrt(252)

    # Calculate Sharpe ratio
    sharpe = (annual_return - risk_free_rate) / annual_volatility

    return sharpe
```

## Best Practices

### 1. Single Responsibility

**Each function should do one thing**:

```python
# ✅ Good - Single responsibility
def fetch_stock_data(ticker: str) -> pd.DataFrame:
    """Fetch stock data from API."""
    return api.get(ticker)

def cache_stock_data(ticker: str, data: pd.DataFrame) -> None:
    """Cache stock data."""
    cache.set(f"stock:{ticker}", data, ttl=3600)

def process_stock_data(data: pd.DataFrame) -> pd.DataFrame:
    """Process and clean stock data."""
    return data.dropna().sort_values("Date")

# ❌ Bad - Multiple responsibilities
def fetch_and_process_stock_data(ticker: str) -> pd.DataFrame:
    """Fetch, cache, and process stock data."""
    data = api.get(ticker)
    cache.set(f"stock:{ticker}", data, ttl=3600)
    return data.dropna().sort_values("Date")
```

### 2. DRY (Don't Repeat Yourself)

```python
# ✅ Good - Reusable function
def calculate_annualized_metric(
    daily_values: pd.Series,
    metric: Literal["return", "volatility"]
) -> float:
    """Calculate annualized metric from daily values."""
    if metric == "return":
        return daily_values.mean() * 252
    elif metric == "volatility":
        return daily_values.std() * np.sqrt(252)

annual_return = calculate_annualized_metric(returns, "return")
annual_volatility = calculate_annualized_metric(returns, "volatility")

# ❌ Bad - Repeated logic
annual_return = returns.mean() * 252
annual_volatility = returns.std() * np.sqrt(252)
# ... repeated elsewhere in code
annual_return2 = returns2.mean() * 252
annual_volatility2 = returns2.std() * np.sqrt(252)
```

### 3. Early Returns

```python
# ✅ Good - Early returns for clarity
def get_stock_data(ticker: str) -> dict | None:
    """Fetch stock data with validation."""
    if not ticker:
        logger.warning("Empty ticker provided")
        return None

    if not validate_ticker_format(ticker):
        logger.error(f"Invalid ticker format: {ticker}")
        return None

    # Main logic
    return fetch_from_api(ticker)

# ❌ Bad - Nested conditions
def get_stock_data(ticker: str) -> dict | None:
    """Fetch stock data with validation."""
    if ticker:
        if validate_ticker_format(ticker):
            return fetch_from_api(ticker)
        else:
            logger.error(f"Invalid ticker format: {ticker}")
            return None
    else:
        logger.warning("Empty ticker provided")
        return None
```

### 4. Comprehensions

```python
# ✅ Good - List comprehensions for simple transformations
tickers = [t.upper().strip() for t in raw_tickers]
valid_tickers = [t for t in tickers if validate_ticker(t)]
prices = {ticker: data["Close"] for ticker, data in stock_data.items()}

# ❌ Bad - Unnecessary loops
tickers = []
for t in raw_tickers:
    tickers.append(t.upper().strip())
```

### 5. Context Managers

```python
# ✅ Good - Context manager for resources
with Session() as session:
    stocks = session.query(Stock).all()
    # Session automatically closed

# ✅ Good - Custom context manager
@contextmanager
def timed_operation(operation_name: str):
    """Time an operation."""
    start = time.time()
    yield
    elapsed = time.time() - start
    logger.info(f"{operation_name} took {elapsed:.2f}s")

with timed_operation("Backtesting"):
    results = run_backtest(strategy, data)
```

### 6. Use Built-ins

```python
# ✅ Good - Use built-in functions
total = sum(values)
maximum = max(values)
minimum = min(values)
has_positive = any(v > 0 for v in values)
all_positive = all(v > 0 for v in values)

# ❌ Bad - Manual loops
total = 0
for v in values:
    total += v
```

## Testing Conventions

See [Testing Guide](testing.md) for comprehensive testing conventions.

**Key points:**
- AAA pattern (Arrange-Act-Assert)
- Descriptive test names
- One concept per test
- Use fixtures for setup
- Mock external dependencies

## Logging

### Levels

```python
import logging

logger = logging.getLogger(__name__)

# DEBUG - Detailed diagnostic information
logger.debug(f"Fetching data for {ticker} from cache")

# INFO - General informational messages
logger.info(f"Stock data fetched successfully for {ticker}")

# WARNING - Warning messages (recoverable issues)
logger.warning(f"Cache miss for {ticker}, fetching from API")

# ERROR - Error messages (failure but recoverable)
logger.error(f"API rate limit exceeded for {ticker}")

# CRITICAL - Critical errors (system failure)
logger.critical("Database connection lost")
```

### Structured Logging

```python
# ✅ Good - Structured with context
logger.info(
    "Stock data fetched",
    extra={
        "ticker": ticker,
        "records": len(data),
        "source": "tiingo",
        "duration_ms": elapsed * 1000
    }
)

# ❌ Bad - Unstructured string
logger.info(f"Fetched {len(data)} records for {ticker} from tiingo in {elapsed}s")
```

## Additional Resources

- [PEP 8 - Python Style Guide](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [ruff Documentation](https://docs.astral.sh/ruff/)
- [ty Documentation](https://github.com/astral-sh/ty)
- [Type Hints (PEP 484)](https://peps.python.org/pep-0484/)

---

**Next Steps:**
- Set up pre-commit hooks for automatic formatting
- Configure IDE for ruff integration
- Enable type checking in CI/CD
- Review existing code for style compliance
