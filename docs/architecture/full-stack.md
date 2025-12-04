# Full Stack Architecture

Overview of Maverick's full-stack architecture, from the web UI to the MCP server.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                        │
├─────────────────┬─────────────────┬─────────────────┬──────────────────────┤
│   Web Browser   │   Mobile App    │  Claude Desktop │   Scripts/CI/CD      │
│   (Next.js)     │   (Future)      │   (MCP Client)  │   (API Keys)         │
└────────┬────────┴────────┬────────┴────────┬────────┴──────────┬───────────┘
         │                 │                 │                   │
         │ HTTP/SSE        │ HTTP/SSE        │ SSE (MCP)         │ HTTP
         │                 │                 │                   │
         ▼                 ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY (Future)                              │
│                         Rate Limiting, Auth, Routing                        │
└─────────────────────────────────────────────────────────────────────────────┘
                │                          │
         ┌──────┴──────┐            ┌──────┴──────┐
         ▼             ▼            ▼             ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   REST API      │  │   MCP Server    │  │   Web Server    │
│   (FastAPI)     │  │   (FastMCP)     │  │   (Next.js)     │
│   Port: 8000    │  │   Port: 8003    │  │   Port: 3000    │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ • Auth          │  │ • MCP Protocol  │  │ • SSR/SSG       │
│ • REST Endpoints│  │ • Tool Calls    │  │ • React UI      │
│ • SSE Streaming │  │ • SSE Transport │  │ • Static Assets │
│ • Rate Limiting │  │ • AI Integration│  │                 │
└────────┬────────┘  └────────┬────────┘  └─────────────────┘
         │                    │
         └─────────┬──────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SHARED SERVICES LAYER                               │
│                        (maverick-services package)                          │
├─────────────────┬─────────────────┬─────────────────┬──────────────────────┤
│  StockService   │ PortfolioService│ ScreeningService│   UserService        │
│  • Quotes       │ • Positions     │ • Maverick      │   • Auth             │
│  • History      │ • Performance   │ • Bear          │   • API Keys         │
│  • Technicals   │ • Allocation    │ • Supply/Demand │   • Sessions         │
└────────┬────────┴────────┬────────┴────────┬────────┴──────────┬───────────┘
         │                 │                 │                   │
         └─────────────────┴─────────────────┴───────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                        │
├─────────────────┬─────────────────┬─────────────────┬──────────────────────┤
│   PostgreSQL    │     Redis       │   External APIs │   File Storage       │
│   (Database)    │   (Cache)       │   (Data)        │   (S3/Local)         │
├─────────────────┼─────────────────┼─────────────────┼──────────────────────┤
│ • Users         │ • Sessions      │ • Tiingo        │ • Transcripts        │
│ • Portfolios    │ • API cache     │ • Yahoo Finance │ • Reports            │
│ • Positions     │ • Rate limits   │ • OpenAI        │ • Exports            │
│ • API Keys      │ • Price cache   │ • News APIs     │                      │
└─────────────────┴─────────────────┴─────────────────┴──────────────────────┘
```

## Service Architecture

### Frontend (Next.js)

The web application built with Next.js 14:

```
apps/web/
├── src/
│   ├── app/                 # Pages (App Router)
│   │   ├── (auth)/         # Login, Register
│   │   └── (dashboard)/    # Protected pages
│   ├── components/          # React components
│   │   ├── ui/             # Base UI components
│   │   └── portfolio/      # Feature components
│   └── lib/
│       ├── api/            # API hooks (React Query)
│       └── auth/           # Auth context
```

**Key Patterns:**

- Server Components for initial load
- Client Components for interactivity
- React Query for data fetching
- SSE for real-time updates

### REST API (FastAPI)

The REST API for web and mobile clients:

```
packages/api/
├── src/maverick_api/
│   ├── routes/
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── stocks.py       # Stock data endpoints
│   │   ├── portfolio.py    # Portfolio management
│   │   ├── screening.py    # Stock screening
│   │   └── sse.py          # Real-time streaming
│   ├── middleware/
│   │   ├── auth.py         # Auth middleware
│   │   └── rate_limit.py   # Rate limiting
│   └── dependencies.py     # Dependency injection
```

**Key Patterns:**

- Dependency injection for services
- Middleware for cross-cutting concerns
- OpenAPI documentation
- Structured error responses

### MCP Server (FastMCP)

The MCP server for AI assistant integration:

```
packages/server/
├── src/maverick_server/
│   ├── routers/
│   │   ├── technical.py    # Technical analysis tools
│   │   ├── screening.py    # Screening tools
│   │   ├── portfolio.py    # Portfolio tools
│   │   └── research.py     # Research tools
│   └── main.py             # MCP server setup
```

**Key Patterns:**

- MCP protocol over SSE
- Tool definitions with schemas
- Resource providers
- Prompt templates

### Shared Services

Business logic shared between API and MCP:

```
packages/services/
├── src/maverick_services/
│   ├── stock_service.py
│   ├── portfolio_service.py
│   ├── screening_service.py
│   ├── user_service.py
│   └── api_key_service.py
```

**Key Patterns:**

- Repository pattern for data access
- Service layer for business logic
- Dependency injection
- Async/await for I/O

## Data Flow

### User Authentication

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│   API    │────▶│  Service │────▶│  Redis   │
│ (Login)  │     │ (Auth)   │     │ (User)   │     │(Sessions)│
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │
     │  credentials   │  validate      │  create        │
     │ ─────────────▶ │ ─────────────▶ │  session       │
     │                │                │ ─────────────▶ │
     │                │                │                │
     │  JWT/Cookie    │  token/session │  session_id    │
     │ ◀───────────── │ ◀───────────── │ ◀───────────── │
```

