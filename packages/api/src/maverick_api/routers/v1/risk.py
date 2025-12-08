"""
Risk Analytics API Endpoints.

Provides endpoints for correlation analysis, diversification scoring,
sector exposure, and advanced risk metrics.
"""

import logging
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field

from maverick_schemas.base import MaverickBaseModel
from maverick_schemas.responses import APIResponse, ResponseMeta
from maverick_schemas.auth import AuthenticatedUser
from maverick_services import (
    CorrelationService,
    CorrelationPeriod,
    get_correlation_service,
)
from maverick_api.dependencies import get_current_user, get_request_id, get_redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk", tags=["Risk Analytics"])


# ============================================
# Request/Response Models
# ============================================


class CorrelationMatrixRequest(MaverickBaseModel):
    """Request for correlation matrix."""
    
    tickers: list[str] = Field(min_length=2, max_length=50)
    period_days: int = Field(default=90, ge=30, le=504)


class CorrelationMatrixResponse(MaverickBaseModel):
    """Correlation matrix response."""
    
    tickers: list[str]
    matrix: list[list[float]]
    period_days: int
    data_points: int
    calculated_at: str
    stats: dict


class PairCorrelationResponse(MaverickBaseModel):
    """Pair correlation response."""
    
    ticker1: str
    ticker2: str
    correlation: float
    period_days: int
    data_points: int
    calculated_at: str
    interpretation: str


class HighCorrelationPair(MaverickBaseModel):
    """High correlation pair."""
    
    ticker1: str
    ticker2: str
    correlation: float


class RollingCorrelationPoint(MaverickBaseModel):
    """Rolling correlation data point."""
    
    date: str
    correlation: float


# ============================================
# Dependencies
# ============================================


async def get_correlation_service_dep(
    redis=Depends(get_redis),
) -> CorrelationService:
    """Get correlation service instance."""
    return get_correlation_service(redis_client=redis)


# ============================================
# Correlation Endpoints
# ============================================


@router.post("/correlation/matrix", response_model=APIResponse[CorrelationMatrixResponse])
async def calculate_correlation_matrix(
    data: CorrelationMatrixRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    correlation_service: CorrelationService = Depends(get_correlation_service_dep),
):
    """
    Calculate correlation matrix for a list of tickers.
    
    Returns a matrix showing correlation between all pairs.
    """
    try:
        # Map days to period enum
        period = _days_to_period(data.period_days)
        
        matrix = await correlation_service.calculate_correlation_matrix(
            tickers=data.tickers,
            period=period,
        )
        
        stats = correlation_service.calculate_statistics(matrix)
        
        return APIResponse(
            data=CorrelationMatrixResponse(
                tickers=matrix.tickers,
                matrix=matrix.matrix,
                period_days=matrix.period_days,
                data_points=matrix.data_points,
                calculated_at=matrix.calculated_at.isoformat(),
                stats=stats.to_dict(),
            ),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/correlation/pair", response_model=APIResponse[PairCorrelationResponse])
async def get_pair_correlation(
    ticker1: str = Query(description="First ticker"),
    ticker2: str = Query(description="Second ticker"),
    period_days: int = Query(default=90, ge=30, le=504),
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    correlation_service: CorrelationService = Depends(get_correlation_service_dep),
):
    """
    Get correlation between two specific tickers.
    
    More efficient than full matrix when only comparing 2 stocks.
    """
    try:
        period = _days_to_period(period_days)
        
        pair = await correlation_service.calculate_pair_correlation(
            ticker1=ticker1,
            ticker2=ticker2,
            period=period,
        )
        
        return APIResponse(
            data=PairCorrelationResponse(
                ticker1=pair.ticker1,
                ticker2=pair.ticker2,
                correlation=pair.correlation,
                period_days=pair.period_days,
                data_points=pair.data_points,
                calculated_at=pair.calculated_at.isoformat(),
                interpretation=_interpret_correlation(pair.correlation),
            ),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/correlation/pair/multi-period")
async def get_pair_correlation_multi_period(
    ticker1: str = Query(description="First ticker"),
    ticker2: str = Query(description="Second ticker"),
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    correlation_service: CorrelationService = Depends(get_correlation_service_dep),
):
    """
    Get correlation for multiple time periods (30d, 90d, 1y).
    
    Useful for seeing how correlation changes over time.
    """
    try:
        results = await correlation_service.calculate_correlation_across_periods(
            ticker1=ticker1,
            ticker2=ticker2,
        )
        
        formatted = {}
        for period, pair in results.items():
            formatted[period] = {
                "correlation": pair.correlation,
                "data_points": pair.data_points,
                "interpretation": _interpret_correlation(pair.correlation),
            }
        
        return APIResponse(
            data={
                "ticker1": ticker1.upper(),
                "ticker2": ticker2.upper(),
                "periods": formatted,
            },
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/correlation/rolling", response_model=APIResponse[list[RollingCorrelationPoint]])
async def get_rolling_correlation(
    ticker1: str = Query(description="First ticker"),
    ticker2: str = Query(description="Second ticker"),
    window: int = Query(default=30, ge=10, le=90, description="Rolling window in days"),
    total_days: int = Query(default=252, ge=60, le=504, description="Total lookback period"),
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    correlation_service: CorrelationService = Depends(get_correlation_service_dep),
):
    """
    Get rolling correlation time series.
    
    Shows how correlation between two stocks changes over time.
    """
    try:
        rolling = await correlation_service.calculate_rolling_correlation(
            ticker1=ticker1,
            ticker2=ticker2,
            window=window,
            total_days=total_days,
        )
        
        return APIResponse(
            data=[RollingCorrelationPoint(**point) for point in rolling],
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/correlation/high-pairs", response_model=APIResponse[list[HighCorrelationPair]])
async def get_high_correlation_pairs(
    data: CorrelationMatrixRequest,
    threshold: float = Query(default=0.7, ge=0.5, le=0.99),
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    correlation_service: CorrelationService = Depends(get_correlation_service_dep),
):
    """
    Find pairs with correlation above threshold.
    
    Useful for identifying concentration risk.
    """
    try:
        period = _days_to_period(data.period_days)
        
        matrix = await correlation_service.calculate_correlation_matrix(
            tickers=data.tickers,
            period=period,
        )
        
        high_pairs = matrix.get_high_correlations(threshold)
        
        return APIResponse(
            data=[
                HighCorrelationPair(ticker1=t1, ticker2=t2, correlation=corr)
                for t1, t2, corr in high_pairs
            ],
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# Helpers
# ============================================


def _days_to_period(days: int) -> CorrelationPeriod:
    """Map days to nearest CorrelationPeriod."""
    if days <= 30:
        return CorrelationPeriod.DAYS_30
    elif days <= 90:
        return CorrelationPeriod.DAYS_90
    elif days <= 180:
        return CorrelationPeriod.DAYS_180
    elif days <= 252:
        return CorrelationPeriod.YEAR_1
    else:
        return CorrelationPeriod.YEAR_2


def _interpret_correlation(corr: float) -> str:
    """Provide human-readable interpretation of correlation value."""
    abs_corr = abs(corr)
    direction = "positively" if corr > 0 else "negatively"
    
    if abs_corr >= 0.9:
        return f"Very strongly {direction} correlated - essentially move together"
    elif abs_corr >= 0.7:
        return f"Strongly {direction} correlated - limited diversification benefit"
    elif abs_corr >= 0.5:
        return f"Moderately {direction} correlated - some diversification benefit"
    elif abs_corr >= 0.3:
        return f"Weakly {direction} correlated - good diversification"
    else:
        return "Very low correlation - excellent diversification"

