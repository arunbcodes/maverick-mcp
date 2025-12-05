"""
Investment Thesis Generation Service.

Generates comprehensive investment thesis for stocks by synthesizing
technical analysis, fundamentals, news sentiment, and peer comparison.
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

from maverick_services.ai_screening_service import InvestorPersona

logger = logging.getLogger(__name__)


class ThesisRating(str, Enum):
    """Investment thesis rating."""
    
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class RiskLevel(str, Enum):
    """Risk level assessment."""
    
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ThesisSection(BaseModel):
    """A section of the investment thesis."""
    
    title: str = Field(description="Section title")
    content: str = Field(description="Section content")
    bullet_points: list[str] = Field(default_factory=list, description="Key bullet points")


class InvestmentThesis(BaseModel):
    """Comprehensive investment thesis for a stock."""
    
    # Metadata
    ticker: str = Field(description="Stock ticker")
    company_name: str | None = Field(default=None, description="Company name")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    persona: InvestorPersona | None = Field(default=None, description="Persona context")
    
    # Executive summary
    summary: str = Field(description="2-3 sentence investment case")
    rating: ThesisRating = Field(description="Overall rating")
    risk_level: RiskLevel = Field(description="Risk assessment")
    confidence: float = Field(ge=0, le=1, description="Thesis confidence")
    
    # Main sections
    technical_setup: ThesisSection = Field(description="Technical analysis")
    fundamental_story: ThesisSection = Field(description="Fundamental analysis")
    catalysts: ThesisSection = Field(description="Upcoming catalysts")
    risks: ThesisSection = Field(description="Risk factors")
    
    # Price targets
    current_price: Decimal | None = Field(default=None)
    price_target: Decimal | None = Field(default=None)
    stop_loss: Decimal | None = Field(default=None)
    upside_percent: float | None = Field(default=None)
    
    # Comparative analysis
    peer_comparison: list[str] = Field(default_factory=list, description="Comparison to peers")
    
    # Sources used
    data_sources: list[str] = Field(default_factory=list, description="Data sources used")
    
    # Cache info
    cached: bool = Field(default=False)
    model_used: str | None = Field(default=None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }


# Cache TTL in seconds (6 hours)
THESIS_CACHE_TTL = 21600

# LLM timeout (thesis is more complex)
LLM_TIMEOUT = 60


def _build_thesis_prompt(
    ticker: str,
    stock_data: dict,
    technicals: dict | None = None,
    news_sentiment: dict | None = None,
    persona: InvestorPersona | None = None,
) -> str:
    """Build the prompt for thesis generation."""
    
    # Build context from available data
    context_parts = []
    
    # Stock info
    if stock_data:
        info_parts = []
        if stock_data.get("name"):
            info_parts.append(f"Company: {stock_data['name']}")
        if stock_data.get("sector"):
            info_parts.append(f"Sector: {stock_data['sector']}")
        if stock_data.get("market_cap"):
            info_parts.append(f"Market Cap: ${stock_data['market_cap']:,.0f}")
        if stock_data.get("pe_ratio"):
            info_parts.append(f"P/E Ratio: {stock_data['pe_ratio']:.1f}")
        if stock_data.get("dividend_yield"):
            info_parts.append(f"Dividend Yield: {stock_data['dividend_yield']:.2%}")
        if stock_data.get("price"):
            info_parts.append(f"Current Price: ${stock_data['price']:.2f}")
        if info_parts:
            context_parts.append("COMPANY INFO:\n" + "\n".join(info_parts))
    
    # Technical data
    if technicals:
        tech_parts = []
        if technicals.get("rsi"):
            tech_parts.append(f"RSI: {technicals['rsi']:.1f}")
        if technicals.get("macd"):
            macd = technicals["macd"]
            tech_parts.append(f"MACD: {macd.get('signal', 'N/A')}")
        if technicals.get("trend"):
            tech_parts.append(f"Trend: {technicals['trend']}")
        if technicals.get("support_levels"):
            tech_parts.append(f"Support: {technicals['support_levels']}")
        if technicals.get("resistance_levels"):
            tech_parts.append(f"Resistance: {technicals['resistance_levels']}")
        if tech_parts:
            context_parts.append("TECHNICAL ANALYSIS:\n" + "\n".join(tech_parts))
    
    # News sentiment
    if news_sentiment:
        sentiment_parts = []
        if news_sentiment.get("overall_sentiment"):
            sentiment_parts.append(f"Overall: {news_sentiment['overall_sentiment']}")
        if news_sentiment.get("sentiment_score"):
            sentiment_parts.append(f"Score: {news_sentiment['sentiment_score']}")
        if news_sentiment.get("recent_headlines"):
            headlines = news_sentiment["recent_headlines"][:3]
            sentiment_parts.append(f"Recent headlines: {', '.join(headlines)}")
        if sentiment_parts:
            context_parts.append("NEWS SENTIMENT:\n" + "\n".join(sentiment_parts))
    
    context = "\n\n".join(context_parts) if context_parts else "Limited data available"
    
    # Persona-specific instructions
    persona_context = ""
    if persona == InvestorPersona.CONSERVATIVE:
        persona_context = """
