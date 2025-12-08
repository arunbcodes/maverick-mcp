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
    DiversificationService,
    get_diversification_service,
    RiskMetricsService,
    StressScenario,
    STRESS_SCENARIOS,
    get_risk_metrics_service,
    GICS_SECTORS,
    SP500_SECTOR_WEIGHTS,
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


def get_diversification_service_dep() -> DiversificationService:
    """Get diversification service instance."""
    return get_diversification_service()


def get_risk_metrics_service_dep() -> RiskMetricsService:
    """Get risk metrics service instance."""
    return get_risk_metrics_service()


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


# ============================================
# Diversification Endpoints
# ============================================


class DiversificationRequest(MaverickBaseModel):
    """Request for diversification analysis."""
    
    positions: list[dict] = Field(description="Portfolio positions with ticker, market_value")
    sector_map: dict[str, str] | None = Field(default=None, description="Optional ticker->sector mapping")
    avg_correlation: float | None = Field(default=None, ge=-1, le=1)


class PositionConcentrationResponse(MaverickBaseModel):
    """Position concentration data."""
    
    ticker: str
    weight: float
    is_overconcentrated: bool


class SectorConcentrationResponse(MaverickBaseModel):
    """Sector concentration data."""
    
    sector: str
    weight: float
    benchmark_weight: float
    deviation: float
    is_overweight: bool
    is_underweight: bool


class DiversificationBreakdownResponse(MaverickBaseModel):
    """Score breakdown."""
    
    position_score: float
    sector_score: float
    correlation_score: float
    concentration_score: float
    weights: dict


class DiversificationResponse(MaverickBaseModel):
    """Diversification analysis response."""
    
    score: float
    level: str
    hhi: float
    hhi_normalized: float
    effective_positions: float
    position_count: int
    largest_position: PositionConcentrationResponse | None = None
    overconcentrated_count: int
    sector_count: int
    avg_correlation: float | None = None
    breakdown: DiversificationBreakdownResponse
    recommendations: list[str]
    calculated_at: str


