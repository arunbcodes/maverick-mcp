# ADR-006: Separation of REST API and MCP Server

## Status

**Accepted** - December 2024

## Context

As Maverick evolves from a pure MCP server to a full-stack financial platform, we need to decide how to structure the backend services:

1. **Single Server**: One process serving both REST API and MCP protocol
2. **Separate Services**: Distinct REST API and MCP server processes
3. **Hybrid**: Single codebase with multiple entry points

### Requirements

- Web and mobile clients need REST API with HTTP standards
- Claude Desktop and Cursor need MCP protocol over SSE
- Both need access to the same business logic
- Development velocity should not be impacted
- Deployment should remain simple for self-hosting

### Constraints

- MCP protocol has specific requirements (JSON-RPC over SSE)
- REST API needs standard HTTP patterns (status codes, headers)
- Both need authentication, but different strategies
- Rate limiting differs between interactive and AI usage

## Decision

**We will use separate services with a shared services layer.**

```
┌─────────────────┐    ┌─────────────────┐
│   REST API      │    │   MCP Server    │
│   (FastAPI)     │    │   (FastMCP)     │
│   Port: 8000    │    │   Port: 8003    │
└────────┬────────┘    └────────┬────────┘
         │                      │
         └──────────┬───────────┘
                    │
         ┌──────────┴──────────┐
         │   Shared Services   │
         │   (maverick-services)│
         │   • StockService    │
         │   • PortfolioService│
         │   • UserService     │
         └──────────┬──────────┘
                    │
         ┌──────────┴──────────┐
         │   Data Layer        │
         │   • PostgreSQL      │
         │   • Redis           │
         └─────────────────────┘
```

## Rationale

### Why Not Single Server?

1. **Protocol Conflicts**: MCP uses JSON-RPC 2.0 with specific response formats. REST API uses standard HTTP status codes and response envelopes. Mixing these in one process creates complexity.

2. **Framework Mismatch**: FastAPI and FastMCP have different paradigms. FastAPI routes return responses; FastMCP tools return results. Combining them would require significant abstraction.

3. **Scaling Independence**: MCP server handles long-lived SSE connections from AI assistants. REST API handles burst traffic from web/mobile. Different scaling characteristics.

4. **Authentication Complexity**: Web uses cookies, mobile uses JWT, MCP clients use... different patterns. Separating allows cleaner auth implementation.

### Why Separate Services?

1. **Clean Boundaries**: Each service handles one protocol well
2. **Independent Deployment**: Can update API without affecting MCP
3. **Technology Freedom**: Can use best tools for each use case
4. **Debugging**: Easier to isolate issues to one service

### Why Shared Services Layer?

1. **DRY Principle**: Business logic written once
2. **Consistency**: Same calculations in API and MCP
3. **Testability**: Services can be tested independently
4. **Maintenance**: Changes in one place affect both interfaces

## Implementation

### Package Structure

```
packages/
├── services/              # Shared business logic
│   ├── stock_service.py
│   ├── portfolio_service.py
│   └── user_service.py
├── api/                   # REST API
│   ├── routes/
│   └── middleware/
└── server/                # MCP Server
    └── routers/
```

### Service Layer Pattern

```python
# packages/services/stock_service.py
class StockService:
    def __init__(self, cache: Redis, db: AsyncSession):
        self.cache = cache
        self.db = db

    async def get_quote(self, ticker: str) -> StockQuote:
        # Check cache
        cached = await self.cache.get(f"quote:{ticker}")
        if cached:
            return StockQuote.parse_raw(cached)

        # Fetch from provider
        quote = await self._fetch_from_tiingo(ticker)

        # Cache and return
        await self.cache.set(f"quote:{ticker}", quote.json(), ex=60)
        return quote
```

### REST API Usage

```python
# packages/api/routes/stocks.py
@router.get("/stocks/{ticker}/quote")
async def get_quote(
    ticker: str,
    stock_service: StockService = Depends(get_stock_service)
):
    quote = await stock_service.get_quote(ticker)
    return {"data": quote}
```

### MCP Server Usage

```python
# packages/server/routers/technical.py
@mcp.tool()
async def get_stock_quote(ticker: str) -> dict:
    """Get current stock quote."""
    service = StockService(cache, db)
    quote = await service.get_quote(ticker)
    return quote.dict()
```

### Docker Deployment

```yaml
# docker-compose.yml
services:
  api:
    build:
      dockerfile: docker/api.Dockerfile
    ports:
      - "8000:8000"

  mcp:
    build:
      dockerfile: docker/mcp.Dockerfile
    ports:
      - "8003:8000"

  # Shared infrastructure
  postgres:
    image: postgres:15-alpine
  redis:
    image: redis:7-alpine
```

## Consequences

### Positive

- ✅ Clean protocol separation
- ✅ Independent scaling and deployment
- ✅ Shared business logic (DRY)
- ✅ Easier debugging and monitoring
- ✅ Technology flexibility per service

### Negative

- ❌ Two processes to manage (mitigated by Docker Compose)
- ❌ Slight increase in infrastructure complexity
- ❌ Need to ensure service layer consistency
- ❌ Potential for code drift between API and MCP implementations

### Mitigation

1. **Docker Compose**: Single command starts everything
2. **Shared Tests**: Service layer has comprehensive tests
3. **CI Pipeline**: Tests both API and MCP against services
4. **Code Reviews**: Ensure changes use service layer

## Alternatives Considered

### Alternative 1: Single Process with Multiple Handlers

Mount both FastAPI and FastMCP in one process:

```python
app = FastAPI()
mcp = FastMCP()

# FastAPI routes
app.include_router(api_router)

# MCP mounted at /mcp
app.mount("/mcp", mcp.sse_app())
```

**Rejected because:**
- Protocol conflicts in responses
- Complex error handling
- Harder to scale independently

### Alternative 2: Gateway Pattern

Single API gateway routing to internal services:

```
Client → Gateway → API Service
                 → MCP Service
```

**Deferred because:**
- Adds complexity for self-hosting
- May be appropriate at larger scale
- Can be added later without major refactoring

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [ADR-003: Shared Services Architecture](003-shared-services-architecture.md)

