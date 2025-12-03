# Maverick Services

Shared domain services for MaverickMCP. This package provides the business logic layer used by both the MCP server and REST API.

## Design Principles

1. **Single Source of Truth** - All business logic lives here, not duplicated in routers
2. **Protocol-Agnostic** - Services don't know if they're called from MCP or REST
3. **Dependency Injection** - All dependencies (providers, DB sessions) are injected
4. **Schema-First** - Input and output use models from `maverick-schemas`

## Package Structure

```
maverick_services/
├── __init__.py
├── stock_service.py       # Stock data and quotes
├── technical_service.py   # Technical analysis
├── portfolio_service.py   # Portfolio management
├── screening_service.py   # Stock screening
├── backtest_service.py    # Backtesting
├── research_service.py    # AI-powered research
└── exceptions.py          # Service-specific exceptions
```

## Usage

### In MCP Routers

```python
from maverick_services import StockService

service = StockService(provider=provider)

@mcp.tool()
async def get_stock_data(ticker: str):
    history = await service.get_history(ticker)
    return history.model_dump()
```

### In REST API Routers

```python
from fastapi import APIRouter, Depends
from maverick_services import StockService
from maverick_api.dependencies import get_stock_service

router = APIRouter()

@router.get("/stocks/{ticker}/history")
async def get_history(
    ticker: str,
    service: StockService = Depends(get_stock_service),
):
    return await service.get_history(ticker)
```

## Dependency Graph

```
┌─────────────────┐
│ maverick-schemas│
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│  core  │ │  data  │
└────┬───┘ └────┬───┘
     │          │
     └────┬─────┘
          │
          ▼
   ┌──────────────┐
   │   services   │  ← This package
   └──────────────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
┌────────┐  ┌────────┐
│ server │  │  api   │
│ (MCP)  │  │ (REST) │
└────────┘  └────────┘
```

