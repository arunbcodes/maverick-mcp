"""
AI-Enhanced Screening Endpoints.

Provides AI-generated explanations and natural language search for screening results.
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
    NLScreeningService,
    ParsedQuery,
    QuerySuggestion,
    EXAMPLE_QUERIES,
    get_nl_screening_service,
    ThesisGeneratorService,
    InvestmentThesis,
    ThesisSection,
    ThesisRating,
    RiskLevel,
    get_thesis_service,
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
        from maverick_data.models import MaverickStocks, MaverickBearStocks, Stock
        from sqlalchemy import select
        
        ticker_upper = ticker.upper()
        
        if strategy == "maverick":
            # Join with Stock to filter by ticker_symbol
            result = await db.execute(
                select(MaverickStocks)
                .join(Stock, MaverickStocks.stock_id == Stock.stock_id)
                .where(Stock.ticker_symbol == ticker_upper)
                .order_by(MaverickStocks.date_analyzed.desc())
                .limit(1)
            )
            screening = result.scalar_one_or_none()
            if screening:
                return {
                    "combined_score": float(screening.combined_score) if screening.combined_score else None,
                    "momentum_score": float(screening.momentum_score) if screening.momentum_score else None,
                    "current_price": float(screening.close_price) if screening.close_price else None,
                    "pattern": str(screening.pattern_type) if screening.pattern_type else None,
                    "squeeze_status": str(screening.squeeze_status) if screening.squeeze_status else None,
                    "entry_signal": str(screening.entry_signal) if screening.entry_signal else None,
                }
        
        elif strategy == "maverick_bear":
            # Join with Stock to filter by ticker_symbol
            result = await db.execute(
                select(MaverickBearStocks)
                .join(Stock, MaverickBearStocks.stock_id == Stock.stock_id)
                .where(Stock.ticker_symbol == ticker_upper)
                .order_by(MaverickBearStocks.date_analyzed.desc())
                .limit(1)
            )
            screening = result.scalar_one_or_none()
            if screening:
                return {
                    "score": float(screening.score) if screening.score else None,
                    "current_price": float(screening.close_price) if screening.close_price else None,
                    "rsi": float(screening.rsi_14) if screening.rsi_14 else None,
                    "trend": "bearish",
                }
    except Exception as e:
        logger.warning(f"Failed to fetch screening data for {ticker}: {e}")
    
    return {}


# ============================================
# Natural Language Search Endpoints
# ============================================


class NLSearchRequest(MaverickBaseModel):
    """Natural language search request."""
    
    query: str = Field(min_length=3, max_length=500, description="Natural language query")
    persona: str | None = Field(default=None, description="Investor persona context")


class NLRefineRequest(MaverickBaseModel):
    """Request to refine an existing query."""
    
    current_query: str = Field(description="Current query")
    refinement: str = Field(description="Refinement to apply")


class ParsedQueryResponse(MaverickBaseModel):
    """Response with parsed query and interpretation."""
    
    original_query: str = Field(description="Original query")
    interpreted_as: str = Field(description="Human-readable interpretation")
    intent: str = Field(description="Detected intent")
    strategy: str = Field(description="Suggested screening strategy")
    confidence: float = Field(description="Parsing confidence 0-1")
    
    # Extracted criteria
    sectors: list[str] = Field(default_factory=list)
    tickers: list[str] = Field(default_factory=list)
    
    # Conditions
    rsi_condition: str | None = Field(default=None)
    sma_condition: str | None = Field(default=None)
    volume_condition: str | None = Field(default=None)
    
    # Filter summary
    filters: dict = Field(default_factory=dict, description="Extracted filter criteria")
    
    # Persona suggestion
    suggested_persona: str | None = Field(default=None)


class SuggestionResponse(MaverickBaseModel):
    """Query suggestion."""
    
    query: str
    description: str
    category: str


def _parsed_to_response(parsed: ParsedQuery) -> ParsedQueryResponse:
    """Convert ParsedQuery to API response."""
    return ParsedQueryResponse(
        original_query=parsed.original_query,
        interpreted_as=parsed.interpreted_as,
        intent=parsed.intent.value,
        strategy=parsed.strategy,
        confidence=parsed.confidence,
        sectors=parsed.sectors,
        tickers=parsed.tickers,
        rsi_condition=parsed.rsi_condition,
        sma_condition=parsed.sma_condition,
        volume_condition=parsed.volume_condition,
        filters={
            "min_price": str(parsed.filters.min_price) if parsed.filters.min_price else None,
            "max_price": str(parsed.filters.max_price) if parsed.filters.max_price else None,
            "min_rsi": str(parsed.filters.min_rsi) if parsed.filters.min_rsi else None,
            "max_rsi": str(parsed.filters.max_rsi) if parsed.filters.max_rsi else None,
            "above_sma_50": parsed.filters.above_sma_50,
            "above_sma_200": parsed.filters.above_sma_200,
            "sectors": parsed.filters.sectors,
        },
        suggested_persona=parsed.suggested_persona.value if parsed.suggested_persona else None,
    )


async def get_nl_service() -> NLScreeningService:
    """Get NL screening service."""
    return get_nl_screening_service(use_llm=True)


@router.post("/search", response_model=APIResponse[ParsedQueryResponse])
async def natural_language_search(
    data: NLSearchRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    nl_service: NLScreeningService = Depends(get_nl_service),
):
    """
    Search for stocks using natural language.
    
    Examples:
    - "Find tech stocks with strong momentum"
    - "Show me oversold stocks with RSI below 30"
    - "Healthcare stocks above 50 and 200 day moving average"
    - "High volume stocks under $50"
    
    Returns the interpreted query and extracted screening criteria.
    Use the returned criteria with the regular screening endpoints.
    """
    try:
        parsed = await nl_service.parse_query(data.query)
        
        return APIResponse(
            data=_parsed_to_response(parsed),
            meta=ResponseMeta(
                request_id=request_id,
                timestamp=datetime.now(UTC),
            ),
        )
    except Exception as e:
        logger.error(f"NL search failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse query")


@router.post("/search/refine", response_model=APIResponse[ParsedQueryResponse])
async def refine_search(
    data: NLRefineRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    nl_service: NLScreeningService = Depends(get_nl_service),
):
    """
    Refine an existing search with additional criteria.
    
    Examples:
    - Current: "Find tech stocks", Refinement: "Add healthcare too"
    - Current: "Oversold stocks", Refinement: "Only above $20"
    
    Combines the current query with the refinement.
    """
    try:
        parsed = await nl_service.refine_query(data.current_query, data.refinement)
        
        return APIResponse(
            data=_parsed_to_response(parsed),
            meta=ResponseMeta(
                request_id=request_id,
                timestamp=datetime.now(UTC),
            ),
        )
    except Exception as e:
        logger.error(f"Query refinement failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to refine query")


@router.get("/search/suggestions", response_model=APIResponse[list[SuggestionResponse]])
async def get_search_suggestions(
    q: str = Query(default="", description="Partial query for filtering"),
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    nl_service: NLScreeningService = Depends(get_nl_service),
):
    """
    Get search query suggestions for autocomplete.
    
    Returns example queries that match the partial input.
    """
    suggestions = nl_service.get_suggestions(q)
    
    return APIResponse(
        data=[
            SuggestionResponse(
                query=s.query,
                description=s.description,
                category=s.category,
            )
            for s in suggestions
        ],
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )


# ============================================
# Investment Thesis Endpoints
# ============================================


class ThesisSectionResponse(MaverickBaseModel):
    """Thesis section response."""
    
    title: str
    content: str
    bullet_points: list[str] = Field(default_factory=list)


class InvestmentThesisResponse(MaverickBaseModel):
    """Investment thesis API response."""
    
    ticker: str
    company_name: str | None = None
    generated_at: str
    persona: str | None = None
    
    # Summary
    summary: str
    rating: str
    risk_level: str
    confidence: float
    
    # Sections
    technical_setup: ThesisSectionResponse
    fundamental_story: ThesisSectionResponse
    catalysts: ThesisSectionResponse
    risks: ThesisSectionResponse
    
    # Price targets
    current_price: str | None = None
    price_target: str | None = None
    stop_loss: str | None = None
    upside_percent: float | None = None
    
    # Additional
    peer_comparison: list[str] = Field(default_factory=list)
    data_sources: list[str] = Field(default_factory=list)
    
    # Meta
    cached: bool = False
    model_used: str | None = None


def _thesis_to_response(thesis: InvestmentThesis) -> InvestmentThesisResponse:
    """Convert thesis to API response."""
    return InvestmentThesisResponse(
        ticker=thesis.ticker,
        company_name=thesis.company_name,
        generated_at=thesis.generated_at.isoformat() if thesis.generated_at else "",
        persona=thesis.persona.value if thesis.persona else None,
        summary=thesis.summary,
        rating=thesis.rating.value,
        risk_level=thesis.risk_level.value,
        confidence=thesis.confidence,
        technical_setup=ThesisSectionResponse(
            title=thesis.technical_setup.title,
            content=thesis.technical_setup.content,
            bullet_points=thesis.technical_setup.bullet_points,
        ),
        fundamental_story=ThesisSectionResponse(
            title=thesis.fundamental_story.title,
            content=thesis.fundamental_story.content,
            bullet_points=thesis.fundamental_story.bullet_points,
        ),
        catalysts=ThesisSectionResponse(
            title=thesis.catalysts.title,
            content=thesis.catalysts.content,
            bullet_points=thesis.catalysts.bullet_points,
        ),
        risks=ThesisSectionResponse(
            title=thesis.risks.title,
            content=thesis.risks.content,
            bullet_points=thesis.risks.bullet_points,
        ),
        current_price=str(thesis.current_price) if thesis.current_price else None,
        price_target=str(thesis.price_target) if thesis.price_target else None,
        stop_loss=str(thesis.stop_loss) if thesis.stop_loss else None,
        upside_percent=thesis.upside_percent,
        peer_comparison=thesis.peer_comparison,
        data_sources=thesis.data_sources,
        cached=thesis.cached,
        model_used=thesis.model_used,
    )


async def get_thesis_service_dep(
    redis=Depends(get_redis),
) -> ThesisGeneratorService:
    """Get thesis generator service."""
    return get_thesis_service(redis_client=redis)


@router.get("/thesis/{ticker}", response_model=APIResponse[InvestmentThesisResponse])
async def get_investment_thesis(
    ticker: str,
    persona: str | None = Query(default=None, description="Investor persona"),
    force_refresh: bool = Query(default=False, description="Skip cache"),
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    thesis_service: ThesisGeneratorService = Depends(get_thesis_service_dep),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate comprehensive investment thesis for a stock.
    
    Creates a detailed investment report including:
    - Executive summary with rating
    - Technical analysis
    - Fundamental analysis
    - Catalysts and upcoming events
    - Risk factors
    - Price targets and stop loss
    - Peer comparison
    
    The thesis is generated by Claude Opus for deep analysis and cached for 6 hours.
    Use `force_refresh=true` to regenerate.
    
    Personalization:
    - conservative: Focus on stability and downside protection
    - moderate: Balanced analysis (default)
    - aggressive: Focus on upside potential
    """
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
    
    # Fetch stock data and technicals
    stock_data = {}
    technicals = {}
    
    try:
        # Try to get stock info by joining MaverickStocks with Stock
        from maverick_data.models import MaverickStocks, Stock
        from sqlalchemy import select
        
        ticker_upper = ticker.upper()
        
        # First get the Stock info
        stock_result = await db.execute(
            select(Stock).where(Stock.ticker_symbol == ticker_upper)
        )
        stock_info = stock_result.scalar_one_or_none()
        
        # Then get the latest screening data
        screening_result = await db.execute(
            select(MaverickStocks)
            .join(Stock, MaverickStocks.stock_id == Stock.stock_id)
            .where(Stock.ticker_symbol == ticker_upper)
            .order_by(MaverickStocks.date_analyzed.desc())
            .limit(1)
        )
        screening = screening_result.scalar_one_or_none()
        
        if stock_info:
            stock_data = {
                "name": stock_info.company_name,
                "price": float(screening.close_price) if screening and screening.close_price else None,
                "sector": stock_info.sector,
            }
        if screening:
            technicals = {
                "momentum_score": float(screening.momentum_score) if screening.momentum_score else None,
                "pattern": str(screening.pattern_type) if screening.pattern_type else None,
                "squeeze_status": str(screening.squeeze_status) if screening.squeeze_status else None,
            }
    except Exception as e:
        logger.warning(f"Failed to fetch stock data for thesis: {e}")
    
    try:
        thesis = await thesis_service.generate_thesis(
            ticker=ticker,
            stock_data=stock_data,
            technicals=technicals,
            persona=investor_persona,
            force_refresh=force_refresh,
        )
        
        return APIResponse(
            data=_thesis_to_response(thesis),
            meta=ResponseMeta(
                request_id=request_id,
                timestamp=datetime.now(UTC),
            ),
        )
    except Exception as e:
        logger.error(f"Thesis generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate thesis")

