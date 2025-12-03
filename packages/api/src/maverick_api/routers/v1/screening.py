"""
Stock screening endpoints.

Provides Maverick screening strategies and custom filtering.
"""

from datetime import datetime, UTC

from fastapi import APIRouter, Depends, Query

from maverick_api.dependencies import (
    get_screening_service,
    get_current_user,
    get_request_id,
)
from maverick_schemas.auth import AuthenticatedUser
from maverick_schemas.screening import (
    MaverickStock,
    ScreeningFilter,
    ScreeningResponse,
)
from maverick_schemas.responses import APIResponse, PaginatedResponse, ResponseMeta

router = APIRouter()


@router.get("/maverick", response_model=APIResponse[list[MaverickStock]])
async def get_maverick_stocks(
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    min_score: float | None = Query(None, ge=0, le=100, description="Minimum Maverick score"),
    above_sma_50: bool | None = Query(None, description="Filter by above 50 SMA"),
    above_sma_200: bool | None = Query(None, description="Filter by above 200 SMA"),
    request_id: str = Depends(get_request_id),
    service=Depends(get_screening_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get Maverick bullish stock picks.

    Returns stocks with high momentum and positive technicals.
    """
    # Build filter from query params
    filters = None
    if any([min_score, above_sma_50, above_sma_200]):
        filters = ScreeningFilter(
            min_momentum_score=min_score,
            above_sma_50=above_sma_50,
            above_sma_200=above_sma_200,
        )

    stocks = await service.get_maverick_stocks(limit=limit, filters=filters)

    return APIResponse(
        data=stocks,
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


@router.get("/bearish", response_model=APIResponse[list[MaverickStock]])
async def get_bearish_stocks(
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    request_id: str = Depends(get_request_id),
    service=Depends(get_screening_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get Maverick bearish stock picks.

    Returns stocks with weak momentum for potential short opportunities.
    """
    stocks = await service.get_maverick_bear_stocks(limit=limit)

    return APIResponse(
        data=stocks,
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


@router.get("/breakouts", response_model=APIResponse[list[MaverickStock]])
async def get_breakout_stocks(
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    request_id: str = Depends(get_request_id),
    service=Depends(get_screening_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get supply/demand breakout candidates.

    Returns stocks breaking out from accumulation phases.
    """
    stocks = await service.get_breakout_stocks(limit=limit)

    return APIResponse(
        data=stocks,
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


@router.post("/custom", response_model=ScreeningResponse)
async def screen_custom(
    filters: ScreeningFilter,
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    request_id: str = Depends(get_request_id),
    service=Depends(get_screening_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Screen stocks with custom criteria.

    Allows filtering by price, volume, RSI, moving averages, etc.
    """
    response = await service.screen_by_criteria(filters=filters, limit=limit)

    return response


__all__ = ["router"]

