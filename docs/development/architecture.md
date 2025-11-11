# Architecture

Maverick MCP system architecture and design patterns.

## Overview

Maverick MCP is built using modern Python architecture principles with a focus on:

- **Domain-Driven Design (DDD)** for business logic organization
- **Clean Architecture** for separation of concerns
- **SOLID Principles** for maintainable code
- **FastMCP 2.0** for Model Context Protocol integration
- **Multi-tier Caching** for performance
- **Microservice-Ready** design for scalability

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  MCP Clients (Claude Desktop, Cursor, Claude Code CLI)     │
└──────────────────────┬──────────────────────────────────────┘
                       │ MCP Protocol (SSE/HTTP/STDIO)
┌──────────────────────┴──────────────────────────────────────┐
│  FastMCP Server (maverick_mcp/api/server.py)               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • Routers (stock, technical, portfolio, research, concall) │
│  • Tool Registry (40+ MCP tools)                            │
│  • Request/Response handling                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│  Services Layer                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • ScreeningService • MarketCalendarService                 │
│  • PortfolioService • TechnicalAnalysisService              │
│  • ResearchService  • ConcallService                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│  Domain Layer (Business Logic)                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • core/ - Technical analysis calculations                  │
│  • domain/ - Financial entities and value objects           │
│  • backtesting/ - Strategy testing engine                   │
│  • concall/ - Conference call analysis                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│  Data & Infrastructure Layer                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • data/ - ORM models, caching, sessions                    │
│  • providers/ - External APIs (Tiingo, OpenRouter, FRED)   │
│  • infrastructure/ - Database, Redis, external services     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│  External Services                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • PostgreSQL/SQLite (data storage)                         │
│  • Redis (caching)                                          │
│  • Tiingo API (stock data)                                  │
│  • OpenRouter (AI models)                                   │
│  • FRED API (economic data)                                 │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
maverick_mcp/
├── api/                    # FastMCP server and routers
│   ├── server.py          # Main MCP server
│   ├── routers/           # Domain-specific tool routers
│   │   ├── stock_router.py
│   │   ├── technical_router.py
│   │   ├── portfolio_router.py
│   │   ├── research_router.py
│   │   └── concall_router.py
│   └── services/          # API-level services
│
├── domain/                # Business logic (DDD)
│   ├── stock_analysis/    # Stock analysis domain
│   ├── screening/         # Screening strategies
│   └── services/          # Domain services
│
├── core/                  # Core financial calculations
│   ├── technical_analysis.py  # Indicators (RSI, MACD, etc.)
│   └── visualization.py       # Chart generation
│
├── backtesting/          # Strategy testing
│   ├── engine/           # VectorBT integration
│   ├── strategies/       # 15+ built-in strategies
│   └── optimization/     # Parameter optimization
│
├── concall/              # Conference call analysis
│   ├── models.py         # Database models
│   ├── providers/        # Transcript fetchers
│   ├── services/         # Analysis services
│   ├── cache/            # Multi-tier caching
│   └── utils/            # Utilities
│
├── data/                 # Data access layer
│   ├── models.py         # SQLAlchemy models
│   ├── cache.py          # CacheManager
│   ├── session_management.py
│   └── validation.py
│
├── providers/            # External API integrations
│   ├── stock_data.py     # Tiingo provider
│   ├── openrouter_provider.py
│   ├── indian_market_data.py
│   └── macro_data.py
│
├── infrastructure/       # Infrastructure concerns
│   ├── caching/
│   ├── data_fetching/
│   └── database/
│
├── config/              # Configuration
│   └── settings.py      # Environment settings
│
├── services/            # Application services
│   ├── screening_service.py
│   └── market_calendar_service.py
│
└── utils/              # Shared utilities
    └── circuit_breaker_services.py
```

## Design Patterns

### 1. Repository Pattern
**Location**: `data/` layer
**Purpose**: Abstract data access

```python
# Example
class StockRepository:
    def get_by_ticker(self, ticker: str) -> Stock:
        ...
    def get_screening_scores(self, strategy: str) -> list[ScreeningScore]:
        ...
```

### 2. Service Pattern
**Location**: `services/`, `domain/services/`
**Purpose**: Encapsulate business logic

```python
# Example
class ScreeningService:
    def get_maverick_bullish(self, limit: int) -> list[dict]:
        ...
```

### 3. Provider Pattern
**Location**: `providers/`
**Purpose**: Abstract external APIs

```python
# Example
class StockDataProvider:
    def get_historical_data(self, ticker: str) -> pd.DataFrame:
        ...
