# ADR-003: Shared Services Architecture

## Status

Accepted

## Date

2024-12-02

## Context

We have two interfaces to our stock analysis system:
1. **MCP Server**: For Claude Desktop integration
2. **REST API**: For web and mobile applications

Both need access to the same business logic (stock data, technical analysis, portfolio management).

## Decision

We will create a **shared services layer** (`maverick-services`) that both MCP and REST API use.

### Package Structure

```
                    ┌─────────────────┐
                    │ maverick-schemas│  ← Shared Pydantic models
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │   core   │   │   data   │   │ services │
        └──────────┘   └──────────┘   └────┬─────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              │                            │                            │
              ▼                            ▼                            ▼
        ┌──────────┐                ┌──────────┐                 ┌──────────┐
        │  server  │                │   api    │                 │ backtest │
        │  (MCP)   │                │ (REST)   │                 │          │
        └──────────┘                └──────────┘                 └──────────┘
```

### Service Layer Design

```python
# packages/services/src/maverick_services/stock_service.py
class StockService:
    """Protocol-agnostic service - doesn't know if MCP or REST."""
    
    def __init__(self, provider: StockDataProvider, cache: CacheProvider):
        self._provider = provider
        self._cache = cache
    
    async def get_quote(self, ticker: str) -> StockQuote:
        # Business logic here
        pass
```

### Usage in MCP Router

```python
# packages/server/src/maverick_server/routers/data.py
from maverick_services import StockService

@mcp.tool()
async def get_stock_data(ticker: str):
    service = StockService(provider=YFinanceProvider())
    return (await service.get_quote(ticker)).model_dump()
```

### Usage in REST Router

```python
# packages/api/src/maverick_api/routers/v1/stocks.py
from maverick_services import StockService
from maverick_api.dependencies import get_stock_service

@router.get("/{ticker}/quote")
async def get_quote(ticker: str, service = Depends(get_stock_service)):
    return await service.get_quote(ticker)
```

## Consequences

### Positive
- **Single source of truth**: Business logic in one place
- **DRY**: No duplication between MCP and REST
- **Testable**: Services can be unit tested in isolation
- **Consistent**: Same behavior regardless of interface

### Negative
- **Indirection**: Extra layer between routers and data
- **Dependency management**: Services depend on core + data

## Dependency Rules

1. **maverick-schemas**: No internal dependencies (leaf package)
2. **maverick-core**: Only maverick-schemas
3. **maverick-data**: maverick-core, maverick-schemas
4. **maverick-services**: maverick-core, maverick-data, maverick-schemas
5. **maverick-api/server**: maverick-services + above

## Alternatives Considered

1. **Duplicate logic in each interface**
   - Rejected: Leads to inconsistencies, maintenance burden

2. **Direct data access in routers**
   - Rejected: Mixes concerns, harder to test

3. **Single monolithic package**
   - Rejected: Harder to maintain, no clear boundaries

## References

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)

