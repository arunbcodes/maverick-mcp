"""
Technical research subagent.

Specialized agent for technical analysis research including
price patterns, indicators, and chart analysis.
"""

from __future__ import annotations

import logging
from typing import Any

from maverick_agents.research.subagents.base import BaseSubagent, ResearchTask

logger = logging.getLogger(__name__)


class TechnicalResearchAgent(BaseSubagent):
    """
    Specialized agent for technical analysis research.

    Focus areas:
    - Price action and chart patterns
    - Technical indicators (RSI, MACD, etc.)
    - Support and resistance levels
    - Breakout and trend analysis
    - Volume analysis
    """

    FOCUS_AREAS = [
        "price_action",
        "chart_patterns",
        "technical_indicators",
        "support_resistance",
    ]

    def _generate_technical_queries(self, topic: str) -> list[str]:
        """
        Generate technical analysis specific queries.

        Args:
            topic: Research topic

        Returns:
            List of specialized search queries
        """
        return [
            f"{topic} technical analysis chart pattern",
            f"{topic} price target support resistance",
            f"{topic} RSI MACD technical indicators",
            f"{topic} breakout trend analysis",
            f"{topic} volume analysis price movement",
        ]

    async def execute_research(self, task: ResearchTask) -> dict[str, Any]:
        """
        Execute technical analysis research.

        Args:
            task: Research task to execute

        Returns:
            Technical research results
        """
        self.logger.info(f"Executing technical research for: {task.target_topic}")

        # Generate technical-specific search queries
        queries = self._generate_technical_queries(task.target_topic)

        # Perform specialized search
        search_results = await self._perform_specialized_search(
            topic=task.target_topic, specialized_queries=queries, max_results=6
        )

        # Analyze results with technical focus
        analyzed_results = await self._analyze_search_results(
            search_results, analysis_focus="technical_analysis"
        )

        # Extract technical-specific insights
        insights, risks, opportunities, sources = self._aggregate_insights(
            analyzed_results
        )

        return {
            "research_type": "technical",
            "insights": insights,
            "risk_factors": risks,
            "opportunities": opportunities,
            "sentiment": self._calculate_sentiment(analyzed_results),
            "credibility_score": self._calculate_average_credibility(analyzed_results),
            "sources": sources,
            "focus_areas": self.FOCUS_AREAS,
        }