### Stock Quote Request

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│   API    │────▶│  Service │────▶│  Cache   │
│ (Quote)  │     │ (Stocks) │     │ (Stock)  │     │ (Redis)  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │
     │  GET /quote    │  get_quote()   │  check cache   │
     │ ─────────────▶ │ ─────────────▶ │ ─────────────▶ │
     │                │                │                │
     │                │                │   cache miss   │
     │                │                │ ◀───────────── │
     │                │                │                │
     │                │                ▼                │
     │                │         ┌──────────┐           │
     │                │         │  Tiingo  │           │
     │                │         │   API    │           │
     │                │         └──────────┘           │
     │                │                │                │
     │                │                │  fetch price   │
     │                │         ◀──────┘                │
     │                │                │                │
     │                │                │  update cache  │
     │                │                │ ─────────────▶ │
     │                │                │                │
     │   response     │   quote data   │                │
     │ ◀───────────── │ ◀───────────── │                │
```

### Real-time Price Stream (SSE)

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│   API    │────▶│  Redis   │
│  (SSE)   │     │  (SSE)   │     │ (PubSub) │
└──────────┘     └──────────┘     └──────────┘
     │                │                │
     │  subscribe     │  subscribe     │
     │ ─────────────▶ │ ─────────────▶ │
     │                │                │
     │     ...        │     ...        │  price update
     │                │ ◀───────────── │
     │   event        │                │
     │ ◀───────────── │                │
     │                │                │
     │     ...        │  heartbeat     │
     │ ◀───────────── │  (15s)         │
```

## Package Dependencies

```
                    ┌─────────────────┐
                    │ maverick-schemas│
                    │  (Pydantic)     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │maverick-core│  │maverick-data│  │maverick-    │
     │ (Config,    │  │ (Providers, │  │ services    │
     │  Logging)   │  │  Models)    │  │ (Business)  │
     └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
            │                │                │
            └────────────────┼────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │maverick-api │  │maverick-    │  │maverick-    │
     │ (REST API)  │  │ server      │  │ backtest    │
     │             │  │ (MCP)       │  │ (Backtesting)│
     └─────────────┘  └─────────────┘  └─────────────┘
```

## Technology Stack

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Runtime | Python 3.12 | Core language |
| API Framework | FastAPI | REST API |
| MCP Framework | FastMCP | MCP Server |
| ORM | SQLAlchemy 2.0 | Database access |
| Validation | Pydantic v2 | Data validation |
| Task Queue | (AsyncIO) | Background tasks |
| Password Hash | Argon2id | Password security |

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Next.js 14 | React framework |
| Styling | TailwindCSS | Utility CSS |
| Components | shadcn/ui | UI primitives |
| Data Fetching | React Query | Server state |
| Forms | React Hook Form | Form handling |
| Validation | Zod | Schema validation |
| Charts | Recharts | Visualizations |

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| Database | PostgreSQL 15 | Primary storage |
| Cache | Redis 7 | Caching, sessions |
| Containerization | Docker | Deployment |
| Reverse Proxy | (nginx) | Production |

## Security Architecture

### Authentication Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                     AUTHENTICATION STRATEGIES                       │
├────────────────────┬────────────────────┬─────────────────────────┤
│   Cookie (Web)     │   JWT (Mobile)     │   API Key (Scripts)     │
├────────────────────┼────────────────────┼─────────────────────────┤
│ • HttpOnly cookie  │ • Access token     │ • Hashed in DB          │
│ • CSRF protection  │   (15 min)         │ • Prefix visible        │
│ • SameSite=Lax    │ • Refresh token    │ • Expiration dates      │
│ • 7-day sessions   │   (7 days)         │ • Usage tracking        │
│                    │ • Token rotation   │                         │
└────────────────────┴────────────────────┴─────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   Auth Middleware   │
                    │   • Validates auth  │
                    │   • Sets user ctx   │
                    │   • Rate limit check│
                    └─────────────────────┘
```

### Rate Limiting

```
Tier-based limits:
├── Free:    60/min,   1,000/day
├── Basic:  120/min,  10,000/day
└── Pro:    600/min, 100,000/day

Endpoint-specific:
├── /auth/*:        10/min (prevent brute force)
├── /screening/*:   20/min (expensive queries)
└── /stocks/*:     120/min (standard)
```

## Deployment Architecture

### Docker Compose (Development/Small Scale)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Docker Compose                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │   web    │  │   api    │  │   mcp    │                      │
│  │  :3000   │  │  :8000   │  │  :8003   │                      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                      │
│       │             │             │                             │
│       └─────────────┼─────────────┘                             │
│                     │                                            │
│       ┌─────────────┼─────────────┐                             │
│       │             │             │                             │
│  ┌────┴────┐   ┌────┴────┐       │                             │
│  │postgres │   │  redis  │       │                             │
│  │  :5432  │   │  :6379  │       │                             │
│  └─────────┘   └─────────┘       │                             │
│                                   │                             │
│                     maverick-network                            │
└─────────────────────────────────────────────────────────────────┘
```

## Related Documentation

- [ADR-002: Authentication Strategy](adr/002-authentication-strategy.md)
- [ADR-003: Shared Services Architecture](adr/003-shared-services-architecture.md)
- [ADR-005: SSE vs WebSocket](adr/005-sse-vs-websocket.md)
- [ADR-006: API/MCP Separation](adr/006-api-mcp-separation.md)
- [Docker Deployment Guide](../deployment/docker.md)

