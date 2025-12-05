"""
AI-Enhanced Stock Screening Service.

Provides AI-generated explanations for screening results, persona-based filtering,
and natural language stock discovery.
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, UTC
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class InvestorPersona(str, Enum):
    """Investor risk profiles for personalized screening."""
    
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class ConfidenceLevel(str, Enum):
    """AI explanation confidence level."""
    
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StockExplanation(BaseModel):
    """AI-generated explanation for a screened stock."""
    
    ticker: str = Field(description="Stock ticker")
    strategy: str = Field(description="Screening strategy")
    
    # AI-generated content
    summary: str = Field(description="2-3 sentence investment case")
    technical_setup: str = Field(description="Technical analysis summary")
    key_signals: list[str] = Field(default_factory=list, description="Key bullish/bearish signals")
    support_resistance: str | None = Field(default=None, description="Key levels context")
    risk_factors: list[str] = Field(default_factory=list, description="Risk factors to watch")
    
    # Confidence and metadata
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    persona: InvestorPersona | None = Field(default=None, description="Persona context")
    
    # Cache metadata
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    model_used: str | None = Field(default=None)
    cached: bool = Field(default=False)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }


class ExplanationRequest(BaseModel):
    """Request for stock explanation."""
    
    ticker: str
    strategy: str = "maverick"
    persona: InvestorPersona | None = None
    
    # Screening data (from MaverickStock)
    maverick_score: float | None = None
    momentum_score: float | None = None
    current_price: float | None = None
    change_percent: float | None = None
    rsi: float | None = None
    trend: str | None = None
    above_sma_50: bool = False
    above_sma_200: bool = False
    relative_volume: float | None = None
    pattern: str | None = None


# Rate limits per tier (explanations per day)
TIER_LIMITS = {
    "free": 5,
    "pro": 50,
    "enterprise": 500,
}

# Cache TTL in seconds (24 hours)
EXPLANATION_CACHE_TTL = 86400

# LLM timeout in seconds
LLM_TIMEOUT = 30


def _build_explanation_prompt(
    request: ExplanationRequest,
    persona: InvestorPersona | None = None,
) -> str:
    """Build the LLM prompt for generating explanations."""
    
    # Base context
    ticker = request.ticker.upper()
    strategy = request.strategy
    
    # Build metrics string
    metrics = []
    if request.maverick_score is not None:
        metrics.append(f"Maverick Score: {request.maverick_score:.1f}/100")
    if request.momentum_score is not None:
        metrics.append(f"Momentum Score: {request.momentum_score:.1f}")
    if request.rsi is not None:
        metrics.append(f"RSI: {request.rsi:.1f}")
    if request.current_price is not None:
        metrics.append(f"Price: ${request.current_price:.2f}")
    if request.change_percent is not None:
        sign = "+" if request.change_percent >= 0 else ""
        metrics.append(f"Change: {sign}{request.change_percent:.2f}%")
    if request.relative_volume is not None:
        metrics.append(f"Relative Volume: {request.relative_volume:.2f}x")
    if request.trend:
        metrics.append(f"Trend: {request.trend}")
    if request.above_sma_50:
        metrics.append("Above 50 SMA")
    if request.above_sma_200:
        metrics.append("Above 200 SMA")
    if request.pattern:
        metrics.append(f"Pattern: {request.pattern}")
    
    metrics_str = "\n".join(f"- {m}" for m in metrics) if metrics else "No metrics available"
    
    # Persona-specific instructions
    persona_context = ""
    if persona == InvestorPersona.CONSERVATIVE:
        persona_context = """
The investor is CONSERVATIVE - emphasize:
- Downside protection and risk management
- Stability and dividend potential
- Lower volatility characteristics
- Reasons this might NOT be suitable for conservative investors
"""
    elif persona == InvestorPersona.AGGRESSIVE:
        persona_context = """
The investor is AGGRESSIVE - emphasize:
- Upside potential and momentum
- Growth catalysts and breakout potential
- Why the risk/reward is attractive
- Entry timing and momentum signals
"""
    else:  # Moderate or None
        persona_context = """
