"""
Natural Language Screening Service.

Parses natural language queries into structured screening criteria.
Enables users to find stocks using plain English queries like:
"Find tech stocks with strong momentum breaking out of bases"
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime, UTC
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from maverick_schemas.screening import ScreeningFilter
from maverick_services.ai_screening_service import InvestorPersona
from maverick_core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class QueryIntent(str, Enum):
    """Detected intent from natural language query."""
    
    FIND_BULLISH = "find_bullish"
    FIND_BEARISH = "find_bearish"
    FIND_BREAKOUT = "find_breakout"
    FIND_OVERSOLD = "find_oversold"
    FIND_OVERBOUGHT = "find_overbought"
    FIND_DIVIDEND = "find_dividend"
    FIND_VALUE = "find_value"
    FIND_MOMENTUM = "find_momentum"
    COMPARE = "compare"
    GENERAL = "general"


class ParsedQuery(BaseModel):
    """Structured representation of a parsed natural language query."""
    
    # Original query
    original_query: str = Field(description="Original user query")
    
    # Interpreted intent
    intent: QueryIntent = Field(default=QueryIntent.GENERAL, description="Detected intent")
    interpreted_as: str = Field(description="Human-readable interpretation")
    
    # Extracted criteria
    strategy: str = Field(default="maverick", description="Screening strategy to use")
    filters: ScreeningFilter = Field(default_factory=ScreeningFilter, description="Extracted filters")
    
    # Extracted entities
    sectors: list[str] = Field(default_factory=list, description="Mentioned sectors")
    tickers: list[str] = Field(default_factory=list, description="Specific tickers mentioned")
    
    # Technical conditions
    rsi_condition: str | None = Field(default=None, description="RSI condition")
    sma_condition: str | None = Field(default=None, description="Moving average condition")
    volume_condition: str | None = Field(default=None, description="Volume condition")
    
    # Confidence
    confidence: float = Field(default=0.8, ge=0, le=1, description="Parsing confidence")
    
    # Persona suggestion
    suggested_persona: InvestorPersona | None = Field(default=None, description="Suggested persona")


class QuerySuggestion(BaseModel):
    """Suggested query for autocomplete."""
    
    query: str
    description: str
    category: str


# Common query patterns for rule-based parsing
SECTOR_KEYWORDS = {
    "tech": "Technology",
    "technology": "Technology",
    "software": "Technology",
    "healthcare": "Healthcare",
    "health": "Healthcare",
    "biotech": "Healthcare",
    "pharma": "Healthcare",
    "financial": "Financial Services",
    "finance": "Financial Services",
    "bank": "Financial Services",
    "banking": "Financial Services",
    "energy": "Energy",
    "oil": "Energy",
    "gas": "Energy",
    "consumer": "Consumer Cyclical",
    "retail": "Consumer Cyclical",
    "industrial": "Industrials",
    "manufacturing": "Industrials",
    "real estate": "Real Estate",
    "reit": "Real Estate",
    "utilities": "Utilities",
    "telecom": "Communication Services",
    "communication": "Communication Services",
    "materials": "Basic Materials",
}

INTENT_PATTERNS = {
    QueryIntent.FIND_BULLISH: [
        r"bullish", r"buy", r"long", r"strong", r"momentum", r"uptrend",
        r"breaking out", r"breakout", r"rally", r"rising",
    ],
    QueryIntent.FIND_BEARISH: [
        r"bearish", r"short", r"weak", r"downtrend", r"falling",
        r"declining", r"breaking down", r"sell",
    ],
    QueryIntent.FIND_BREAKOUT: [
        r"breakout", r"breaking.*resistance", r"breaking.*out",
        r"new high", r"52.?week high", r"base",
    ],
    QueryIntent.FIND_OVERSOLD: [
        r"oversold", r"rsi.*low", r"rsi.*below", r"beaten.?down",
        r"cheap", r"discount", r"undervalued",
    ],
    QueryIntent.FIND_OVERBOUGHT: [
        r"overbought", r"rsi.*high", r"rsi.*above.*70",
        r"extended", r"overvalued",
    ],
    QueryIntent.FIND_DIVIDEND: [
        r"dividend", r"yield", r"income", r"payout",
    ],
    QueryIntent.FIND_VALUE: [
        r"value", r"p/e.*low", r"pe.*low", r"undervalued",
        r"cheap.*fundamentals",
    ],
    QueryIntent.FIND_MOMENTUM: [
        r"momentum", r"high.*volume", r"relative.*strength",
        r"trending", r"moving.*average",
    ],
}

# Example queries for suggestions
EXAMPLE_QUERIES: list[QuerySuggestion] = [
    QuerySuggestion(
        query="Find tech stocks with strong momentum",
        description="Technology sector with high momentum score",
        category="Sector + Momentum",
    ),
    QuerySuggestion(
        query="Show me oversold stocks with RSI below 30",
        description="Stocks in oversold territory",
        category="Technical",
    ),
    QuerySuggestion(
        query="Stocks breaking out above resistance",
        description="Breakout candidates",
        category="Breakout",
    ),
    QuerySuggestion(
        query="Healthcare stocks above 50 and 200 day moving average",
        description="Healthcare with strong technical setup",
        category="Sector + Technical",
    ),
    QuerySuggestion(
        query="High volume stocks under $50",
        description="Affordable stocks with institutional interest",
        category="Price + Volume",
    ),
    QuerySuggestion(
        query="Dividend stocks in financial sector",
        description="Income-generating financials",
        category="Sector + Dividend",
    ),
    QuerySuggestion(
        query="Small cap momentum plays",
        description="Smaller companies with momentum",
        category="Market Cap + Momentum",
    ),
    QuerySuggestion(
        query="Conservative low volatility stocks",
        description="Stable, lower-risk opportunities",
        category="Risk Profile",
    ),
]

# LLM timeout
LLM_TIMEOUT = 15


class NLScreeningService:
    """
    Natural language stock screening service.
    
    Parses plain English queries into structured screening criteria.
    Uses a hybrid approach:
    1. Rule-based parsing for common patterns (fast)
    2. LLM parsing for complex queries (slower, more accurate)
    """
    
    def __init__(
        self,
        openrouter_api_key: str | None = None,
        use_llm: bool = True,
    ):
        """
        Initialize the NL screening service.
        
        Args:
            openrouter_api_key: OpenRouter API key (optional, uses env var)
            use_llm: Whether to use LLM for complex queries
        """
        self._api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        self._use_llm = use_llm and bool(self._api_key)
        self._llm = None
    
    def _get_llm(self):
        """Get or create LLM instance."""
        if self._llm is not None:
            return self._llm
        
        if not self._api_key:
            return None
        
        try:
            from langchain_openai import ChatOpenAI
            
            # Use Claude Sonnet for accurate query parsing
            self._llm = ChatOpenAI(
                model="anthropic/claude-sonnet-4",
                temperature=0.1,  # Low temperature for consistent parsing
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
    
    async def parse_query(self, query: str) -> ParsedQuery:
        """
        Parse a natural language query into screening criteria.
        
        Args:
            query: Natural language query
            
        Returns:
            ParsedQuery with structured criteria
        """
        query = query.strip()
        if not query:
            return ParsedQuery(
                original_query=query,
                interpreted_as="Empty query",
                confidence=0.0,
            )
        
        # Try rule-based parsing first (fast)
        rule_based = self._parse_with_rules(query)
        
        # If rule-based parsing has high confidence, use it
        if rule_based.confidence >= 0.8:
            logger.debug(f"Using rule-based parsing for: {query}")
            return rule_based
        
        # Otherwise, try LLM parsing for complex queries
        if self._use_llm:
            llm_parsed = await self._parse_with_llm(query)
            if llm_parsed and llm_parsed.confidence > rule_based.confidence:
                logger.debug(f"Using LLM parsing for: {query}")
                return llm_parsed
        
        # Fall back to rule-based
        return rule_based
    
    def _parse_with_rules(self, query: str) -> ParsedQuery:
        """
        Parse query using rule-based patterns.
        
        Fast but limited to common patterns.
        """
        query_lower = query.lower()
        
        # Detect intent
        intent = QueryIntent.GENERAL
        for possible_intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    intent = possible_intent
                    break
            if intent != QueryIntent.GENERAL:
                break
        
        # Extract sectors
        sectors = []
        for keyword, sector in SECTOR_KEYWORDS.items():
            if keyword in query_lower:
                if sector not in sectors:
                    sectors.append(sector)
        
        # Extract price constraints
        min_price = None
        max_price = None
        
        # "under $50", "below $100"
        price_under = re.search(r"(?:under|below|less than)\s*\$?(\d+)", query_lower)
        if price_under:
            max_price = Decimal(price_under.group(1))
        
        # "above $10", "over $20"
        price_above = re.search(r"(?:above|over|more than)\s*\$?(\d+)", query_lower)
        if price_above:
            min_price = Decimal(price_above.group(1))
        
        # "between $10 and $50"
        price_between = re.search(r"between\s*\$?(\d+)\s*(?:and|to|-)\s*\$?(\d+)", query_lower)
        if price_between:
            min_price = Decimal(price_between.group(1))
            max_price = Decimal(price_between.group(2))
        
        # Extract RSI conditions
        rsi_condition = None
        min_rsi = None
        max_rsi = None
        
        rsi_below = re.search(r"rsi\s*(?:below|under|<)\s*(\d+)", query_lower)
        if rsi_below:
            max_rsi = Decimal(rsi_below.group(1))
            rsi_condition = f"RSI below {rsi_below.group(1)}"
        
        rsi_above = re.search(r"rsi\s*(?:above|over|>)\s*(\d+)", query_lower)
        if rsi_above:
            min_rsi = Decimal(rsi_above.group(1))
            rsi_condition = f"RSI above {rsi_above.group(1)}"
        
        # Handle "oversold" / "overbought"
        if "oversold" in query_lower and not max_rsi:
            max_rsi = Decimal("30")
            rsi_condition = "RSI below 30 (oversold)"
        if "overbought" in query_lower and not min_rsi:
            min_rsi = Decimal("70")
            rsi_condition = "RSI above 70 (overbought)"
        
        # Extract SMA conditions
        sma_condition = None
        above_sma_50 = None
        above_sma_200 = None
        
        if re.search(r"above.*50\s*(?:day|sma|ma)", query_lower) or \
           re.search(r"50\s*(?:day|sma|ma).*above", query_lower):
            above_sma_50 = True
            sma_condition = "Above 50 SMA"
        
        if re.search(r"above.*200\s*(?:day|sma|ma)", query_lower) or \
           re.search(r"200\s*(?:day|sma|ma).*above", query_lower):
            above_sma_200 = True
            sma_condition = "Above 200 SMA" if not sma_condition else "Above 50 & 200 SMA"
        
        if "moving average" in query_lower and not above_sma_50:
            above_sma_50 = True
            sma_condition = "Above moving averages"
        
        # Volume condition
        volume_condition = None
        if re.search(r"high\s*volume", query_lower):
            volume_condition = "High relative volume"
        
        # Determine strategy based on intent
        strategy = "maverick"
        if intent == QueryIntent.FIND_BEARISH:
            strategy = "maverick_bear"
        elif intent == QueryIntent.FIND_BREAKOUT:
            strategy = "supply_demand_breakout"
        
        # Build filter
        filters = ScreeningFilter(
            min_price=min_price,
            max_price=max_price,
            min_rsi=min_rsi,
            max_rsi=max_rsi,
            above_sma_50=above_sma_50,
            above_sma_200=above_sma_200,
            sectors=sectors if sectors else None,
        )
        
        # Build interpretation
        parts = []
        if sectors:
            parts.append(f"in {', '.join(sectors)} sector(s)")
        if min_price or max_price:
            if min_price and max_price:
                parts.append(f"priced ${min_price}-${max_price}")
            elif min_price:
                parts.append(f"above ${min_price}")
            else:
                parts.append(f"under ${max_price}")
        if rsi_condition:
            parts.append(f"with {rsi_condition}")
        if sma_condition:
            parts.append(sma_condition.lower())
        if volume_condition:
            parts.append(f"with {volume_condition.lower()}")
        
        intent_descriptions = {
            QueryIntent.FIND_BULLISH: "Finding bullish stocks",
            QueryIntent.FIND_BEARISH: "Finding bearish/short opportunities",
            QueryIntent.FIND_BREAKOUT: "Finding breakout candidates",
            QueryIntent.FIND_OVERSOLD: "Finding oversold stocks",
            QueryIntent.FIND_OVERBOUGHT: "Finding overbought stocks",
            QueryIntent.FIND_DIVIDEND: "Finding dividend stocks",
            QueryIntent.FIND_VALUE: "Finding value stocks",
            QueryIntent.FIND_MOMENTUM: "Finding momentum stocks",
            QueryIntent.GENERAL: "Screening stocks",
        }
        
        interpreted = intent_descriptions[intent]
        if parts:
            interpreted += " " + " ".join(parts)
        
        # Calculate confidence
        confidence = 0.5  # Base confidence
        if intent != QueryIntent.GENERAL:
            confidence += 0.2
        if sectors:
            confidence += 0.1
        if min_price or max_price:
            confidence += 0.1
        if rsi_condition or sma_condition:
            confidence += 0.1
        confidence = min(1.0, confidence)
        
        # Suggest persona based on query
        suggested_persona = None
        if "conservative" in query_lower or "safe" in query_lower or "low risk" in query_lower:
            suggested_persona = InvestorPersona.CONSERVATIVE
        elif "aggressive" in query_lower or "high risk" in query_lower:
            suggested_persona = InvestorPersona.AGGRESSIVE
        
        return ParsedQuery(
            original_query=query,
            intent=intent,
            interpreted_as=interpreted,
            strategy=strategy,
            filters=filters,
            sectors=sectors,
            tickers=[],
            rsi_condition=rsi_condition,
            sma_condition=sma_condition,
            volume_condition=volume_condition,
            confidence=confidence,
            suggested_persona=suggested_persona,
        )
    
    async def _parse_with_llm(self, query: str) -> ParsedQuery | None:
        """
        Parse query using LLM for complex understanding.
        
        More accurate but slower and costs tokens.
        """
        llm = self._get_llm()
        if not llm:
            return None
        
        from langchain_core.messages import HumanMessage, SystemMessage
        
        prompt = f"""Parse this stock screening query into structured criteria.

