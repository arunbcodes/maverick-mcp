"""
Watchlist API Endpoints.

Provides endpoints for managing user watchlists with real-time price updates.
"""

import logging
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field

from maverick_schemas.base import MaverickBaseModel
from maverick_schemas.responses import APIResponse, ResponseMeta
from maverick_schemas.auth import AuthenticatedUser
from maverick_services import (
    WatchlistService,
    get_watchlist_service,
)
from maverick_api.dependencies import get_current_user, get_request_id, get_redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/watchlists", tags=["Watchlists"])


# ============================================
# Request/Response Models
# ============================================


class CreateWatchlistRequest(MaverickBaseModel):
    """Request to create a watchlist."""
    
    name: str = Field(min_length=1, max_length=50, description="Watchlist name")
    description: str | None = Field(default=None, max_length=200)
    is_default: bool = Field(default=False)


class UpdateWatchlistRequest(MaverickBaseModel):
    """Request to update a watchlist."""
    
    name: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=200)
    is_default: bool | None = None


class AddItemRequest(MaverickBaseModel):
    """Request to add an item to a watchlist."""
    
    ticker: str = Field(min_length=1, max_length=10)
    notes: str | None = Field(default=None, max_length=500)
    target_price: float | None = Field(default=None, gt=0)
    stop_price: float | None = Field(default=None, gt=0)


class AddItemsBatchRequest(MaverickBaseModel):
    """Request to add multiple items."""
    
    tickers: list[str] = Field(min_length=1, max_length=20)


class UpdateItemRequest(MaverickBaseModel):
    """Request to update an item."""
    
    notes: str | None = Field(default=None, max_length=500)
    alert_enabled: bool | None = None
    target_price: float | None = None
    stop_price: float | None = None


class ReorderRequest(MaverickBaseModel):
    """Request to reorder items."""
    
    tickers: list[str] = Field(description="Tickers in desired order")


class QuickAddRequest(MaverickBaseModel):
    """Request for quick add."""
    
    ticker: str = Field(min_length=1, max_length=10)
    watchlist_id: str | None = None


class WatchlistItemResponse(MaverickBaseModel):
    """Watchlist item response."""
    
    ticker: str
    added_at: str
    notes: str | None = None
    alert_enabled: bool
    target_price: float | None = None
    stop_price: float | None = None
    position: int
    current_price: float | None = None
    price_change: float | None = None
    price_change_pct: float | None = None


class WatchlistResponse(MaverickBaseModel):
    """Watchlist response."""
    
    watchlist_id: str
    user_id: str
    name: str
    description: str | None = None
    is_default: bool
    items: list[WatchlistItemResponse]
    item_count: int
    created_at: str
    updated_at: str | None = None


class WatchlistSummaryResponse(MaverickBaseModel):
    """Watchlist summary (without items)."""
    
    watchlist_id: str
    name: str
    description: str | None = None
    is_default: bool
    item_count: int
    created_at: str


class IsWatchingResponse(MaverickBaseModel):
    """Response for checking if watching."""
    
    is_watching: bool
    watchlist_id: str | None = None
    watchlist_name: str | None = None
    notes: str | None = None
    target_price: float | None = None
    stop_price: float | None = None


# ============================================
# Dependencies
# ============================================


async def get_watchlist_service_dep(
    redis=Depends(get_redis),
) -> WatchlistService:
    """Get watchlist service instance."""
    return get_watchlist_service(redis_client=redis)


# ============================================
# Watchlist CRUD Endpoints
# ============================================


