"""
Server-Sent Events (SSE) endpoints.

Provides real-time price updates and portfolio P&L streaming.
"""

import json

from fastapi import APIRouter, Depends, Query, Request
from sse_starlette.sse import EventSourceResponse

from maverick_api.dependencies import (
    get_sse_manager,
    get_current_user,
)
from maverick_schemas.auth import AuthenticatedUser

router = APIRouter()


@router.get("/prices")
async def price_stream(
    request: Request,
    tickers: str = Query(..., description="Comma-separated tickers (e.g., AAPL,MSFT,GOOGL)"),
    sse_manager=Depends(get_sse_manager),
):
    """
    Stream real-time price updates via Server-Sent Events.

    Subscribe to price updates for specified tickers. Updates are pushed
    when prices change. Heartbeats are sent every 15 seconds to keep
    connections alive through proxies.

    **Usage:**
    ```javascript
    const eventSource = new EventSource('/api/v1/sse/prices?tickers=AAPL,MSFT');
    eventSource.addEventListener('price_update', (event) => {
        const data = JSON.parse(event.data);
        console.log(data.ticker, data.price);
    });
    eventSource.addEventListener('heartbeat', (event) => {
        // Connection is alive
    });
    ```

    **Advantages over WebSocket:**
    - Auto-reconnect built into browser
    - Better firewall compatibility
    - Lower battery usage on mobile
    """
    ticker_set = set(t.strip().upper() for t in tickers.split(",") if t.strip())

    if not ticker_set:
        return EventSourceResponse(
            iter([{"event": "error", "data": json.dumps({"error": "No tickers specified"})}])
        )

    async def event_generator():
        async for data in sse_manager.subscribe_prices(ticker_set):
            if await request.is_disconnected():
                break

            # Handle heartbeat events
            if data.get("_heartbeat"):
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({"timestamp": data["timestamp"]}),
                }
            else:
                yield {
                    "event": "price_update",
                    "data": json.dumps(data),
                }

    return EventSourceResponse(event_generator())


@router.get("/portfolio")
async def portfolio_stream(
    request: Request,
    sse_manager=Depends(get_sse_manager),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Stream portfolio P&L updates via Server-Sent Events.

    Requires authentication. Streams updates for the authenticated user's
    portfolio when positions or prices change. Heartbeats are sent every
    15 seconds to keep connections alive.

    **Usage:**
    ```javascript
    const eventSource = new EventSource('/api/v1/sse/portfolio', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    eventSource.addEventListener('portfolio_update', (event) => {
        const data = JSON.parse(event.data);
        console.log('Total P&L:', data.total_pnl);
    });
    ```
    """
    async def event_generator():
        async for data in sse_manager.subscribe_portfolio(user.user_id):
            if await request.is_disconnected():
                break

            if data.get("_heartbeat"):
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({"timestamp": data["timestamp"]}),
                }
            else:
                yield {
                    "event": "portfolio_update",
                    "data": json.dumps(data),
                }

    return EventSourceResponse(event_generator())


@router.get("/alerts")
async def alerts_stream(
    request: Request,
    sse_manager=Depends(get_sse_manager),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Stream price alerts via Server-Sent Events.

    Requires authentication. Streams alerts when user-defined price
    conditions are triggered. Heartbeats are sent every 15 seconds.

    **Usage:**
    ```javascript
    const eventSource = new EventSource('/api/v1/sse/alerts');
    eventSource.addEventListener('alert', (event) => {
        const data = JSON.parse(event.data);
        console.log(`Alert: ${data.ticker} ${data.condition}`);
    });
    ```
    """
    async def event_generator():
        async for data in sse_manager.subscribe_alerts(user.user_id):
            if await request.is_disconnected():
                break

            if data.get("_heartbeat"):
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({"timestamp": data["timestamp"]}),
                }
            else:
                yield {
                    "event": "alert",
                    "data": json.dumps(data),
                }

    return EventSourceResponse(event_generator())


__all__ = ["router"]

