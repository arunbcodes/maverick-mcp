"""
Stock data endpoints.

Provides stock quotes, historical data, and company information.
"""

from datetime import datetime, UTC

from fastapi import APIRouter, Depends, Query

from maverick_api.dependencies import (
    get_stock_service,
    get_current_user,
    get_request_id,
)
from maverick_schemas.auth import AuthenticatedUser
from maverick_schemas.stock import StockQuote, StockInfo, StockHistory, BatchQuoteRequest, BatchQuoteResponse
from maverick_schemas.responses import APIResponse, ResponseMeta

router = APIRouter()


@router.get("/{ticker}", response_model=APIResponse[StockInfo])
async def get_stock(
    ticker: str,
    request_id: str = Depends(get_request_id),
    service=Depends(get_stock_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get stock information.

    Returns company details, valuation metrics, and trading info.
    """
    info = await service.get_info(ticker)

    return APIResponse(
        data=info,
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


@router.get("/{ticker}/quote", response_model=APIResponse[StockQuote])
async def get_quote(
    ticker: str,
    request_id: str = Depends(get_request_id),
    service=Depends(get_stock_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get real-time quote for a stock.

    Returns current price, change, volume, and other quote data.
    """
    quote = await service.get_quote(ticker)

    return APIResponse(
        data=quote,
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


@router.get("/{ticker}/history", response_model=APIResponse[StockHistory])
async def get_history(
    ticker: str,
    start: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    interval: str = Query("1d", description="Data interval (1d, 1wk, 1mo)"),
    fields: str | None = Query(
        None,
        description="Comma-separated fields to return (for bandwidth optimization)",
    ),
    request_id: str = Depends(get_request_id),
    service=Depends(get_stock_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get historical OHLCV data for a stock.

    Returns daily open, high, low, close, and volume data.

    Mobile optimization: Use `fields` parameter to reduce payload size.
    Example: `?fields=date,close,volume`
    """
    history = await service.get_history(
        ticker,
        start_date=start,
        end_date=end,
        interval=interval,
    )

    # Apply field filtering for mobile optimization
    if fields:
        requested_fields = set(f.strip().lower() for f in fields.split(","))
        filtered_data = []
        for ohlcv in history.data:
            filtered = {}
            ohlcv_dict = ohlcv.model_dump()
            for field in requested_fields:
                if field in ohlcv_dict:
                    filtered[field] = ohlcv_dict[field]
            filtered_data.append(filtered)
        # Return as dict response for filtered data
        return APIResponse(
            data={"ticker": history.ticker, "data": filtered_data},
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )

    return APIResponse(
        data=history,
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


@router.post("/batch", response_model=APIResponse[BatchQuoteResponse])
async def get_batch_quotes(
    request: BatchQuoteRequest,
    request_id: str = Depends(get_request_id),
    service=Depends(get_stock_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get quotes for multiple stocks.

    Efficient endpoint for fetching multiple quotes in one request.
    Limited to 50 tickers per request.
    """
    tickers = request.tickers
    if len(tickers) > 50:
        tickers = tickers[:50]

    response = await service.get_batch_quotes(tickers)

    return APIResponse(
        data=response,
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


__all__ = ["router"]

