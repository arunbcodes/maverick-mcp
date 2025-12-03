"""
Portfolio management endpoints.

Provides portfolio tracking, position management, and P&L calculation.
"""

from datetime import datetime, UTC
from decimal import Decimal

from fastapi import APIRouter, Depends, Query

from maverick_api.dependencies import (
    get_portfolio_service,
    get_current_user,
    get_request_id,
)
from maverick_schemas.auth import AuthenticatedUser
from maverick_schemas.portfolio import Portfolio, Position, PositionCreate
from maverick_schemas.responses import APIResponse, ResponseMeta

router = APIRouter()


@router.get("", response_model=APIResponse[Portfolio])
async def get_portfolio(
    include_prices: bool = Query(True, description="Include current prices and P&L"),
    request_id: str = Depends(get_request_id),
    service=Depends(get_portfolio_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get user's portfolio with all positions.

    Returns positions with cost basis and optionally current prices/P&L.
    """
    portfolio = await service.get_portfolio(
        user_id=user.user_id,
        include_prices=include_prices,
    )

    return APIResponse(
        data=portfolio,
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


@router.post("/positions", response_model=APIResponse[Position])
async def add_position(
    position: PositionCreate,
    request_id: str = Depends(get_request_id),
    service=Depends(get_portfolio_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Add a position to the portfolio.

    If the ticker already exists, averages into the existing position.
    """
    created = await service.add_position(
        user_id=user.user_id,
        position=position,
    )

    return APIResponse(
        data=created,
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


@router.delete("/positions/{ticker}", response_model=APIResponse[dict])
async def remove_position(
    ticker: str,
    shares: Decimal | None = Query(None, description="Shares to remove (all if not specified)"),
    request_id: str = Depends(get_request_id),
    service=Depends(get_portfolio_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Remove shares from a position or close entirely.

    If shares not specified, removes the entire position.
    """
    result = await service.remove_position(
        user_id=user.user_id,
        ticker=ticker,
        shares=shares,
    )

    message = "Position closed" if result is None else f"Removed shares from {ticker}"

    return APIResponse(
        data={"message": message, "remaining": result.model_dump() if result else None},
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


__all__ = ["router"]

