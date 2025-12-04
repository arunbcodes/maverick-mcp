# SSE Streaming

Maverick uses Server-Sent Events (SSE) for real-time data streaming. SSE provides a simple, efficient way to push updates from the server to clients.

## Why SSE?

| Feature | SSE | WebSocket |
|---------|-----|-----------|
| Direction | Server → Client | Bidirectional |
| Protocol | HTTP | Custom |
| Reconnection | Automatic | Manual |
| Mobile Battery | Better | Higher drain |
| Firewall | Friendly | May be blocked |
| Complexity | Simple | Complex |

For real-time price updates and notifications, SSE is the better choice. See [ADR-005: SSE vs WebSocket](../architecture/adr/005-sse-vs-websocket.md).

## Endpoints

### Price Stream

Subscribe to real-time price updates for multiple tickers:

```
GET /api/v1/sse/prices?tickers=AAPL,MSFT,GOOGL
```

**Headers:**

```http
Accept: text/event-stream
Authorization: Bearer <token>
```

**Events:**

```
event: price
data: {"ticker":"AAPL","price":185.92,"change":2.34,"timestamp":"2024-01-15T16:00:00Z"}

event: price
data: {"ticker":"MSFT","price":402.15,"change":1.23,"timestamp":"2024-01-15T16:00:01Z"}

event: heartbeat
data: {"timestamp":"2024-01-15T16:00:05Z"}
```

### Portfolio Stream

Subscribe to portfolio value updates:

```
GET /api/v1/sse/portfolio
```

**Events:**

```
event: portfolio_update
data: {"total_value":125000.50,"daily_change":1250.00,"daily_change_percent":1.01}

event: position_update
data: {"ticker":"AAPL","shares":10,"current_value":1859.20,"unrealized_pnl":109.20}
```

## Event Types

| Event | Description |
|-------|-------------|
| `price` | Real-time price update for a ticker |
| `portfolio_update` | Portfolio-wide value changes |
| `position_update` | Individual position changes |
| `heartbeat` | Keep-alive signal (every 15s) |
| `error` | Error notification |
| `connected` | Connection established |

## Client Implementation

### JavaScript (Browser)

```javascript
const eventSource = new EventSource(
  'http://localhost:8000/api/v1/sse/prices?tickers=AAPL,MSFT',
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);

// Note: EventSource doesn't support custom headers natively
// Use fetch with ReadableStream or a library like eventsource

eventSource.addEventListener('price', (event) => {
  const data = JSON.parse(event.data);
  console.log(`${data.ticker}: $${data.price}`);
});

eventSource.addEventListener('heartbeat', (event) => {
  console.log('Connection alive');
});

eventSource.onerror = (error) => {
  console.error('SSE Error:', error);
  // EventSource automatically reconnects
};

// Clean up
eventSource.close();
```

### React Hook

```typescript
import { useEffect, useState, useCallback } from 'react';

interface PriceUpdate {
  ticker: string;
  price: number;
  change: number;
  timestamp: string;
}

export function usePriceStream(tickers: string[]) {
  const [prices, setPrices] = useState<Record<string, PriceUpdate>>({});
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (tickers.length === 0) return;

    const url = `/api/v1/sse/prices?tickers=${tickers.join(',')}`;
    const eventSource = new EventSource(url);

    eventSource.addEventListener('connected', () => {
      setConnected(true);
      setError(null);
    });

    eventSource.addEventListener('price', (event) => {
      const data: PriceUpdate = JSON.parse(event.data);
      setPrices(prev => ({
        ...prev,
        [data.ticker]: data
      }));
    });

    eventSource.onerror = () => {
      setConnected(false);
      setError(new Error('Connection lost'));
    };

    return () => {
      eventSource.close();
    };
  }, [tickers.join(',')]);

  return { prices, connected, error };
}
```

### Python

```python
import httpx
import json

async def stream_prices(tickers: list[str], token: str):
    url = f"http://localhost:8000/api/v1/sse/prices"
    params = {"tickers": ",".join(tickers)}
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "text/event-stream"
    }

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "GET", url, params=params, headers=headers
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    print(f"Price update: {data}")
                elif line.startswith("event:"):
                    event_type = line[6:].strip()
                    print(f"Event: {event_type}")
```