Target audience: CONSERVATIVE investor
- Emphasize stability, dividend history, downside protection
- Be more cautious in risk assessment
- Focus on long-term value rather than short-term momentum
- Highlight why this might NOT be suitable if risks are high
"""
    elif persona == InvestorPersona.AGGRESSIVE:
        persona_context = """
Target audience: AGGRESSIVE investor
- Focus on upside potential and momentum
- Emphasize growth catalysts and breakout potential
- Be open to higher-risk, higher-reward scenarios
- Highlight entry timing and momentum signals
"""
    else:
        persona_context = """
Target audience: MODERATE investor
- Provide balanced analysis of risk and reward
- Consider both growth potential and downside protection
- Focus on risk-adjusted returns
"""

    prompt = f"""Generate a comprehensive investment thesis for {ticker}.

{context}

{persona_context}

Return a JSON object with this structure:
{{
    "summary": "2-3 sentence investment case",
    "rating": "strong_buy|buy|hold|sell|strong_sell",
    "risk_level": "low|moderate|high|very_high",
    "confidence": 0.0-1.0,
    "technical_setup": {{
        "title": "Technical Setup",
        "content": "2-3 paragraph technical analysis",
        "bullet_points": ["Key technical point 1", "Key technical point 2"]
    }},
    "fundamental_story": {{
        "title": "Fundamental Analysis",
        "content": "2-3 paragraph fundamental analysis",
        "bullet_points": ["Key fundamental point 1", "Key fundamental point 2"]
    }},
    "catalysts": {{
        "title": "Catalysts & Outlook",
        "content": "Upcoming events and catalysts",
        "bullet_points": ["Catalyst 1", "Catalyst 2"]
    }},
    "risks": {{
        "title": "Risk Factors",
        "content": "Key risks to consider",
        "bullet_points": ["Risk 1", "Risk 2", "Risk 3"]
    }},
    "price_target": number or null,
    "stop_loss": number or null,
    "peer_comparison": ["Comparison point 1", "Comparison point 2"],
    "data_sources": ["Source 1", "Source 2"]
}}

