# Maverick Schemas

Shared Pydantic models for MaverickMCP. This is a **dependency-light leaf package** that other packages import from.

## Design Principles

1. **No internal dependencies** - This package does NOT depend on any other maverick-* packages
2. **Pure Pydantic** - Only Pydantic as a dependency for maximum portability
3. **Shared models** - Used by both MCP server and REST API for consistency

## Package Structure

```
maverick_schemas/
├── base.py          # Base models, response envelopes, common types
├── stock.py         # Stock, Quote, OHLCV models
├── technical.py     # Technical indicators (RSI, MACD, etc.)
├── portfolio.py     # Position, Portfolio, P&L models
├── screening.py     # Screening results and filters
├── backtest.py      # Strategy and backtest result models
├── research.py      # Research and sentiment models
├── auth.py          # Authentication models
└── responses.py     # API response envelopes
```

## Usage

```python
from maverick_schemas import StockQuote, APIResponse, PaginatedResponse
from maverick_schemas.stock import OHLCV, StockHistory
from maverick_schemas.responses import ErrorResponse
```

## Dependency Graph

```
                    ┌─────────────────┐
                    │ maverick-schemas│  ← This package (leaf node)
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │   core   │   │   data   │   │ services │
        └──────────┘   └──────────┘   └──────────┘
```

