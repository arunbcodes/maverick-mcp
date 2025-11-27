"""
Fundamental research subagent.

Specialized agent for fundamental financial analysis including
earnings, valuation, financial health, and growth prospects.
"""

from __future__ import annotations

import logging
from typing import Any

from maverick_agents.research.subagents.base import BaseSubagent, ResearchTask

logger = logging.getLogger(__name__)


class FundamentalResearchAgent(BaseSubagent):
    """
    Specialized agent for fundamental financial analysis.

    Focus areas:
    - Earnings reports and financial results
    - Revenue growth and profit margins
    - Balance sheet and debt analysis
    - Valuation metrics (P/E, P/B, etc.)
    - Cash flow and dividend analysis
    """

    FOCUS_AREAS = [
        "earnings",
        "valuation",
        "financial_health",
        "growth_prospects",
    ]

    def _generate_fundamental_queries(self, topic: str) -> list[str]:
        """
        Generate fundamental analysis specific queries.

        Args:
            topic: Research topic

        Returns:
            List of specialized search queries
        """
        return [
            f"{topic} earnings report financial results",
            f"{topic} revenue growth profit margins",
            f"{topic} balance sheet debt ratio financial health",
            f"{topic} valuation PE ratio price earnings",
            f"{topic} cash flow dividend payout",
        ]

    async def execute_research(self, task: ResearchTask) -> dict[str, Any]:
        """
        Execute fundamental analysis research.

        Args:
            task: Research task to execute

        Returns:
            Fundamental research results
        """
        self.logger.info(f"Executing fundamental research for: {task.target_topic}")

        # Generate fundamental-specific search queries
        queries = self._generate_fundamental_queries(task.target_topic)

        # Perform specialized search
        search_results = await self._perform_specialized_search(
            topic=task.target_topic, specialized_queries=queries, max_results=8
        )

        # Analyze results with fundamental focus
        analyzed_results = await self._analyze_search_results(
            search_results, analysis_focus="fundamental_analysis"
        )

        # Extract fundamental-specific insights
        insights, risks, opportunities, sources = self._aggregate_insights(
            analyzed_results
        )

        return {
            "research_type": "fundamental",
            "insights": insights,
            "risk_factors": risks,
            "opportunities": opportunities,
            "sentiment": self._calculate_sentiment(analyzed_results),
            "credibility_score": self._calculate_average_credibility(analyzed_results),
            "sources": sources,
            "focus_areas": self.FOCUS_AREAS,
        }