```

### 4. Strategy Pattern
**Location**: `backtesting/strategies/`
**Purpose**: Pluggable trading strategies

```python
# Example
class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        ...
```

### 5. Cache-Aside Pattern
**Location**: `data/cache.py`, `concall/cache/`
**Purpose**: Performance optimization

```python
# Example
def get_stock_data(ticker: str):
    cached = cache.get(f"stock:{ticker}")
    if cached:
        return cached
    data = fetch_from_api(ticker)
    cache.set(f"stock:{ticker}", data, ttl=3600)
    return data
```

### 6. Multi-Agent Pattern
**Location**: `agents/`, research tools
**Purpose**: Parallel AI processing

```python
# Example
agents = [
    FinancialAgent(),
    NewsAgent(),
    SentimentAgent(),
    CompetitorAgent()
]
results = await asyncio.gather(*[agent.research(ticker) for agent in agents])
```

## Key Architectural Decisions

### FastMCP 2.0 for MCP Protocol
**Why**: Official MCP framework with SSE/HTTP/STDIO support
**Benefits**: Multiple transport protocols, automatic tool registration, type safety

### SQLAlchemy ORM
**Why**: Database abstraction with multi-DB support
**Benefits**: SQLite for development, PostgreSQL for production, type-safe queries

### Multi-Tier Caching
**Why**: Performance and cost optimization
**Architecture**:
- L1: Redis/Memory (1-5ms)
- L2: Database (10-50ms)
- L3: External APIs (1000-60000ms)

### OpenRouter for AI
**Why**: Access to 400+ models with cost optimization
**Benefits**: Automatic model selection, 40-60% cost savings, smart fallbacks

### VectorBT for Backtesting
**Why**: Vectorized performance, production-ready
**Benefits**: 100-1000x faster than sequential, extensive strategy library

## Data Flow Examples

### Stock Data Request
```
User → Claude Desktop
  ↓ MCP Protocol
FastMCP Server → get_stock_data tool
  ↓
StockDataProvider
  ↓ Check cache
CacheManager (Redis/Database)
  ↓ Cache miss
Tiingo API
  ↓ Response
Cache → Store (TTL: 1 hour)
  ↓
Return to user
```

### AI Research Request
```
User → Claude Desktop
  ↓ MCP Protocol
FastMCP Server → research_comprehensive tool
  ↓
ResearchService → Spawn 6 parallel agents
  ↓
OpenRouterProvider → Select optimal models
  ↓ Parallel execution
[Agent1, Agent2, Agent3, Agent4, Agent5, Agent6]
  ↓ Each gathers data
[Stock API, News API, Financial API, ...]
  ↓ Synthesize results
Supervisor Agent → Aggregate insights
  ↓ Cache results
ConcallCacheService (Redis + Database)
  ↓
Return comprehensive analysis
```

## Performance Optimizations

### Vectorization
All technical analysis uses pandas/numpy vectorized operations:
```python
# Vectorized RSI calculation
delta = data['Close'].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.rolling(period).mean()
avg_loss = loss.rolling(period).mean()
rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))
```

### Parallel Processing
- Multi-agent research: 6 concurrent agents
- Backtesting: Parallel strategy evaluation
- Portfolio optimization: Parallel scenarios

### Intelligent Caching
- Time-based TTL (1 hour for stock data)
- Event-based invalidation
- Pre-seeded database (520 S&P 500 stocks)

### Database Optimization
- Composite indexes on (ticker, date)
- Connection pooling
- Batch operations

## Security Considerations

### API Key Management
- Environment variables only
- Never committed to git
- Secrets rotation support

### Input Validation
- Ticker format validation
- Date range validation
- Parameter bounds checking

### Non-Root Execution
- Docker runs as user 1000
- No elevated privileges

### Rate Limiting
- Respect API limits
- Circuit breakers for failures
- Exponential backoff

## Scalability

### Current Capacity
- Single instance: 100+ requests/second
- Database: 1M+ stocks
- Cache: 10GB+ Redis

### Horizontal Scaling
- Stateless design (can run multiple instances)
- Shared PostgreSQL
- Shared Redis cluster
- Load balancer ready

### Future Enhancements
- Kubernetes deployment
- Service mesh (Istio)
- Message queue (RabbitMQ/Kafka)
- Microservices split

## Testing Strategy

- **Unit Tests**: 90%+ coverage target
- **Integration Tests**: Database, Redis, APIs
- **End-to-End Tests**: Full MCP tool workflows
- **Performance Tests**: Latency, throughput
- **Load Tests**: Concurrent users

See [Testing Guide](testing.md) for details.

## Monitoring & Observability

### Logging
- Structured logging (JSON)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation IDs for tracing

### Metrics (Future)
- Request latency
- Cache hit rates
- API call counts
- Error rates

### Health Checks
- Database connectivity
- Redis availability
- API endpoint health

## Additional Resources

- [API Reference](../api-reference/core.md)
- [Contributing Guide](contributing.md)
- [Testing Guide](testing.md)
- [Code Style Guide](code-style.md)
