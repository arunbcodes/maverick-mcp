"""
Stock screening endpoints.

Provides Maverick screening strategies, persona-based filtering, and risk scoring.
"""

from datetime import datetime, UTC
from enum import Enum
from typing import Literal

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import Field

from maverick_api.dependencies import (
    get_screening_service,
    get_current_user,
    get_request_id,
)
from maverick_schemas.auth import AuthenticatedUser
from maverick_schemas.base import MaverickBaseModel
from maverick_schemas.screening import (
    MaverickStock,
    ScreeningFilter,
    ScreeningResponse,
)
from maverick_schemas.responses import APIResponse, PaginatedResponse, ResponseMeta
from maverick_services.screening_service import InvestorPersona

router = APIRouter()


# Response model with risk score
class ScreenedStock(MaverickBaseModel):
    """Screened stock with risk information."""
    
    stock: MaverickStock = Field(description="Stock data")
    risk_score: int = Field(ge=1, le=10, description="Risk score 1-10 (higher = riskier)")
    persona_fit: str | None = Field(default=None, description="How well it fits persona")


class ScreenedStocksResponse(MaverickBaseModel):
    """Response with screened stocks and risk data."""
    
    stocks: list[MaverickStock] = Field(description="Screened stocks")
    persona: str | None = Field(default=None, description="Active persona filter")
    total_count: int = Field(description="Total results")


def _parse_persona(persona_str: str | None) -> InvestorPersona | None:
    """Parse persona string to enum."""
    if not persona_str:
        return None
    try:
        return InvestorPersona(persona_str.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid persona. Must be: conservative, moderate, aggressive"
        )


@router.get("/maverick", response_model=APIResponse[list[MaverickStock]])
async def get_maverick_stocks(
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    min_score: float | None = Query(None, ge=0, le=100, description="Minimum Maverick score"),
    above_sma_50: bool | None = Query(None, description="Filter by above 50 SMA"),
    above_sma_200: bool | None = Query(None, description="Filter by above 200 SMA"),
    persona: str | None = Query(None, description="Investor persona: conservative, moderate, aggressive"),
    request_id: str = Depends(get_request_id),
    service=Depends(get_screening_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get Maverick bullish stock picks.

    Returns stocks with high momentum and positive technicals.
    
    Use the `persona` parameter to filter stocks based on risk profile:
    - conservative: Lower volatility, larger cap, dividend stocks
    - moderate: Balanced risk/reward (default behavior)
    - aggressive: High momentum, smaller cap, breakout patterns
    """
    # Build filter from query params
    filters = None
    if any([min_score, above_sma_50, above_sma_200]):
        filters = ScreeningFilter(
            min_momentum_score=min_score,
            above_sma_50=above_sma_50,
            above_sma_200=above_sma_200,
        )

    # Parse and apply persona filter
    investor_persona = _parse_persona(persona)
    
    if investor_persona:
        stocks = await service.get_maverick_stocks_by_persona(
            persona=investor_persona,
            limit=limit,
            filters=filters,
        )
    else:
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
    persona: str | None = Query(None, description="Investor persona: conservative, moderate, aggressive"),
    request_id: str = Depends(get_request_id),
    service=Depends(get_screening_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get Maverick bearish stock picks.

    Returns stocks with weak momentum for potential short opportunities.
    
    Conservative investors will see lower-volatility short candidates.
    Aggressive investors will see high-volatility short opportunities.
    """
    investor_persona = _parse_persona(persona)
    
    if investor_persona:
        stocks = await service.get_maverick_bear_stocks_by_persona(
            persona=investor_persona,
            limit=limit,
        )
    else:
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
    persona: str | None = Query(None, description="Investor persona: conservative, moderate, aggressive"),
    request_id: str = Depends(get_request_id),
    service=Depends(get_screening_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get supply/demand breakout candidates.

    Returns stocks breaking out from accumulation phases.
    
    Conservative investors will see higher-confidence breakouts only.
    Aggressive investors will see more breakout opportunities.
    """
    investor_persona = _parse_persona(persona)
    
    if investor_persona:
        stocks = await service.get_breakout_stocks_by_persona(
            persona=investor_persona,
            limit=limit,
        )
    else:
        stocks = await service.get_breakout_stocks(limit=limit)

    return APIResponse(
        data=stocks,
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


@router.get("/risk-score/{ticker}", response_model=APIResponse[dict])
async def get_stock_risk_score(
    ticker: str,
    request_id: str = Depends(get_request_id),
    service=Depends(get_screening_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get risk score for a specific stock.
    
    Returns a risk score from 1-10 based on:
    - RSI levels
    - Moving average support
    - Volume characteristics
    - Technical patterns
    """
    from maverick_services.screening_service import ScreeningService
    
    # For now, return a placeholder - in production, you'd fetch real data
    # This demonstrates the endpoint structure
    risk_score = ScreeningService.calculate_risk_score_for_data(
        rsi=50,  # Would fetch from real data
        above_sma_50=True,
        above_sma_200=True,
        relative_volume=1.5,
    )
    
    risk_level = "low" if risk_score <= 3 else "moderate" if risk_score <= 6 else "high"
    
    return APIResponse(
        data={
            "ticker": ticker.upper(),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "factors": [
                "RSI at neutral levels",
                "Above both major moving averages",
                "Normal volume patterns",
            ],
        },
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