@router.post("/diversification/score", response_model=APIResponse[DiversificationResponse])
async def calculate_diversification_score(
    data: DiversificationRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    div_service: DiversificationService = Depends(get_diversification_service_dep),
):
    """
    Calculate portfolio diversification score.
    
    Returns:
    - Overall score (0-100)
    - HHI concentration index
    - Effective number of positions
    - Position and sector concentration analysis
    - Actionable recommendations
    """
    result = div_service.calculate_diversification_score(
        positions=data.positions,
        sector_map=data.sector_map,
        avg_correlation=data.avg_correlation,
    )
    
    return APIResponse(
        data=DiversificationResponse(
            score=round(result.score, 1),
            level=result.level.value,
            hhi=round(result.hhi, 2),
            hhi_normalized=round(result.hhi_normalized, 1),
            effective_positions=round(result.effective_positions, 1),
            position_count=result.position_count,
            largest_position=PositionConcentrationResponse(
                ticker=result.largest_position.ticker,
                weight=round(result.largest_position.weight, 2),
                is_overconcentrated=result.largest_position.is_overconcentrated,
            ) if result.largest_position else None,
            overconcentrated_count=len(result.overconcentrated_positions),
            sector_count=result.sector_count,
            avg_correlation=round(result.avg_correlation, 3) if result.avg_correlation else None,
            breakdown=DiversificationBreakdownResponse(
                position_score=round(result.breakdown.position_score, 1),
                sector_score=round(result.breakdown.sector_score, 1),
                correlation_score=round(result.breakdown.correlation_score, 1),
                concentration_score=round(result.breakdown.concentration_score, 1),
                weights={
                    "position": result.breakdown.position_weight,
                    "sector": result.breakdown.sector_weight,
                    "correlation": result.breakdown.correlation_weight,
                    "concentration": result.breakdown.concentration_weight,
                },
            ),
            recommendations=result.recommendations,
            calculated_at=result.calculated_at.isoformat(),
        ),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.post("/diversification/sectors", response_model=APIResponse[list[SectorConcentrationResponse]])
async def get_sector_breakdown(
    data: DiversificationRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    div_service: DiversificationService = Depends(get_diversification_service_dep),
):
    """
    Get detailed sector breakdown with benchmark comparison.
    """
    result = div_service.calculate_diversification_score(
        positions=data.positions,
        sector_map=data.sector_map,
    )
    
    return APIResponse(
        data=[
            SectorConcentrationResponse(
                sector=s.sector,
                weight=round(s.weight, 2),
                benchmark_weight=round(s.benchmark_weight, 2),
                deviation=round(s.deviation, 2),
                is_overweight=s.is_overweight,
                is_underweight=s.is_underweight,
            )
            for s in result.sector_breakdown
        ],
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.get("/diversification/sectors/benchmark")
async def get_sector_benchmarks(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get S&P 500 sector benchmark weights.
    """
    return APIResponse(
        data={
            "sectors": GICS_SECTORS,
            "weights": SP500_SECTOR_WEIGHTS,
        },
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


# ============================================
# Sector Exposure Endpoints
# ============================================


class SectorExposureItem(MaverickBaseModel):
    """Sector exposure data."""
    
    sector: str
    weight: float  # Portfolio weight %
    benchmark_weight: float  # S&P 500 weight %
    deviation: float  # Difference from benchmark
    status: str  # "overweight", "underweight", "neutral"
    recommendation: str | None = None


class SectorExposureResponse(MaverickBaseModel):
    """Sector exposure analysis response."""
    
    sectors: list[SectorExposureItem]
    total_weight: float
    covered_sectors: int
    total_sectors: int
    overweight_count: int
    underweight_count: int


@router.post("/sectors/exposure", response_model=APIResponse[SectorExposureResponse])
async def get_sector_exposure(
    data: DiversificationRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    div_service: DiversificationService = Depends(get_diversification_service_dep),
):
    """
    Get detailed sector exposure analysis with benchmark comparison.
    
    Returns sector weights vs S&P 500 benchmark with recommendations.
    """
    result = div_service.calculate_diversification_score(
        positions=data.positions,
        sector_map=data.sector_map,
    )
    
    sector_items = []
    overweight_count = 0
    underweight_count = 0
    
    for s in result.sector_breakdown:
        # Determine status
        if s.weight == 0 and s.benchmark_weight > 3:
            status = "missing"
            recommendation = f"Consider adding {s.sector} exposure ({s.benchmark_weight:.1f}% benchmark)"
        elif s.deviation > 10:
            status = "overweight"
            overweight_count += 1
            recommendation = f"Consider reducing ({s.weight:.1f}% vs {s.benchmark_weight:.1f}% benchmark)"
        elif s.deviation < -5 and s.benchmark_weight > 3:
            status = "underweight"
            underweight_count += 1
            recommendation = f"Consider increasing ({s.weight:.1f}% vs {s.benchmark_weight:.1f}% benchmark)"
        else:
            status = "neutral"
            recommendation = None
        
        sector_items.append(SectorExposureItem(
            sector=s.sector,
            weight=round(s.weight, 2),
            benchmark_weight=round(s.benchmark_weight, 2),
            deviation=round(s.deviation, 2),
            status=status,
            recommendation=recommendation,
        ))
    
    # Sort by weight descending
    sector_items.sort(key=lambda x: x.weight, reverse=True)
    
    return APIResponse(
        data=SectorExposureResponse(
            sectors=sector_items,
            total_weight=sum(s.weight for s in sector_items),
            covered_sectors=sum(1 for s in sector_items if s.weight > 0),
            total_sectors=11,
            overweight_count=overweight_count,
            underweight_count=underweight_count,
        ),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


class SectorComparisonItem(MaverickBaseModel):
    """Single sector comparison."""
    
    sector: str
    portfolio_weight: float
    benchmark_weight: float


@router.post("/sectors/comparison", response_model=APIResponse[list[SectorComparisonItem]])
async def get_sector_comparison(
    data: DiversificationRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    div_service: DiversificationService = Depends(get_diversification_service_dep),
):
    """
    Get sector weight comparison for bar chart visualization.
    
    Returns portfolio weights alongside benchmark weights for all sectors.
    """
    result = div_service.calculate_diversification_score(
        positions=data.positions,
        sector_map=data.sector_map,
    )
    
    comparison = []
    for s in result.sector_breakdown:
        if s.sector != "Unknown":  # Skip unknown sector
            comparison.append(SectorComparisonItem(
                sector=s.sector,
                portfolio_weight=round(s.weight, 2),
                benchmark_weight=round(s.benchmark_weight, 2),
            ))
    
    # Sort by benchmark weight descending
    comparison.sort(key=lambda x: x.benchmark_weight, reverse=True)
    
    return APIResponse(
        data=comparison,
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


class SectorRebalanceSuggestion(MaverickBaseModel):
    """Rebalancing suggestion for a sector."""
    
    sector: str
    current_weight: float
    target_weight: float
    action: str  # "buy", "sell", "hold"
    change_needed: float  # Percentage points to change
    priority: str  # "high", "medium", "low"


@router.post("/sectors/rebalance", response_model=APIResponse[list[SectorRebalanceSuggestion]])
async def get_sector_rebalance_suggestions(
    data: DiversificationRequest,
    target_profile: str = Query(default="balanced", description="Target: balanced, aggressive, defensive"),
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    div_service: DiversificationService = Depends(get_diversification_service_dep),
):
    """
    Get sector rebalancing suggestions based on target profile.
    
    Profiles:
    - balanced: Match S&P 500 weights
    - aggressive: Overweight Tech, Communication, Consumer Disc
    - defensive: Overweight Utilities, Consumer Staples, Healthcare
    """
    result = div_service.calculate_diversification_score(
        positions=data.positions,
        sector_map=data.sector_map,
    )
    
    # Define target weights based on profile
    if target_profile == "aggressive":
        target_weights = {
            "Technology": 35.0,
            "Healthcare": 12.0,
            "Financials": 10.0,
            "Consumer Discretionary": 12.0,
            "Communication Services": 12.0,
            "Industrials": 7.0,
            "Consumer Staples": 4.0,
            "Energy": 3.0,
            "Utilities": 1.5,
            "Real Estate": 2.0,
            "Materials": 1.5,
        }
    elif target_profile == "defensive":
        target_weights = {
            "Technology": 20.0,
            "Healthcare": 18.0,
            "Financials": 14.0,
            "Consumer Discretionary": 7.0,
            "Communication Services": 6.0,
            "Industrials": 10.0,
            "Consumer Staples": 12.0,
            "Energy": 5.0,
            "Utilities": 5.0,
            "Real Estate": 2.0,
            "Materials": 1.0,
        }
    else:  # balanced
        target_weights = SP500_SECTOR_WEIGHTS.copy()
    
    suggestions = []
    for s in result.sector_breakdown:
        if s.sector == "Unknown":
            continue
        
        target = target_weights.get(s.sector, 0)
        change = target - s.weight
        
        # Determine action and priority
        if abs(change) < 2:
            action = "hold"
            priority = "low"
        elif change > 0:
            action = "buy"
            priority = "high" if change > 5 else "medium"
        else:
            action = "sell"
            priority = "high" if abs(change) > 5 else "medium"
        
        suggestions.append(SectorRebalanceSuggestion(
            sector=s.sector,
            current_weight=round(s.weight, 2),
            target_weight=round(target, 2),
            action=action,
            change_needed=round(change, 2),
            priority=priority,
        ))
    
    # Sort by priority and change magnitude
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda x: (priority_order[x.priority], -abs(x.change_needed)))
    
    return APIResponse(
        data=suggestions,
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


# ============================================
# Advanced Risk Metrics Endpoints
# ============================================


class RiskMetricsRequest(MaverickBaseModel):
    """Request for risk metrics calculation."""
    
    portfolio_returns: list[float] = Field(min_length=20)
    benchmark_returns: list[float] | None = Field(default=None)
    portfolio_value: float = Field(gt=0)
    var_method: str = Field(default="historical")


class VaRResponse(MaverickBaseModel):
    """VaR calculation response."""
    
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    method: str
    period_days: int
    portfolio_value: float
    var_95_amount: float
    var_99_amount: float
    cvar_95_amount: float
    cvar_99_amount: float


class BetaResponse(MaverickBaseModel):
    """Beta calculation response."""
    
    beta: float
    alpha: float
    r_squared: float
    correlation: float
    interpretation: str


class VolatilityResponse(MaverickBaseModel):
    """Volatility metrics response."""
    
    daily_volatility: float
    annualized_volatility: float
    downside_volatility: float
    upside_volatility: float
    volatility_skew: float
    max_daily_loss: float
    max_daily_gain: float


class StressTestResponse(MaverickBaseModel):
    """Stress test result response."""
    
    scenario: str
    scenario_name: str
    description: str
    market_return: float
    estimated_portfolio_loss: float
    estimated_loss_amount: float
    recovery_estimate_days: int | None = None


class RiskMetricsSummaryResponse(MaverickBaseModel):
    """Complete risk metrics response."""
    
    var: VaRResponse
    beta: BetaResponse
    volatility: VolatilityResponse
    stress_tests: list[StressTestResponse]
    risk_score: float
    risk_level: str
    calculated_at: str


@router.post("/metrics/var", response_model=APIResponse[VaRResponse])
async def calculate_var(
    data: RiskMetricsRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    risk_service: RiskMetricsService = Depends(get_risk_metrics_service_dep),
):
    """
    Calculate Value at Risk (VaR) and Conditional VaR.
    
    VaR represents the maximum expected loss at a given confidence level.
    CVaR (Expected Shortfall) is the expected loss beyond VaR.
    """
    try:
        result = risk_service.calculate_var(
            returns=data.portfolio_returns,
            portfolio_value=data.portfolio_value,
            method=data.var_method,
        )
        
        return APIResponse(
            data=VaRResponse(**result.to_dict()),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/metrics/beta", response_model=APIResponse[BetaResponse])
async def calculate_beta(
    data: RiskMetricsRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    risk_service: RiskMetricsService = Depends(get_risk_metrics_service_dep),
):
    """
    Calculate portfolio beta relative to benchmark.
    
    Beta measures systematic risk relative to the market.
    """
    if not data.benchmark_returns:
        # Use sample benchmark returns for demo
        data.benchmark_returns = risk_service.generate_benchmark_returns(
            len(data.portfolio_returns)
        ).tolist()
    
    try:
        result = risk_service.calculate_beta(
            portfolio_returns=data.portfolio_returns,
            benchmark_returns=data.benchmark_returns,
        )
        
        return APIResponse(
            data=BetaResponse(**result.to_dict()),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/metrics/volatility", response_model=APIResponse[VolatilityResponse])
async def calculate_volatility(
    data: RiskMetricsRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    risk_service: RiskMetricsService = Depends(get_risk_metrics_service_dep),
):
    """
    Calculate comprehensive volatility metrics.
    
    Includes daily, annualized, downside, and upside volatility.
    """
    try:
        result = risk_service.calculate_volatility(returns=data.portfolio_returns)
        
        return APIResponse(
            data=VolatilityResponse(**result.to_dict()),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class StressTestRequest(MaverickBaseModel):
    """Request for stress testing."""
    
    portfolio_beta: float = Field(ge=-2, le=5)
    portfolio_value: float = Field(gt=0)
    scenarios: list[str] | None = Field(default=None)


@router.post("/metrics/stress-test", response_model=APIResponse[list[StressTestResponse]])
async def run_stress_tests(
    data: StressTestRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    risk_service: RiskMetricsService = Depends(get_risk_metrics_service_dep),
):
    """
    Run stress tests for various market scenarios.
    
    Available scenarios:
    - market_drop_10: 10% correction
    - market_drop_20: Bear market
    - market_drop_30: Severe crash
    - financial_crisis_2008: 2008 crisis simulation
    - covid_crash_2020: COVID crash
    - tech_bubble_2000: Dot-com bubble
    - flash_crash: Flash crash
    """
    try:
        scenarios = None
        if data.scenarios:
            scenarios = [StressScenario(s) for s in data.scenarios]
        
        results = risk_service.run_stress_tests(
            portfolio_beta=data.portfolio_beta,
            portfolio_value=data.portfolio_value,
            scenarios=scenarios,
        )
        
        return APIResponse(
            data=[StressTestResponse(**r.to_dict()) for r in results],
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class CustomStressRequest(MaverickBaseModel):
    """Request for custom stress test."""
    
    portfolio_beta: float = Field(ge=-2, le=5)
    portfolio_value: float = Field(gt=0)
    market_drop_percent: float = Field(gt=0, le=100)
    scenario_name: str = Field(default="Custom Scenario")


@router.post("/metrics/stress-test/custom", response_model=APIResponse[StressTestResponse])
async def run_custom_stress_test(
    data: CustomStressRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    risk_service: RiskMetricsService = Depends(get_risk_metrics_service_dep),
):
    """
    Run a custom stress test with user-specified market drop.
    """
    result = risk_service.custom_stress_test(
        portfolio_beta=data.portfolio_beta,
        portfolio_value=data.portfolio_value,
        market_drop_percent=data.market_drop_percent,
        scenario_name=data.scenario_name,
    )
    
    return APIResponse(
        data=StressTestResponse(**result.to_dict()),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.post("/metrics/full", response_model=APIResponse[RiskMetricsSummaryResponse])
async def calculate_full_risk_metrics(
    data: RiskMetricsRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    risk_service: RiskMetricsService = Depends(get_risk_metrics_service_dep),
):
    """
    Calculate all risk metrics in one call.
    
    Returns VaR, Beta, Volatility, Stress Tests, and composite Risk Score.
    """
    if not data.benchmark_returns:
        data.benchmark_returns = risk_service.generate_benchmark_returns(
            len(data.portfolio_returns)
        ).tolist()
    
    try:
        result = risk_service.calculate_full_risk_metrics(
            portfolio_returns=data.portfolio_returns,
            benchmark_returns=data.benchmark_returns,
            portfolio_value=data.portfolio_value,
            var_method=data.var_method,
        )
        
        return APIResponse(
            data=RiskMetricsSummaryResponse(
                var=VaRResponse(**result.var.to_dict()),
                beta=BetaResponse(**result.beta.to_dict()),
                volatility=VolatilityResponse(**result.volatility.to_dict()),
                stress_tests=[StressTestResponse(**s.to_dict()) for s in result.stress_tests],
                risk_score=result.risk_score,
                risk_level=result.risk_level,
                calculated_at=result.calculated_at.isoformat(),
            ),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/metrics/scenarios")
async def get_available_scenarios(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get list of available stress test scenarios.
    """
    scenarios = []
    for scenario, params in STRESS_SCENARIOS.items():
        scenarios.append({
            "id": scenario.value,
            "name": params["name"],
            "description": params["description"],
            "market_return": params["market_return"],
            "duration_days": params["duration_days"],
        })
    
    return APIResponse(
        data=scenarios,
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )

