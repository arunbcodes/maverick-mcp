# Maverick Core

Core domain logic and interfaces for the Maverick stock analysis platform.

## Overview

`maverick-core` is the foundation package that contains:

- **Domain Entities**: Pure business logic following DDD principles
- **Interface Definitions**: Protocol-based contracts for all services
- **Technical Analysis**: Pure functions for calculating indicators
- **Exception Hierarchy**: Common exception types for all packages

## Installation

```bash
pip install maverick-core
```

Or with uv:

```bash
uv add maverick-core
```

## Key Features

### Zero Framework Dependencies

This package has minimal external dependencies:
- `numpy` - Numerical computations
- `pandas` - Data manipulation
- `pandas-ta` - Technical indicators
- `pydantic` - Data validation

No SQLAlchemy, Redis, LangChain, or other framework dependencies.

### Domain Entities

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

# Calculate metrics
metrics = portfolio.calculate_portfolio_metrics({
    "AAPL": Decimal("175.00")
})
print(f"Total P&L: ${metrics['total_pnl']:.2f}")
```

### Interface Contracts

```python
from maverick_core.interfaces import IStockDataFetcher, IStockScreener

# Implement in your own package
class MyDataProvider(IStockDataFetcher):
    async def get_stock_data(self, symbol: str, ...) -> pd.DataFrame:
        # Your implementation
        ...
```

### Exceptions

```python
from maverick_core.exceptions import (
    MaverickError,
    StockDataError,
    ValidationError,
)

try:
    # Your code
    pass
except StockDataError as e:
    print(f"Data error: {e.message}")
except MaverickError as e:
    print(f"General error: {e}")
```

## Package Structure

```
maverick_core/
├── domain/
│   ├── portfolio.py      # Portfolio & Position entities
│   ├── entities/         # Other domain entities
│   ├── value_objects/    # Immutable value objects
│   └── services/         # Domain services
├── interfaces/
│   ├── stock_data.py     # IStockDataFetcher, IStockScreener
│   ├── cache.py          # ICacheProvider
│   ├── persistence.py    # IRepository, IStockRepository
│   ├── technical.py      # ITechnicalAnalyzer
│   ├── llm.py            # ILLMProvider, IResearchAgent
│   └── backtest.py       # IBacktestEngine, IStrategy
├── technical/            # Pure technical analysis functions
└── exceptions/           # Exception hierarchy
```

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Type check
uv run mypy src/

# Lint
uv run ruff check src/
```

## License

MIT