@router.get("", response_model=APIResponse[list[WatchlistSummaryResponse]])
async def get_watchlists(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service_dep),
):
    """
    Get all watchlists for the current user.
    
    Returns watchlist summaries without items for performance.
    """
    watchlists = await watchlist_service.get_watchlists(user.user_id)
    
    return APIResponse(
        data=[
            WatchlistSummaryResponse(
                watchlist_id=wl.watchlist_id,
                name=wl.name,
                description=wl.description,
                is_default=wl.is_default,
                item_count=len(wl.items),
                created_at=wl.created_at.isoformat(),
            )
            for wl in watchlists
        ],
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.post("", response_model=APIResponse[WatchlistResponse])
async def create_watchlist(
    data: CreateWatchlistRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service_dep),
):
    """Create a new watchlist."""
    try:
        watchlist = await watchlist_service.create_watchlist(
            user_id=user.user_id,
            name=data.name,
            description=data.description,
            is_default=data.is_default,
        )
        
        return APIResponse(
            data=_watchlist_to_response(watchlist),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/{watchlist_id}", response_model=APIResponse[WatchlistResponse])
async def get_watchlist(
    watchlist_id: str,
    include_prices: bool = Query(default=True, description="Include real-time prices"),
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service_dep),
):
    """Get a specific watchlist with items."""
    watchlist = await watchlist_service.get_watchlist(user.user_id, watchlist_id)
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    # TODO: Populate prices if include_prices is True
    # This would integrate with the stock data service
    
    return APIResponse(
        data=_watchlist_to_response(watchlist),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.patch("/{watchlist_id}", response_model=APIResponse[WatchlistResponse])
async def update_watchlist(
    watchlist_id: str,
    data: UpdateWatchlistRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service_dep),
):
    """Update watchlist details."""
    watchlist = await watchlist_service.update_watchlist(
        user_id=user.user_id,
        watchlist_id=watchlist_id,
        name=data.name,
        description=data.description,
        is_default=data.is_default,
    )
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    return APIResponse(
        data=_watchlist_to_response(watchlist),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.delete("/{watchlist_id}")
async def delete_watchlist(
    watchlist_id: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service_dep),
):
    """Delete a watchlist."""
    try:
        deleted = await watchlist_service.delete_watchlist(user.user_id, watchlist_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        
        return APIResponse(
            data={"deleted": True, "watchlist_id": watchlist_id},
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# Item Management Endpoints
# ============================================


@router.post("/{watchlist_id}/items", response_model=APIResponse[WatchlistItemResponse])
async def add_item(
    watchlist_id: str,
    data: AddItemRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service_dep),
):
    """Add a stock to a watchlist."""
    try:
        item = await watchlist_service.add_item(
            user_id=user.user_id,
            watchlist_id=watchlist_id,
            ticker=data.ticker,
            notes=data.notes,
            target_price=data.target_price,
            stop_price=data.stop_price,
        )
        
        return APIResponse(
            data=_item_to_response(item),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{watchlist_id}/items/batch", response_model=APIResponse[list[WatchlistItemResponse]])
async def add_items_batch(
    watchlist_id: str,
    data: AddItemsBatchRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service_dep),
):
    """Add multiple stocks to a watchlist."""
    try:
        items = await watchlist_service.add_items_batch(
            user_id=user.user_id,
            watchlist_id=watchlist_id,
            tickers=data.tickers,
        )
        
        return APIResponse(
            data=[_item_to_response(item) for item in items],
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{watchlist_id}/items/{ticker}", response_model=APIResponse[WatchlistItemResponse])
async def update_item(
    watchlist_id: str,
    ticker: str,
    data: UpdateItemRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service_dep),
):
    """Update a watchlist item."""
    item = await watchlist_service.update_item(
        user_id=user.user_id,
        watchlist_id=watchlist_id,
        ticker=ticker,
        notes=data.notes,
        alert_enabled=data.alert_enabled,
        target_price=data.target_price,
        stop_price=data.stop_price,
    )
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return APIResponse(
        data=_item_to_response(item),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.delete("/{watchlist_id}/items/{ticker}")
async def remove_item(
    watchlist_id: str,
    ticker: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service_dep),
):
    """Remove a stock from a watchlist."""
    removed = await watchlist_service.remove_item(
        user_id=user.user_id,
        watchlist_id=watchlist_id,
        ticker=ticker,
    )
    
    if not removed:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return APIResponse(
        data={"removed": True, "ticker": ticker},
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.post("/{watchlist_id}/reorder")
async def reorder_items(
    watchlist_id: str,
    data: ReorderRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service_dep),
):
    """Reorder items in a watchlist (for drag & drop)."""
    success = await watchlist_service.reorder_items(
        user_id=user.user_id,
        watchlist_id=watchlist_id,
        tickers=data.tickers,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    return APIResponse(
        data={"reordered": True},
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


# ============================================
# Quick Add & Check Endpoints
# ============================================


@router.post("/quick-add", response_model=APIResponse[dict])
async def quick_add(
    data: QuickAddRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service_dep),
):
    """
    Quickly add a stock to a watchlist.
    
    If no watchlist_id provided, adds to the default watchlist.
    Creates a default watchlist if none exists.
    """
    try:
        item, watchlist = await watchlist_service.quick_add(
            user_id=user.user_id,
            ticker=data.ticker,
            watchlist_id=data.watchlist_id,
        )
        
        return APIResponse(
            data={
                "item": _item_to_response(item).model_dump(),
                "watchlist_id": watchlist.watchlist_id,
                "watchlist_name": watchlist.name,
            },
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/check/{ticker}", response_model=APIResponse[IsWatchingResponse])
async def check_watching(
    ticker: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service_dep),
):
    """Check if a ticker is in any of the user's watchlists."""
    result = await watchlist_service.is_watching(user.user_id, ticker)
    
    if result:
        return APIResponse(
            data=IsWatchingResponse(
                is_watching=True,
                watchlist_id=result["watchlist_id"],
                watchlist_name=result["watchlist_name"],
                notes=result.get("notes"),
                target_price=result.get("target_price"),
                stop_price=result.get("stop_price"),
            ),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    
    return APIResponse(
        data=IsWatchingResponse(is_watching=False),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


# ============================================
# Helpers
# ============================================


def _watchlist_to_response(watchlist) -> WatchlistResponse:
    """Convert Watchlist to response model."""
    return WatchlistResponse(
        watchlist_id=watchlist.watchlist_id,
        user_id=watchlist.user_id,
        name=watchlist.name,
        description=watchlist.description,
        is_default=watchlist.is_default,
        items=[_item_to_response(item) for item in watchlist.items],
        item_count=len(watchlist.items),
        created_at=watchlist.created_at.isoformat(),
        updated_at=watchlist.updated_at.isoformat() if watchlist.updated_at else None,
    )


def _item_to_response(item) -> WatchlistItemResponse:
    """Convert WatchlistItem to response model."""
    return WatchlistItemResponse(
        ticker=item.ticker,
        added_at=item.added_at.isoformat(),
        notes=item.notes,
        alert_enabled=item.alert_enabled,
        target_price=item.target_price,
        stop_price=item.stop_price,
        position=item.position,
        current_price=item.current_price,
        price_change=item.price_change,
        price_change_pct=item.price_change_pct,
    )

