"""
Research router - thin wrapper around maverick-agents.

All AI/LLM research logic lives in maverick-agents.
This router only defines MCP tool signatures and delegates.

Note: Requires maverick-agents optional dependency.
"""

import logging
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from maverick_server.capabilities_integration import with_audit

logger = logging.getLogger(__name__)

# Check if maverick-agents is available
try:
    from maverick_agents import (
        OpenRouterProvider,
        DeepResearchAgent,
    )
    from maverick_agents.research import (
        create_optimized_research_agent,
        get_depth_config,
    )
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    logger.warning("maverick-agents not installed - research tools disabled")


def register_research_tools(mcp: FastMCP) -> None:
    """Register research tools with MCP server.

    Only registers tools if maverick-agents is installed.
    """
    if not AGENTS_AVAILABLE:
        logger.info("Skipping research tools - maverick-agents not available")
        return

    @mcp.tool()
    @with_audit("research_comprehensive")
    async def research_comprehensive(
        query: str,
        persona: str = "moderate",
        research_scope: str = "standard",
        max_sources: int = 10,
        timeframe: str = "1m",
    ) -> Dict[str, Any]:
        """Perform comprehensive research on any financial topic.

        Uses AI agents with web search for deep analysis.

        Args:
            query: Research query or topic
            persona: Investor persona (conservative, moderate, aggressive)
            research_scope: Research depth (basic, standard, comprehensive, exhaustive)
            max_sources: Maximum sources to analyze (1-50)
            timeframe: Time frame for search (1d, 1w, 1m, 3m)

        Returns:
            Comprehensive research results with insights and recommendations
        """
        try:
            # Get appropriate timeout based on scope
            depth_config = get_depth_config(research_scope)

            # Create optimized research agent
            agent = create_optimized_research_agent(
                time_budget_seconds=depth_config.timeout_seconds,
            )

            # Run research
            result = await agent.research(
                query=query,
                persona=persona,
                max_sources=max_sources,
                timeframe=timeframe,
            )

            return {
                "query": query,
                "persona": persona,
                "scope": research_scope,
                "summary": result.get("summary", ""),
                "insights": result.get("insights", []),
                "sentiment": result.get("sentiment", {}),
                "sources_analyzed": result.get("sources_analyzed", 0),
                "confidence": result.get("confidence", 0.0),
            }
        except Exception as e:
            logger.error(f"Research error: {e}")
            return {"error": str(e)}

    @mcp.tool()
    @with_audit("research_company")
    async def research_company(
        symbol: str,
        include_competitive_analysis: bool = False,
        persona: str = "moderate",
    ) -> Dict[str, Any]:
        """Perform comprehensive research on a specific company.

        Args:
            symbol: Stock ticker symbol
            include_competitive_analysis: Include competitive analysis
            persona: Investor persona for analysis perspective

        Returns:
            Company-specific research with financial insights
        """
        try:
            agent = create_optimized_research_agent(time_budget_seconds=180.0)

            query = f"Comprehensive analysis of {symbol} stock"
            if include_competitive_analysis:
                query += " including competitive landscape and market position"

            result = await agent.research(
                query=query,
                persona=persona,
                max_sources=15,
            )

            return {
                "symbol": symbol,
                "company_analysis": result.get("summary", ""),
                "key_insights": result.get("insights", []),
                "sentiment": result.get("sentiment", {}),
                "risks": result.get("risks", []),
                "opportunities": result.get("opportunities", []),
                "competitive_included": include_competitive_analysis,
            }
        except Exception as e:
            logger.error(f"Company research error for {symbol}: {e}")
            return {"error": str(e)}

    @mcp.tool()
    @with_audit("research_market_sentiment")
    async def research_market_sentiment(
        topic: str,
        timeframe: str = "1w",
        persona: str = "moderate",
    ) -> Dict[str, Any]:
        """Analyze market sentiment for a specific topic or sector.

        Args:
            topic: Topic to analyze (company, sector, theme)
            timeframe: Time frame for analysis (1d, 1w, 1m)
            persona: Investor persona

        Returns:
            Sentiment analysis with market insights
        """
        try:
            agent = create_optimized_research_agent(time_budget_seconds=120.0)

            result = await agent.research(
                query=f"Market sentiment analysis for {topic}",
                persona=persona,
                max_sources=10,
                timeframe=timeframe,
            )

            sentiment = result.get("sentiment", {})

            return {
                "topic": topic,
                "timeframe": timeframe,
                "overall_sentiment": sentiment.get("direction", "neutral"),
                "sentiment_score": sentiment.get("confidence", 0.5),
                "key_themes": result.get("insights", [])[:5],
                "news_summary": result.get("summary", ""),
                "sources_analyzed": result.get("sources_analyzed", 0),
            }
        except Exception as e:
            logger.error(f"Sentiment analysis error for {topic}: {e}")
            return {"error": str(e)}

    logger.info("Registered research tools")
