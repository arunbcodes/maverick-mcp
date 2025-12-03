"""
Technical analysis endpoints.

Provides RSI, MACD, Bollinger Bands, and comprehensive technical summaries.
"""

from datetime import datetime, UTC

from fastapi import APIRouter, Depends, Query

from maverick_api.dependencies import (
    get_technical_service,
    get_current_user,
    get_request_id,
)
from maverick_schemas.auth import AuthenticatedUser
from maverick_schemas.technical import (
    RSIAnalysis,
    MACDAnalysis,
    BollingerBands,
    MovingAverages,
    TechnicalSummary,
)
from maverick_schemas.responses import APIResponse, ResponseMeta

router = APIRouter()


@router.get("/{ticker}/rsi", response_model=APIResponse[RSIAnalysis])
async def get_rsi(
    ticker: str,
    period: int = Query(14, ge=2, le=50, description="RSI period"),
    days: int = Query(365, ge=30, le=1000, description="Days of historical data"),
    request_id: str = Depends(get_request_id),
    service=Depends(get_technical_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get RSI (Relative Strength Index) analysis.

    Returns current RSI value and interpretation (oversold/neutral/overbought).
    """
    rsi = await service.get_rsi(ticker, period=period, days=days)

    return APIResponse(
        data=rsi,
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


@router.get("/{ticker}/macd", response_model=APIResponse[MACDAnalysis])
async def get_macd(
    ticker: str,
    fast: int = Query(12, ge=2, le=50, description="Fast EMA period"),
    slow: int = Query(26, ge=5, le=100, description="Slow EMA period"),
    signal: int = Query(9, ge=2, le=50, description="Signal line period"),
    days: int = Query(365, ge=30, le=1000, description="Days of historical data"),
    request_id: str = Depends(get_request_id),
    service=Depends(get_technical_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get MACD (Moving Average Convergence Divergence) analysis.

    Returns MACD line, signal line, histogram, and trend interpretation.
    """
    macd = await service.get_macd(
        ticker,
        fast_period=fast,
        slow_period=slow,
        signal_period=signal,
        days=days,
    )

    return APIResponse(
        data=macd,
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


@router.get("/{ticker}/bollinger", response_model=APIResponse[BollingerBands])
async def get_bollinger(
    ticker: str,
    period: int = Query(20, ge=5, le=50, description="SMA period"),
    std_dev: float = Query(2.0, ge=0.5, le=4.0, description="Standard deviations"),
    days: int = Query(365, ge=30, le=1000, description="Days of historical data"),
    request_id: str = Depends(get_request_id),
    service=Depends(get_technical_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get Bollinger Bands analysis.

    Returns upper/middle/lower bands, %B, bandwidth, and interpretation.
    """
    bb = await service.get_bollinger(
        ticker,
        period=period,
        std_dev=std_dev,
        days=days,
    )

    return APIResponse(
        data=bb,
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


@router.get("/{ticker}/moving-averages", response_model=APIResponse[MovingAverages])
async def get_moving_averages(
    ticker: str,
    days: int = Query(365, ge=30, le=1000, description="Days of historical data"),
    request_id: str = Depends(get_request_id),
    service=Depends(get_technical_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get moving averages analysis.

    Returns SMA (20, 50, 100, 200) and EMA (12, 26, 50) with
    golden/death cross detection.
    """
    ma = await service.get_moving_averages(ticker, days=days)

    return APIResponse(
        data=ma,
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


@router.get("/{ticker}/summary", response_model=APIResponse[TechnicalSummary])
async def get_technical_summary(
    ticker: str,
    days: int = Query(365, ge=30, le=1000, description="Days of historical data"),
    request_id: str = Depends(get_request_id),
    service=Depends(get_technical_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get comprehensive technical analysis summary.

    Returns all indicators (RSI, MACD, Bollinger, MAs) with overall
    recommendation and confidence score.
    """
    summary = await service.get_summary(ticker, days=days)

    return APIResponse(
        data=summary,
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


__all__ = ["router"]