### cURL

```bash
curl -N "http://localhost:8000/api/v1/sse/prices?tickers=AAPL,MSFT" \
  -H "Accept: text/event-stream" \
  -H "Authorization: Bearer <token>"
```

## Connection Management

### Heartbeats

The server sends heartbeat events every 15 seconds to keep the connection alive:

```
event: heartbeat
data: {"timestamp":"2024-01-15T16:00:15Z"}
```

### Automatic Reconnection

The browser's `EventSource` API automatically reconnects on connection loss. The server sends a `retry` field to suggest reconnection timing:

```
retry: 3000
event: connected
data: {"message":"Connected to price stream"}
```

### Connection Timeout

Connections are terminated after 5 minutes of inactivity (no subscribed ticker activity). Clients should:

1. Handle the `close` event
2. Reconnect if updates are still needed

### Maximum Tickers

- **Per connection**: 50 tickers
- **Per user**: 100 total SSE connections

## Error Handling

### Error Events

```
event: error
data: {"code":"TICKER_NOT_FOUND","message":"Unknown ticker: INVALID"}
```

### HTTP Errors

| Code | Description |
|------|-------------|
| 401 | Unauthorized - invalid/missing token |
| 429 | Too many connections |
| 503 | Service temporarily unavailable |

### Reconnection Strategy

```typescript
class SSEClient {
  private eventSource: EventSource | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private baseDelay = 1000;

  connect(url: string) {
    this.eventSource = new EventSource(url);

    this.eventSource.onerror = () => {
      this.handleError();
    };

    this.eventSource.addEventListener('connected', () => {
      this.reconnectAttempts = 0;
    });
  }

  private handleError() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    const delay = this.baseDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;

    setTimeout(() => {
      this.connect(this.url);
    }, delay);
  }

  disconnect() {
    this.eventSource?.close();
    this.eventSource = null;
  }
}
```

## Performance Considerations

### Throttling

Price updates are throttled to prevent overwhelming clients:

- **Real-time prices**: Max 1 update per ticker per second
- **Portfolio updates**: Max 1 update per 5 seconds

### Batching

When multiple tickers update simultaneously, events are batched:

```
event: prices
data: [
  {"ticker":"AAPL","price":185.92},
  {"ticker":"MSFT","price":402.15},
  {"ticker":"GOOGL","price":142.50}
]
```

### Compression

SSE responses support gzip compression when the client sends:

```http
Accept-Encoding: gzip
```

## Authentication for SSE

SSE connections can authenticate via:

1. **Query parameter** (for EventSource compatibility):
   ```
   /api/v1/sse/prices?token=<jwt>&tickers=AAPL
   ```

2. **Cookie** (for web apps):
   ```javascript
   // Cookies are sent automatically
   new EventSource('/api/v1/sse/prices?tickers=AAPL');
   ```

3. **Custom header** (requires fetch-based implementation):
   ```javascript
   // See React hook example above
   ```

!!! warning "Token in URL"
    Using tokens in URLs is less secure (appears in logs). Use cookies when possible in web applications.

## Testing SSE

### Manual Testing

```bash
# Watch events in terminal
curl -N "http://localhost:8000/api/v1/sse/prices?tickers=AAPL" \
  -H "Accept: text/event-stream"
```

### Automated Testing

```python
import pytest
import httpx

@pytest.mark.asyncio
async def test_price_stream():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "GET",
            "http://localhost:8000/api/v1/sse/prices",
            params={"tickers": "AAPL"},
            headers={"Accept": "text/event-stream"}
        ) as response:
            events = []
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    events.append(line)
                if len(events) >= 2:
                    break

            assert any("connected" in e for e in events)
```

## Related Resources

- [ADR-005: SSE vs WebSocket](../architecture/adr/005-sse-vs-websocket.md)
- [REST API Overview](rest-api.md)
- [Authentication](authentication.md)

