"""
AI-Enhanced Screening Endpoints.

Provides AI-generated explanations for screening results.
"""

from datetime import datetime, UTC
from decimal import Decimal
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import Field

from maverick_schemas.base import MaverickBaseModel
from maverick_schemas.responses import APIResponse, ResponseMeta
from maverick_schemas.auth import AuthenticatedUser
from maverick_services import (
    AIScreeningService,
    ExplanationRequest,
    StockExplanation,
    InvestorPersona,
    ConfidenceLevel,
)
from maverick_api.dependencies import get_db, get_current_user, get_request_id, get_redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-screening", tags=["AI Screening"])


# --- Response Models ---


class ExplanationResponse(MaverickBaseModel):
    """API response for stock explanation."""
    
    ticker: str = Field(description="Stock ticker")
    strategy: str = Field(description="Screening strategy")
    
    # AI content
    summary: str = Field(description="Investment case summary")
    technical_setup: str = Field(description="Technical analysis")
    key_signals: list[str] = Field(default_factory=list, description="Key signals")
    support_resistance: str | None = Field(default=None, description="Key levels")
    risk_factors: list[str] = Field(default_factory=list, description="Risk factors")
    
    # Metadata
    confidence: str = Field(description="Confidence level")
    persona: str | None = Field(default=None, description="Persona context")
    generated_at: str = Field(description="Generation timestamp")
    cached: bool = Field(default=False, description="Was cached")
    model_used: str | None = Field(default=None, description="LLM model used")


class BatchExplanationRequest(MaverickBaseModel):
    """Request for batch explanations."""
    
    tickers: list[str] = Field(min_length=1, max_length=20, description="Tickers to explain")
    strategy: str = Field(default="maverick", description="Screening strategy")
    persona: str | None = Field(default=None, description="Investor persona")


class UsageStatsResponse(MaverickBaseModel):
    """AI usage statistics."""
    
    user_id: str
    date: str
    explanations_used: int
    explanations_limit: int
    remaining: int


def _explanation_to_response(exp: StockExplanation) -> ExplanationResponse:
    """Convert service model to API response."""
    return ExplanationResponse(
        ticker=exp.ticker,
        strategy=exp.strategy,
        summary=exp.summary,
        technical_setup=exp.technical_setup,
        key_signals=exp.key_signals,
        support_resistance=exp.support_resistance,
        risk_factors=exp.risk_factors,
        confidence=exp.confidence.value if exp.confidence else "medium",
        persona=exp.persona.value if exp.persona else None,
        generated_at=exp.generated_at.isoformat() if exp.generated_at else "",
        cached=exp.cached,
        model_used=exp.model_used,
    )


# --- Dependencies ---


async def get_ai_service(
    redis=Depends(get_redis),
) -> AIScreeningService:
    """Get AI screening service with Redis."""
    return AIScreeningService(redis_client=redis)


# --- Endpoints ---


