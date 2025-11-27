"""
Competitive research subagent.

Specialized agent for competitive and industry analysis including
market position, competitors, and industry trends.
"""

from __future__ import annotations

import logging
from typing import Any

from maverick_agents.research.subagents.base import BaseSubagent, ResearchTask

logger = logging.getLogger(__name__)


class CompetitiveResearchAgent(BaseSubagent):
    """
    Specialized agent for competitive and industry analysis.

    Focus areas:
    - Competitive position and market share
    - Competitor comparison and analysis
    - Industry trends and dynamics
    - Competitive advantages and moats
    - Sector performance
    """

    FOCUS_AREAS = [
        "competitive_position",
        "market_share",
        "industry_trends",
        "competitive_advantages",
    ]

    def _generate_competitive_queries(self, topic: str) -> list[str]:
        """
        Generate competitive analysis specific queries.

        Args:
            topic: Research topic

        Returns:
            List of specialized search queries
        """
        return [
            f"{topic} market share competitive position industry",
            f"{topic} competitors comparison competitive advantage",
            f"{topic} industry analysis market trends",
            f"{topic} competitive landscape market dynamics",
            f"{topic} industry outlook sector performance",
        ]

    async def execute_research(self, task: ResearchTask) -> dict[str, Any]:
        """
        Execute competitive analysis research.

        Args:
            task: Research task to execute

        Returns:
            Competitive research results
        """
        self.logger.info(f"Executing competitive research for: {task.target_topic}")

        # Generate competitive-specific search queries
        queries = self._generate_competitive_queries(task.target_topic)

        # Perform specialized search
        search_results = await self._perform_specialized_search(
            topic=task.target_topic, specialized_queries=queries, max_results=8
        )

        # Analyze results with competitive focus
        analyzed_results = await self._analyze_search_results(
            search_results, analysis_focus="competitive_analysis"
        )

        # Extract competitive-specific insights
        insights, risks, opportunities, sources = self._aggregate_insights(
            analyzed_results
        )

        return {
            "research_type": "competitive",
            "insights": insights,
            "risk_factors": risks,
            "opportunities": opportunities,
            "sentiment": self._calculate_sentiment(analyzed_results),
            "credibility_score": self._calculate_average_credibility(analyzed_results),
            "sources": sources,
            "focus_areas": self.FOCUS_AREAS,
        }
