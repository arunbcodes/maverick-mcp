# ADR-005: SSE vs WebSocket for Real-Time Updates

## Status

Accepted

## Date

2024-12-02

## Context

We need real-time updates for:
1. Stock price streaming
2. Portfolio P&L updates
3. Price alert notifications

Options considered:
- WebSocket
- Server-Sent Events (SSE)
- Long polling

## Decision

We will use **Server-Sent Events (SSE)** for real-time updates.

### SSE Endpoint Example

```python
@router.get("/sse/prices")
async def price_stream(
    request: Request,
    tickers: str,  # Comma-separated: "AAPL,MSFT,GOOGL"
):
    ticker_set = set(tickers.split(","))
    
    async def event_generator():
        async for price in sse_manager.subscribe_prices(ticker_set):
            if await request.is_disconnected():
                break
            yield {
                "event": "price_update",
                "data": json.dumps(price),
            }
    
    return EventSourceResponse(event_generator())
```

### Client Usage

```javascript
const eventSource = new EventSource('/api/v1/sse/prices?tickers=AAPL,MSFT');

eventSource.addEventListener('price_update', (event) => {
    const data = JSON.parse(event.data);
    console.log(`${data.ticker}: $${data.price}`);
});

eventSource.onerror = (error) => {
    console.log('Connection error, auto-reconnecting...');
    // Browser handles reconnection automatically
};
```

### Horizontal Scaling with Redis Pub/Sub

```
┌─────────────────────────────────────────────────────────┐
│                    Redis Pub/Sub                         │
│                                                          │
│   Channel: sse:prices     Channel: sse:portfolio:123    │
└───────────┬─────────────────────────┬────────────────────┘
            │                         │
     ┌──────┴──────┐           ┌──────┴──────┐
     │             │           │             │
     ▼             ▼           ▼             ▼
┌─────────┐   ┌─────────┐  ┌─────────┐   ┌─────────┐
│ Worker 1│   │ Worker 2│  │ Worker 1│   │ Worker 2│
│  SSE    │   │  SSE    │  │  SSE    │   │  SSE    │
└────┬────┘   └────┬────┘  └────┬────┘   └────┬────┘
     │             │            │             │
     ▼             ▼            ▼             ▼
  Client A      Client B     Client C     Client D
```

Background workers publish to Redis channels. Each API worker subscribes and forwards to its connected clients.

## Why SSE over WebSocket

| Factor | SSE | WebSocket |
|--------|-----|-----------|
| **Auto-reconnect** | Built into browser | Must implement |
| **Firewall compatibility** | Uses HTTP | May be blocked |
| **Mobile battery** | Lower (unidirectional) | Higher (bidirectional) |
| **Complexity** | Simple HTTP | Protocol handshake |
| **Proxy support** | Works through HTTP proxies | Often problematic |
| **Use case fit** | Server → Client updates ✓ | Bidirectional chat |

### When to Use WebSocket

- Bidirectional communication needed (e.g., chat)
- High-frequency updates (>10/second)
- Binary data transfer

Our use case (price updates every 5 seconds) fits SSE perfectly.

## Consequences

### Positive
- Simpler implementation
- Better mobile battery life
- Automatic reconnection
- Works through corporate proxies

### Negative
- Unidirectional only (server → client)
- Limited to 6 connections per domain in HTTP/1.1 (not an issue with HTTP/2)
- Must implement heartbeat for some proxies

## Heartbeat Implementation

Some proxies close idle connections. We send periodic comments:

```python
async def event_generator():
    last_event = time.time()
    
    async for price in subscribe():
        yield {"event": "price_update", "data": price}
        last_event = time.time()
        
        # Send heartbeat every 15 seconds
        if time.time() - last_event > 15:
            yield {"comment": "heartbeat"}
            last_event = time.time()
```

## References

- [SSE Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [SSE vs WebSocket](https://ably.com/blog/websockets-vs-sse)
- [sse-starlette Library](https://github.com/sysid/sse-starlette)