Query: "{query}"

Return a JSON object with:
{{
    "intent": "find_bullish|find_bearish|find_breakout|find_oversold|find_overbought|find_dividend|find_value|find_momentum|general",
    "interpreted_as": "Human-readable interpretation of what user wants",
    "strategy": "maverick|maverick_bear|supply_demand_breakout",
    "sectors": ["Technology", "Healthcare", etc] or [],
    "tickers": ["AAPL", "MSFT"] if specific stocks mentioned, or [],
    "filters": {{
        "min_price": number or null,
        "max_price": number or null,
        "min_rsi": number or null,
        "max_rsi": number or null,
        "above_sma_50": true/false/null,
        "above_sma_200": true/false/null
    }},
    "rsi_condition": "RSI description" or null,
    "sma_condition": "SMA description" or null,
    "volume_condition": "Volume description" or null,
    "suggested_persona": "conservative|moderate|aggressive" or null,
    "confidence": 0.0-1.0 (how confident in interpretation)
}}

Return ONLY valid JSON, no markdown or explanation."""

        try:
            response = await asyncio.wait_for(
                llm.ainvoke([
                    SystemMessage(content=(
                        "You are a stock screening query parser. "
                        "Extract structured criteria from natural language. "
                        "Return ONLY valid JSON."
                    )),
                    HumanMessage(content=prompt),
                ]),
                timeout=LLM_TIMEOUT,
            )
            
            content = response.content.strip()
            
            # Clean up potential markdown
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            data = json.loads(content)
            
            # Build filter from parsed data
            filters_data = data.get("filters", {})
            filters = ScreeningFilter(
                min_price=Decimal(str(filters_data["min_price"])) if filters_data.get("min_price") else None,
                max_price=Decimal(str(filters_data["max_price"])) if filters_data.get("max_price") else None,
                min_rsi=Decimal(str(filters_data["min_rsi"])) if filters_data.get("min_rsi") else None,
                max_rsi=Decimal(str(filters_data["max_rsi"])) if filters_data.get("max_rsi") else None,
                above_sma_50=filters_data.get("above_sma_50"),
                above_sma_200=filters_data.get("above_sma_200"),
                sectors=data.get("sectors") if data.get("sectors") else None,
            )
            
            # Parse persona
            persona_str = data.get("suggested_persona")
            suggested_persona = None
            if persona_str:
                try:
                    suggested_persona = InvestorPersona(persona_str)
                except ValueError:
                    pass
            
            return ParsedQuery(
                original_query=query,
                intent=QueryIntent(data.get("intent", "general")),
                interpreted_as=data.get("interpreted_as", "Screening stocks"),
                strategy=data.get("strategy", "maverick"),
                filters=filters,
                sectors=data.get("sectors", []),
                tickers=data.get("tickers", []),
                rsi_condition=data.get("rsi_condition"),
                sma_condition=data.get("sma_condition"),
                volume_condition=data.get("volume_condition"),
                confidence=data.get("confidence", 0.8),
                suggested_persona=suggested_persona,
            )
            
        except asyncio.TimeoutError:
            logger.warning(f"LLM timeout parsing query: {query}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM parsing error: {e}")
            return None
    
    def get_suggestions(self, partial_query: str = "") -> list[QuerySuggestion]:
        """
        Get query suggestions for autocomplete.
        
        Args:
            partial_query: Partial query for filtering suggestions
            
        Returns:
            List of suggested queries
        """
        if not partial_query:
            return EXAMPLE_QUERIES[:6]
        
        partial_lower = partial_query.lower()
        matching = [
            s for s in EXAMPLE_QUERIES
            if partial_lower in s.query.lower() or partial_lower in s.description.lower()
        ]
        
        return matching[:6]
    
    async def refine_query(
        self,
        current_query: str,
        refinement: str,
    ) -> ParsedQuery:
        """
        Refine an existing query with additional criteria.
        
        Examples:
            current: "Find tech stocks"
            refinement: "Add healthcare too"
            result: "Find tech and healthcare stocks"
            
        Args:
            current_query: Current query
            refinement: User's refinement request
            
        Returns:
            ParsedQuery with combined criteria
        """
        # Parse both queries
        current_parsed = await self.parse_query(current_query)
        refinement_parsed = await self.parse_query(refinement)
        
        # Merge sectors
        merged_sectors = list(set(current_parsed.sectors + refinement_parsed.sectors))
        
        # Merge filters (refinement takes precedence)
        merged_filters = ScreeningFilter(
            min_price=refinement_parsed.filters.min_price or current_parsed.filters.min_price,
            max_price=refinement_parsed.filters.max_price or current_parsed.filters.max_price,
            min_rsi=refinement_parsed.filters.min_rsi or current_parsed.filters.min_rsi,
            max_rsi=refinement_parsed.filters.max_rsi or current_parsed.filters.max_rsi,
            above_sma_50=refinement_parsed.filters.above_sma_50 if refinement_parsed.filters.above_sma_50 is not None else current_parsed.filters.above_sma_50,
            above_sma_200=refinement_parsed.filters.above_sma_200 if refinement_parsed.filters.above_sma_200 is not None else current_parsed.filters.above_sma_200,
            sectors=merged_sectors if merged_sectors else None,
        )
        
        # Build combined interpretation
        combined_query = f"{current_query}; {refinement}"
        
        return ParsedQuery(
            original_query=combined_query,
            intent=refinement_parsed.intent if refinement_parsed.intent != QueryIntent.GENERAL else current_parsed.intent,
            interpreted_as=f"{current_parsed.interpreted_as}, also {refinement_parsed.interpreted_as.lower()}",
            strategy=refinement_parsed.strategy if refinement_parsed.strategy != "maverick" else current_parsed.strategy,
            filters=merged_filters,
            sectors=merged_sectors,
            tickers=list(set(current_parsed.tickers + refinement_parsed.tickers)),
            rsi_condition=refinement_parsed.rsi_condition or current_parsed.rsi_condition,
            sma_condition=refinement_parsed.sma_condition or current_parsed.sma_condition,
            volume_condition=refinement_parsed.volume_condition or current_parsed.volume_condition,
            confidence=min(current_parsed.confidence, refinement_parsed.confidence),
            suggested_persona=refinement_parsed.suggested_persona or current_parsed.suggested_persona,
        )


# Factory function
def get_nl_screening_service(use_llm: bool = True) -> NLScreeningService:
    """Get configured NL screening service."""
    if settings.openrouter_api_key:
        return NLScreeningService(openrouter_api_key=settings.openrouter_api_key, use_llm=use_llm)
    return NLScreeningService(use_llm=use_llm)


__all__ = [
    "NLScreeningService",
    "ParsedQuery",
    "QueryIntent",
    "QuerySuggestion",
    "EXAMPLE_QUERIES",
    "get_nl_screening_service",
]

