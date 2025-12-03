# Maverick API

REST API layer for MaverickMCP. Provides HTTP endpoints for web and mobile clients.

## Features

- **Multi-Strategy Authentication**: Cookie (web), JWT (mobile), API Key (programmatic)
- **Rate Limiting**: Tiered limits based on user subscription
- **Real-time Updates**: Server-Sent Events for price streaming
- **OpenAPI Documentation**: Auto-generated Swagger/ReDoc
- **Health Probes**: Kubernetes-ready liveness/readiness endpoints

## Package Structure

```
maverick_api/
├── main.py                 # FastAPI application factory
├── config.py               # Settings (pydantic-settings)
├── dependencies.py         # Dependency injection
├── auth/                   # Multi-strategy authentication
│   ├── base.py            # Auth strategy interface
│   ├── cookie.py          # HttpOnly cookie auth (web)
│   ├── jwt.py             # JWT auth with refresh rotation (mobile)
│   ├── api_key.py         # API key auth (programmatic)
│   └── middleware.py      # Auth middleware
├── middleware/
│   ├── rate_limit.py      # Tiered rate limiting
│   ├── cors.py            # CORS configuration
│   ├── logging.py         # Request logging with correlation
│   └── deprecation.py     # Deprecation headers
├── routers/
│   ├── v1/                # Version 1 API
│   │   ├── stocks.py
│   │   ├── technical.py
│   │   ├── portfolio.py
│   │   ├── screening.py
│   │   ├── backtest.py
│   │   └── sse.py         # Server-Sent Events
│   └── health.py          # Health probes
├── sse/                   # SSE implementation
│   └── manager.py         # Redis pub/sub for SSE
└── exceptions.py          # Exception handlers
```

## Quick Start

```python
from maverick_api import create_app

app = create_app()

# Run with uvicorn
# uvicorn maverick_api:app --reload
```

## API Versioning

- All endpoints under `/api/v1/*`
- Breaking changes → new version (`/api/v2/*`)
- Deprecation: 6-month notice with `Sunset` header

## Authentication

### Web App (Cookie)
```javascript
// Login sets HttpOnly cookie automatically
await fetch('/api/v1/auth/login', {
  method: 'POST',
  credentials: 'include',
  body: JSON.stringify({ email, password })
});

// CSRF token for mutations
await fetch('/api/v1/portfolio/positions', {
  method: 'POST',
  credentials: 'include',
  headers: { 'X-CSRF-Token': csrfToken }
});
```

### Mobile App (JWT)
```javascript
const { access_token, refresh_token } = await login(email, password);

// Use access token
await fetch('/api/v1/stocks/AAPL', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});

// Refresh when expired
const newTokens = await refresh(refresh_token);
```

### Programmatic (API Key)
```bash
curl -H "X-API-Key: mav_live_..." https://api.maverick.com/api/v1/stocks/AAPL
```

## Rate Limits

| Tier       | Requests/min | LLM Tokens/day |
|------------|--------------|----------------|
| Free       | 100          | 10,000         |
| Pro        | 1,000        | 100,000        |
| Enterprise | 10,000       | 1,000,000      |

## Health Endpoints

- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe
- `GET /startup` - Startup probe