The investor is MODERATE - provide balanced analysis:
- Both opportunities and risks
- Reasonable entry points
- Risk/reward assessment
- Suitability for core holdings
"""

    prompt = f"""Analyze {ticker} which was selected by the {strategy} screening strategy.

SCREENING DATA:
{metrics_str}

{persona_context}

Generate a concise explanation in JSON format:
{{
    "summary": "2-3 sentence investment case - why this stock was selected",
    "technical_setup": "Current technical picture in 2-3 sentences",
    "key_signals": ["Signal 1", "Signal 2", "Signal 3"],
    "support_resistance": "Key support/resistance levels if apparent from the data",
    "risk_factors": ["Risk 1", "Risk 2"],
    "confidence": "high/medium/low"
}}

Be specific and actionable. Reference the actual metrics provided. Keep it under 200 words total.
Return ONLY valid JSON, no markdown or explanation."""

    return prompt


def _build_fallback_explanation(request: ExplanationRequest) -> StockExplanation:
    """Generate a rule-based fallback explanation when LLM fails."""
    
    ticker = request.ticker.upper()
    strategy = request.strategy
    
    # Build summary based on available data
    summary_parts = [f"{ticker} was identified by the {strategy} screening strategy"]
    
    if request.maverick_score and request.maverick_score > 70:
        summary_parts.append("with a strong overall score")
    
    if request.trend == "bullish":
        summary_parts.append("showing bullish trend characteristics")
    elif request.trend == "bearish":
        summary_parts.append("showing bearish trend characteristics")
    
    summary = ". ".join(summary_parts) + "."
    
    # Technical setup
    tech_parts = []
    if request.rsi:
        if request.rsi < 30:
            tech_parts.append("RSI indicates oversold conditions")
        elif request.rsi > 70:
            tech_parts.append("RSI indicates overbought conditions")
        else:
            tech_parts.append(f"RSI at {request.rsi:.0f} suggests neutral momentum")
    
    if request.above_sma_50 and request.above_sma_200:
        tech_parts.append("Price is trading above both 50 and 200-day moving averages, indicating strength")
    elif request.above_sma_50:
        tech_parts.append("Price is above the 50-day moving average")
    
    technical_setup = ". ".join(tech_parts) if tech_parts else "Technical analysis pending."
    
    # Key signals
    key_signals = []
    if request.maverick_score and request.maverick_score > 80:
        key_signals.append(f"High Maverick score ({request.maverick_score:.0f})")
    if request.relative_volume and request.relative_volume > 1.5:
        key_signals.append(f"Above-average volume ({request.relative_volume:.1f}x)")
    if request.pattern:
        key_signals.append(f"Pattern detected: {request.pattern}")
    if request.above_sma_50:
        key_signals.append("Trading above 50 SMA")
    
    if not key_signals:
        key_signals = ["Screening criteria met"]
    
    # Risk factors
    risk_factors = [
        "Market conditions can change rapidly",
        "Past performance does not guarantee future results",
    ]
    if request.rsi and request.rsi > 70:
        risk_factors.insert(0, "Overbought RSI may lead to pullback")
    if request.relative_volume and request.relative_volume > 2:
        risk_factors.insert(0, "High volume may indicate volatility")
    
    return StockExplanation(
        ticker=ticker,
        strategy=strategy,
        summary=summary,
        technical_setup=technical_setup,
        key_signals=key_signals[:4],  # Max 4 signals
        support_resistance=None,
        risk_factors=risk_factors[:3],  # Max 3 risks
        confidence=ConfidenceLevel.LOW,
        persona=request.persona,
        generated_at=datetime.now(UTC),
        model_used="fallback",
        cached=False,
    )


class AIScreeningService:
    """
    AI-powered stock screening explanations.
    
    Provides:
    - AI-generated explanations for screened stocks
    - Persona-based customization
    - Caching with Redis
    - Graceful degradation on LLM failures
    - Tier-based rate limiting
    """
    
    def __init__(
        self,
        redis_client: Any | None = None,
        openrouter_api_key: str | None = None,
    ):
        """
        Initialize the AI screening service.
        
        Args:
            redis_client: Redis client for caching (optional)
            openrouter_api_key: OpenRouter API key (optional, uses env var)
        """
        self._redis = redis_client
        self._api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        self._llm = None
        
    def _get_llm(self):
        """Get or create LLM instance."""
        if self._llm is not None:
            return self._llm
            
        if not self._api_key:
            logger.warning("No OpenRouter API key available")
            return None
        
        try:
            from langchain_openai import ChatOpenAI
            
            # Use Claude 3.5 Haiku for cost-effective explanations
            self._llm = ChatOpenAI(
                model="anthropic/claude-3.5-haiku",
                temperature=0.3,
                max_tokens=1024,
                openai_api_base="https://openrouter.ai/api/v1",
                openai_api_key=self._api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com/wshobson/maverick-mcp",
                    "X-Title": "Maverick MCP",
                },
            )
            return self._llm
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            return None
    
    def _get_cache_key(
        self,
        ticker: str,
        strategy: str,
        persona: InvestorPersona | None = None,
    ) -> str:
        """Generate cache key for explanation."""
        parts = [ticker.upper(), strategy]
        if persona:
            parts.append(persona.value)
        key_str = ":".join(parts)
        return f"ai:explanation:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    async def _get_cached(self, cache_key: str) -> StockExplanation | None:
        """Get cached explanation if available."""
        if not self._redis:
            return None
            
        try:
            data = await self._redis.get(cache_key)
            if data:
                parsed = json.loads(data)
                explanation = StockExplanation(**parsed)
                explanation.cached = True
                return explanation
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
        
        return None
    
    async def _set_cached(
        self,
        cache_key: str,
        explanation: StockExplanation,
        ttl: int = EXPLANATION_CACHE_TTL,
    ) -> None:
        """Cache explanation."""
        if not self._redis:
            return
            
        try:
            data = explanation.model_dump_json()
            await self._redis.set(cache_key, data, ex=ttl)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
    
    async def _check_rate_limit(
        self,
        user_id: str,
        tier: str = "free",
    ) -> tuple[bool, int]:
        """
        Check if user has remaining quota.
        
        Returns:
            Tuple of (allowed, remaining_count)
        """
        if not self._redis:
            return True, -1  # No rate limiting without Redis
        
        limit = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        key = f"ai:ratelimit:{user_id}:{datetime.now(UTC).date().isoformat()}"
        
        try:
            count = await self._redis.get(key)
            current = int(count) if count else 0
            
            if current >= limit:
                return False, 0
            
            return True, limit - current
        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}")
            return True, -1
    
    async def _increment_usage(self, user_id: str) -> None:
        """Increment usage counter."""
        if not self._redis:
            return
            
        key = f"ai:ratelimit:{user_id}:{datetime.now(UTC).date().isoformat()}"
        
        try:
            await self._redis.incr(key)
            # Set expiry to end of day + buffer
            await self._redis.expire(key, 90000)  # ~25 hours
        except Exception as e:
            logger.warning(f"Usage increment failed: {e}")
    
    async def generate_explanation(
        self,
        request: ExplanationRequest,
        user_id: str | None = None,
        tier: str = "free",
        force_refresh: bool = False,
    ) -> StockExplanation:
        """
        Generate AI explanation for a screened stock.
        
        Args:
            request: Explanation request with stock data
            user_id: Optional user ID for rate limiting
            tier: User tier for rate limiting
            force_refresh: Skip cache and regenerate
            
        Returns:
            StockExplanation with AI-generated content
        """
        cache_key = self._get_cache_key(request.ticker, request.strategy, request.persona)
        
        # Check cache first (unless force_refresh)
        if not force_refresh:
            cached = await self._get_cached(cache_key)
            if cached:
                logger.debug(f"Cache hit for {request.ticker}")
                return cached
        
        # Check rate limit
        if user_id:
            allowed, remaining = await self._check_rate_limit(user_id, tier)
            if not allowed:
                logger.warning(f"Rate limit exceeded for user {user_id}")
                # Return fallback instead of error
                fallback = _build_fallback_explanation(request)
                fallback.summary = f"Rate limit reached. {fallback.summary}"
                return fallback
        
        # Try LLM generation
        llm = self._get_llm()
        if llm:
            try:
                explanation = await self._generate_with_llm(request, llm)
                if explanation:
                    # Increment usage
                    if user_id:
                        await self._increment_usage(user_id)
                    
                    # Cache result
                    await self._set_cached(cache_key, explanation)
                    
                    return explanation
            except Exception as e:
                logger.error(f"LLM generation failed for {request.ticker}: {e}")
        
        # Fallback to rule-based explanation
        logger.info(f"Using fallback explanation for {request.ticker}")
        fallback = _build_fallback_explanation(request)
        
        # Cache fallback with shorter TTL
        await self._set_cached(cache_key, fallback, ttl=3600)  # 1 hour
        
        return fallback
    
    async def _generate_with_llm(
        self,
        request: ExplanationRequest,
        llm: Any,
    ) -> StockExplanation | None:
        """Generate explanation using LLM."""
        from langchain_core.messages import HumanMessage, SystemMessage
        
        prompt = _build_explanation_prompt(request, request.persona)
        
        try:
            response = await asyncio.wait_for(
                llm.ainvoke([
                    SystemMessage(content=(
                        "You are a professional stock analyst providing concise, "
                        "actionable explanations for stock screening results. "
                        "Return ONLY valid JSON."
                    )),
                    HumanMessage(content=prompt),
                ]),
                timeout=LLM_TIMEOUT,
            )
            
            # Parse response
            content = response.content.strip()
            
            # Clean up potential markdown
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            data = json.loads(content)
            
            return StockExplanation(
                ticker=request.ticker.upper(),
                strategy=request.strategy,
                summary=data.get("summary", ""),
                technical_setup=data.get("technical_setup", ""),
                key_signals=data.get("key_signals", []),
                support_resistance=data.get("support_resistance"),
                risk_factors=data.get("risk_factors", []),
                confidence=ConfidenceLevel(data.get("confidence", "medium")),
                persona=request.persona,
                generated_at=datetime.now(UTC),
                model_used="anthropic/claude-3.5-haiku",
                cached=False,
            )
            
        except asyncio.TimeoutError:
            logger.warning(f"LLM timeout for {request.ticker}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return None
    
    async def generate_batch_explanations(
        self,
        requests: list[ExplanationRequest],
        user_id: str | None = None,
        tier: str = "free",
        max_concurrent: int = 5,
    ) -> list[StockExplanation]:
        """
        Generate explanations for multiple stocks.
        
        Args:
            requests: List of explanation requests
            user_id: Optional user ID for rate limiting
            tier: User tier
            max_concurrent: Maximum concurrent LLM calls
            
        Returns:
            List of explanations (some may be fallbacks)
        """
        # Use semaphore to limit concurrent calls
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_one(req: ExplanationRequest) -> StockExplanation:
            async with semaphore:
                return await self.generate_explanation(
                    req,
                    user_id=user_id,
                    tier=tier,
                )
        
        # Generate all in parallel (with concurrency limit)
        tasks = [generate_one(req) for req in requests]
        return await asyncio.gather(*tasks)
    
    async def get_usage_stats(self, user_id: str) -> dict[str, Any]:
        """Get usage statistics for a user."""
        if not self._redis:
            return {"error": "Redis not available"}
        
        today = datetime.now(UTC).date().isoformat()
        key = f"ai:ratelimit:{user_id}:{today}"
        
        try:
            count = await self._redis.get(key)
            current = int(count) if count else 0
            
            return {
                "user_id": user_id,
                "date": today,
                "explanations_used": current,
                "explanations_limit": TIER_LIMITS.get("free", 5),  # Would need tier
            }
        except Exception as e:
            return {"error": str(e)}


# Factory function for easy instantiation
def get_ai_screening_service(
    redis_client: Any | None = None,
) -> AIScreeningService:
    """Get configured AI screening service."""
    return AIScreeningService(redis_client=redis_client)

