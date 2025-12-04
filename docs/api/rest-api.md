# REST API Overview

Maverick provides a comprehensive REST API for programmatic access to all features.

## Base URL

```
http://localhost:8000/api/v1
```

## Interactive Documentation

When the API server is running, interactive documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Authentication

The API supports three authentication methods:

| Method | Use Case | Header/Cookie |
|--------|----------|---------------|
| **JWT Bearer** | Mobile apps, SPAs | `Authorization: Bearer <token>` |
| **Cookie** | Web browser sessions | `session` cookie (HttpOnly) |
| **API Key** | Programmatic access | `X-API-Key: <key>` |

See [Authentication](authentication.md) for details.

## Endpoints

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/health/ready` | Readiness probe |
| GET | `/health/startup` | Startup probe |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create new account |
| POST | `/auth/login` | Login (returns JWT or sets cookie) |
| POST | `/auth/logout` | Logout (invalidates session) |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user info |
| PUT | `/auth/password` | Change password |

### API Keys

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api-keys` | List user's API keys |
| POST | `/api-keys` | Create new API key |
| DELETE | `/api-keys/{key_id}` | Revoke API key |

### Stocks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stocks/{ticker}/quote` | Get current quote |
| GET | `/stocks/{ticker}/info` | Get company info |
| GET | `/stocks/{ticker}/history` | Get price history |
| POST | `/stocks/batch/quotes` | Get multiple quotes |

### Technical Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stocks/{ticker}/technicals` | Get technical indicators |
| GET | `/stocks/{ticker}/rsi` | Get RSI analysis |
| GET | `/stocks/{ticker}/macd` | Get MACD analysis |
| GET | `/stocks/{ticker}/support-resistance` | Get S/R levels |

### Portfolio

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/portfolio` | Get portfolio summary |
| GET | `/portfolio/positions` | List all positions |
| POST | `/portfolio/positions` | Add position |
| PUT | `/portfolio/positions/{id}` | Update position |
| DELETE | `/portfolio/positions/{id}` | Remove position |
| GET | `/portfolio/performance` | Get performance metrics |

### Screening

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/screening/maverick` | Get Maverick bullish stocks |
| GET | `/screening/maverick-bear` | Get Maverick bearish stocks |
| GET | `/screening/supply-demand` | Get supply/demand breakouts |
| GET | `/screening/all` | Get all screening results |

### Real-time Data (SSE)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sse/prices?tickers=AAPL,MSFT` | Subscribe to price updates |
| GET | `/sse/portfolio` | Subscribe to portfolio updates |

See [SSE Streaming](sse-streaming.md) for details.

## Request/Response Format

### Request Headers

```http
Content-Type: application/json
Authorization: Bearer <jwt_token>
```

Or for API key authentication:

```http
Content-Type: application/json
X-API-Key: mav_xxxxxxxxxxxx
```

### Response Format

**Success Response:**

```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

**Error Response:**

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid ticker symbol",
    "details": {
      "field": "ticker",
      "value": "INVALID"
    }
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing/invalid auth) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |

## Rate Limiting

API requests are rate limited per user:

| Tier | Requests/minute | Requests/day |
|------|-----------------|--------------|
| Free | 60 | 1,000 |
| Basic | 120 | 10,000 |
| Pro | 600 | 100,000 |

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705318200
```

## Examples

### Get Stock Quote

```bash
curl -X GET "http://localhost:8000/api/v1/stocks/AAPL/quote" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "data": {
    "ticker": "AAPL",
    "price": 185.92,
    "change": 2.34,
    "change_percent": 1.27,
    "volume": 45678900,
    "timestamp": "2024-01-15T16:00:00Z"
  }
}
```

### Add Portfolio Position

```bash
curl -X POST "http://localhost:8000/api/v1/portfolio/positions" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "shares": 10,
    "purchase_price": 150.00,
    "purchase_date": "2024-01-01"
  }'
```

### Get Screening Results

```bash
curl -X GET "http://localhost:8000/api/v1/screening/maverick?limit=20" \
  -H "X-API-Key: mav_xxxxxxxxxxxx"
```

## SDKs & Code Generation

### TypeScript/JavaScript

Generate a typed client from OpenAPI:

```bash
# Using openapi-typescript-codegen
npx openapi-typescript-codegen \
  --input http://localhost:8000/openapi.json \
  --output ./src/api-client \
  --client fetch
```

### Python

```bash
# Using openapi-python-client
pip install openapi-python-client
openapi-python-client generate \
  --url http://localhost:8000/openapi.json
```

## Versioning

The API uses URL-based versioning:

- Current: `/api/v1/...`
- Future: `/api/v2/...`

See [ADR-001: API Versioning](../architecture/adr/001-api-versioning.md) for the versioning strategy.

## Next Steps

- [Authentication Guide](authentication.md) - Detailed auth docs
- [SSE Streaming](sse-streaming.md) - Real-time data feeds
- [Backtesting API](backtesting.md) - Strategy backtesting endpoints

