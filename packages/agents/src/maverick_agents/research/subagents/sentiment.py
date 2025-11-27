"""
Sentiment research subagent.

Specialized agent for market sentiment analysis including
analyst ratings, news sentiment, and investor opinions.
"""

from __future__ import annotations

import logging
from typing import Any

from maverick_agents.research.subagents.base import BaseSubagent, ResearchTask

logger = logging.getLogger(__name__)


class SentimentResearchAgent(BaseSubagent):
    """
    Specialized agent for market sentiment analysis.

    Focus areas:
    - Analyst ratings and recommendations
    - News sentiment (positive/negative)
    - Investor opinions and sentiment
    - Social sentiment (discussion trends)
    - Institutional sentiment
    """

    FOCUS_AREAS = [
        "market_sentiment",
        "analyst_opinions",
        "news_sentiment",
        "social_sentiment",
    ]

    def _generate_sentiment_queries(self, topic: str) -> list[str]:
        """
        Generate sentiment analysis specific queries.

        Args:
            topic: Research topic

        Returns:
            List of specialized search queries
        """
        return [
            f"{topic} analyst rating recommendation upgrade downgrade",
            f"{topic} market sentiment investor opinion",
            f"{topic} news sentiment positive negative",
            f"{topic} social sentiment discussion",
            f"{topic} institutional investor sentiment",
        ]

    async def execute_research(self, task: ResearchTask) -> dict[str, Any]:
        """
        Execute sentiment analysis research.

        Args:
            task: Research task to execute

        Returns:
            Sentiment research results
        """
        self.logger.info(f"Executing sentiment research for: {task.target_topic}")

        # Generate sentiment-specific search queries
        queries = self._generate_sentiment_queries(task.target_topic)

        # Perform specialized search (more sources for sentiment)
        search_results = await self._perform_specialized_search(
            topic=task.target_topic, specialized_queries=queries, max_results=10
        )

        # Analyze results with sentiment focus
        analyzed_results = await self._analyze_search_results(
            search_results, analysis_focus="sentiment_analysis"
        )

        # Extract sentiment-specific insights
        insights, risks, opportunities, sources = self._aggregate_insights(
            analyzed_results
        )

        return {
            "research_type": "sentiment",
            "insights": insights,
            "risk_factors": risks,
            "opportunities": opportunities,
            "sentiment": self._calculate_weighted_sentiment(analyzed_results),
            "credibility_score": self._calculate_average_credibility(analyzed_results),
            "sources": sources,
            "focus_areas": self.FOCUS_AREAS,
        }

    def _calculate_weighted_sentiment(
        self, results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Calculate weighted sentiment with confidence weighting.

        Args:
            results: List of analyzed results

        Returns:
            Sentiment dictionary with direction and confidence
        """
        sentiments = [
            r.get("analysis", {}).get("sentiment", {})
            for r in results
            if r.get("analysis")
        ]
        sentiments = [s for s in sentiments if s]

        if not sentiments:
            return {"direction": "neutral", "confidence": 0.5}

        # Weighted by confidence
        weighted_scores = []
        total_confidence = 0.0

        for sentiment in sentiments:
            direction = sentiment.get("direction", "neutral")
            confidence = sentiment.get("confidence", 0.5)

            if direction == "bullish":
                weighted_scores.append(1 * confidence)
            elif direction == "bearish":
                weighted_scores.append(-1 * confidence)
            else:
                weighted_scores.append(0)

            total_confidence += confidence

        if not weighted_scores:
            return {"direction": "neutral", "confidence": 0.5}

        avg_score = sum(weighted_scores) / len(weighted_scores)
        avg_confidence = total_confidence / len(sentiments)

        if avg_score > 0.3:
            return {"direction": "bullish", "confidence": avg_confidence}
        elif avg_score < -0.3:
            return {"direction": "bearish", "confidence": avg_confidence}
        else:
            return {"direction": "neutral", "confidence": avg_confidence}