@router.get("/{strategy}/{ticker}/explain", response_model=APIResponse[ExplanationResponse])
async def get_stock_explanation(
    strategy: str,
    ticker: str,
    persona: str | None = Query(default=None, description="Investor persona"),
    force_refresh: bool = Query(default=False, description="Skip cache"),
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    ai_service: AIScreeningService = Depends(get_ai_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI-generated explanation for a screened stock.
    
    The explanation includes:
    - Investment case summary
    - Technical setup analysis
    - Key bullish/bearish signals
    - Support/resistance levels
    - Risk factors to watch
    
    Results are cached for 24 hours. Use force_refresh=true to regenerate.
    """
    # Validate strategy
    valid_strategies = ["maverick", "maverick_bear", "supply_demand_breakout"]
    if strategy not in valid_strategies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy. Must be one of: {valid_strategies}"
        )
    
    # Parse persona
    investor_persona = None
    if persona:
        try:
            investor_persona = InvestorPersona(persona.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid persona. Must be: conservative, moderate, aggressive"
            )
    
    # Fetch screening data for context (if available)
    screening_data = await _get_screening_data(db, ticker, strategy)
    
    # Build request
    request = ExplanationRequest(
        ticker=ticker.upper(),
        strategy=strategy,
        persona=investor_persona,
        **screening_data,
    )
    
    try:
        explanation = await ai_service.generate_explanation(
            request=request,
            user_id=user.user_id,
            tier=str(user.tier),
            force_refresh=force_refresh,
        )
        
        return APIResponse(
            data=_explanation_to_response(explanation),
            meta=ResponseMeta(
                request_id=request_id,
                timestamp=datetime.now(UTC),
            ),
        )
    except Exception as e:
        logger.error(f"Explanation generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate explanation")


@router.post("/explain-batch", response_model=APIResponse[list[ExplanationResponse]])
async def batch_explain_stocks(
    data: BatchExplanationRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    ai_service: AIScreeningService = Depends(get_ai_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate explanations for multiple stocks.
    
    Maximum 20 tickers per request. Results are cached individually.
    Rate limits apply per explanation.
    """
    # Parse persona
    investor_persona = None
    if data.persona:
        try:
            investor_persona = InvestorPersona(data.persona.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid persona. Must be: conservative, moderate, aggressive"
            )
    
    # Build requests
    requests = []
    for ticker in data.tickers:
        screening_data = await _get_screening_data(db, ticker, data.strategy)
        requests.append(ExplanationRequest(
            ticker=ticker.upper(),
            strategy=data.strategy,
            persona=investor_persona,
            **screening_data,
        ))
    
    try:
        explanations = await ai_service.generate_batch_explanations(
            requests=requests,
            user_id=user.user_id,
            tier=str(user.tier),
        )
        
        return APIResponse(
            data=[_explanation_to_response(exp) for exp in explanations],
            meta=ResponseMeta(
                request_id=request_id,
                timestamp=datetime.now(UTC),
            ),
        )
    except Exception as e:
        logger.error(f"Batch explanation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate explanations")


@router.get("/usage", response_model=APIResponse[UsageStatsResponse])
async def get_ai_usage_stats(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    ai_service: AIScreeningService = Depends(get_ai_service),
):
    """
    Get AI explanation usage statistics.
    
    Shows daily usage and remaining quota.
    """
    stats = await ai_service.get_usage_stats(user.user_id)
    
    if "error" in stats:
        raise HTTPException(status_code=500, detail=stats["error"])
    
    # Determine limit based on tier
    tier_limits = {"free": 5, "pro": 50, "enterprise": 500}
    limit = tier_limits.get(str(user.tier), 5)
    used = stats.get("explanations_used", 0)
    
    return APIResponse(
        data=UsageStatsResponse(
            user_id=user.user_id,
            date=stats.get("date", ""),
            explanations_used=used,
            explanations_limit=limit,
            remaining=max(0, limit - used),
        ),
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


# --- Helper Functions ---


async def _get_screening_data(
    db: AsyncSession,
    ticker: str,
    strategy: str,
) -> dict[str, Any]:
    """Fetch screening data for a ticker."""
    # Try to get from cached screening results
    try:
        from maverick_data.models import MaverickStocks, MaverickBearStocks
        from sqlalchemy import select
        
        ticker_upper = ticker.upper()
        
        if strategy == "maverick":
            result = await db.execute(
                select(MaverickStocks).where(MaverickStocks.ticker == ticker_upper)
            )
            stock = result.scalar_one_or_none()
            if stock:
                return {
                    "maverick_score": float(stock.maverick_score) if stock.maverick_score else None,
                    "momentum_score": float(stock.momentum_score) if hasattr(stock, 'momentum_score') and stock.momentum_score else None,
                    "current_price": float(stock.current_price) if stock.current_price else None,
                    "change_percent": float(stock.change_percent) if hasattr(stock, 'change_percent') and stock.change_percent else None,
                    "rsi": float(stock.rsi) if hasattr(stock, 'rsi') and stock.rsi else None,
                    "trend": str(stock.trend) if hasattr(stock, 'trend') and stock.trend else None,
                    "above_sma_50": bool(stock.above_sma_50) if hasattr(stock, 'above_sma_50') else False,
                    "above_sma_200": bool(stock.above_sma_200) if hasattr(stock, 'above_sma_200') else False,
                    "relative_volume": float(stock.relative_volume) if hasattr(stock, 'relative_volume') and stock.relative_volume else None,
                    "pattern": str(stock.pattern) if hasattr(stock, 'pattern') and stock.pattern else None,
                }
        
        elif strategy == "maverick_bear":
            result = await db.execute(
                select(MaverickBearStocks).where(MaverickBearStocks.ticker == ticker_upper)
            )
            stock = result.scalar_one_or_none()
            if stock:
                return {
                    "maverick_score": float(stock.maverick_score) if hasattr(stock, 'maverick_score') and stock.maverick_score else None,
                    "current_price": float(stock.current_price) if stock.current_price else None,
                    "rsi": float(stock.rsi) if hasattr(stock, 'rsi') and stock.rsi else None,
                    "trend": "bearish",
                }
    except Exception as e:
        logger.warning(f"Failed to fetch screening data for {ticker}: {e}")
    
    return {}