Be specific, actionable, and reference actual data when available.
Total thesis should be 500-1000 words.
Return ONLY valid JSON, no markdown or explanation."""

    return prompt


def _build_fallback_thesis(
    ticker: str,
    stock_data: dict,
) -> InvestmentThesis:
    """Generate a basic fallback thesis when LLM fails."""
    
    price = stock_data.get("price")
    
    return InvestmentThesis(
        ticker=ticker.upper(),
        company_name=stock_data.get("name"),
        summary=f"{ticker} requires further analysis. Limited data available for comprehensive thesis generation.",
        rating=ThesisRating.HOLD,
        risk_level=RiskLevel.MODERATE,
        confidence=0.3,
        technical_setup=ThesisSection(
            title="Technical Setup",
            content="Technical analysis unavailable. Consider reviewing charts manually.",
            bullet_points=["Review price action on charts", "Check volume patterns"],
        ),
        fundamental_story=ThesisSection(
            title="Fundamental Analysis",
            content="Fundamental data incomplete. Recommend reviewing financial statements.",
            bullet_points=["Review latest earnings", "Check valuation metrics"],
        ),
        catalysts=ThesisSection(
            title="Catalysts",
            content="Upcoming catalysts unclear. Monitor news and earnings calendar.",
            bullet_points=["Check earnings date", "Monitor sector trends"],
        ),
        risks=ThesisSection(
            title="Risk Factors",
            content="Standard market risks apply. Conduct thorough due diligence.",
            bullet_points=[
                "Market volatility risk",
                "Sector-specific risks",
                "Company-specific risks",
            ],
        ),
        current_price=Decimal(str(price)) if price else None,
        data_sources=["Limited data available"],
        cached=False,
        model_used="fallback",
    )


class ThesisGeneratorService:
    """
    Investment thesis generation service.
    
    Creates comprehensive investment reports by synthesizing:
    - Technical analysis
    - Fundamental data
    - News sentiment
    - Peer comparison
    """
    
    def __init__(
        self,
        redis_client: Any | None = None,
        openrouter_api_key: str | None = None,
    ):
        """
        Initialize thesis generator service.
        
        Args:
            redis_client: Redis client for caching
            openrouter_api_key: OpenRouter API key
        """
        self._redis = redis_client
        self._api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        self._llm = None
    
    def _get_llm(self):
        """Get or create LLM instance."""
        if self._llm is not None:
            return self._llm
        
        if not self._api_key:
            return None
        
        try:
            from langchain_openai import ChatOpenAI
            
            # Use Claude Opus for deep analysis
            self._llm = ChatOpenAI(
                model="anthropic/claude-opus-4",
                temperature=0.3,
                max_tokens=4096,
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
    
    def _get_cache_key(self, ticker: str, persona: InvestorPersona | None = None) -> str:
        """Generate cache key."""
        parts = [ticker.upper()]
        if persona:
            parts.append(persona.value)
        key_str = ":".join(parts)
        return f"thesis:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    async def _get_cached(self, cache_key: str) -> InvestmentThesis | None:
        """Get cached thesis."""
        if not self._redis:
            return None
        
        try:
            data = await self._redis.get(cache_key)
            if data:
                parsed = json.loads(data)
                thesis = InvestmentThesis(**parsed)
                thesis.cached = True
                return thesis
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
        
        return None
    
    async def _set_cached(self, cache_key: str, thesis: InvestmentThesis) -> None:
        """Cache thesis."""
        if not self._redis:
            return
        
        try:
            data = thesis.model_dump_json()
            await self._redis.set(cache_key, data, ex=THESIS_CACHE_TTL)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
    
    async def generate_thesis(
        self,
        ticker: str,
        stock_data: dict | None = None,
        technicals: dict | None = None,
        news_sentiment: dict | None = None,
        persona: InvestorPersona | None = None,
        force_refresh: bool = False,
    ) -> InvestmentThesis:
        """
        Generate comprehensive investment thesis.
        
        Args:
            ticker: Stock ticker
            stock_data: Stock info dict
            technicals: Technical analysis dict
            news_sentiment: News sentiment dict
            persona: Investor persona for tailored analysis
            force_refresh: Skip cache
            
        Returns:
            InvestmentThesis with comprehensive analysis
        """
        ticker = ticker.upper()
        cache_key = self._get_cache_key(ticker, persona)
        
        # Check cache
        if not force_refresh:
            cached = await self._get_cached(cache_key)
            if cached:
                logger.debug(f"Cache hit for thesis: {ticker}")
                return cached
        
        # Try LLM generation
        llm = self._get_llm()
        if llm:
            try:
                thesis = await self._generate_with_llm(
                    ticker=ticker,
                    stock_data=stock_data or {},
                    technicals=technicals,
                    news_sentiment=news_sentiment,
                    persona=persona,
                    llm=llm,
                )
                if thesis:
                    await self._set_cached(cache_key, thesis)
                    return thesis
            except Exception as e:
                logger.error(f"LLM thesis generation failed: {e}")
        
        # Fallback
        logger.info(f"Using fallback thesis for {ticker}")
        fallback = _build_fallback_thesis(ticker, stock_data or {})
        await self._set_cached(cache_key, fallback)
        return fallback
    
    async def _generate_with_llm(
        self,
        ticker: str,
        stock_data: dict,
        technicals: dict | None,
        news_sentiment: dict | None,
        persona: InvestorPersona | None,
        llm: Any,
    ) -> InvestmentThesis | None:
        """Generate thesis using LLM."""
        from langchain_core.messages import HumanMessage, SystemMessage
        
        prompt = _build_thesis_prompt(
            ticker=ticker,
            stock_data=stock_data,
            technicals=technicals,
            news_sentiment=news_sentiment,
            persona=persona,
        )
        
        try:
            response = await asyncio.wait_for(
                llm.ainvoke([
                    SystemMessage(content=(
                        "You are a professional equity research analyst. "
                        "Generate comprehensive, balanced investment thesis reports. "
                        "Be specific and data-driven. Return ONLY valid JSON."
                    )),
                    HumanMessage(content=prompt),
                ]),
                timeout=LLM_TIMEOUT,
            )
            
            content = response.content.strip()
            
            # Clean up markdown
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            data = json.loads(content)
            
            # Build thesis from response
            current_price = stock_data.get("price")
            price_target = data.get("price_target")
            
            # Calculate upside
            upside = None
            if current_price and price_target:
                upside = ((price_target - current_price) / current_price) * 100
            
            return InvestmentThesis(
                ticker=ticker,
                company_name=stock_data.get("name"),
                summary=data.get("summary", ""),
                rating=ThesisRating(data.get("rating", "hold")),
                risk_level=RiskLevel(data.get("risk_level", "moderate")),
                confidence=data.get("confidence", 0.7),
                technical_setup=ThesisSection(**data.get("technical_setup", {
                    "title": "Technical Setup",
                    "content": "Technical analysis unavailable",
                    "bullet_points": [],
                })),
                fundamental_story=ThesisSection(**data.get("fundamental_story", {
                    "title": "Fundamental Analysis",
                    "content": "Fundamental analysis unavailable",
                    "bullet_points": [],
                })),
                catalysts=ThesisSection(**data.get("catalysts", {
                    "title": "Catalysts",
                    "content": "Catalyst analysis unavailable",
                    "bullet_points": [],
                })),
                risks=ThesisSection(**data.get("risks", {
                    "title": "Risk Factors",
                    "content": "Risk analysis unavailable",
                    "bullet_points": [],
                })),
                current_price=Decimal(str(current_price)) if current_price else None,
                price_target=Decimal(str(price_target)) if price_target else None,
                stop_loss=Decimal(str(data["stop_loss"])) if data.get("stop_loss") else None,
                upside_percent=upside,
                peer_comparison=data.get("peer_comparison", []),
                data_sources=data.get("data_sources", ["AI Analysis"]),
                persona=persona,
                cached=False,
                model_used="anthropic/claude-opus-4",
            )
            
        except asyncio.TimeoutError:
            logger.warning(f"LLM timeout for thesis: {ticker}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse thesis response: {e}")
            return None
        except Exception as e:
            logger.error(f"Thesis generation error: {e}")
            return None


def get_thesis_service(
    redis_client: Any | None = None,
) -> ThesisGeneratorService:
    """Get configured thesis generator service."""
    return ThesisGeneratorService(redis_client=redis_client)


__all__ = [
    "ThesisGeneratorService",
    "InvestmentThesis",
    "ThesisSection",
    "ThesisRating",
    "RiskLevel",
    "get_thesis_service",
]

