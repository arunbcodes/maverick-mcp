"""
AI-powered content analysis for research results.

Provides sentiment analysis, insight extraction, and credibility scoring
using LLM with batch processing capabilities.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from maverick_agents.research.config import PERSONA_RESEARCH_FOCUS

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMProtocol(Protocol):
    """Protocol for LLM interface."""

    async def ainvoke(self, messages: list[Any]) -> Any:
        """Invoke the LLM with messages."""
        ...


class ContentAnalyzer:
    """
    AI-powered content analysis for research results with batch processing capability.

    Features:
    - Sentiment analysis (bullish/bearish/neutral)
    - Key insight extraction
    - Risk factor identification
    - Credibility scoring
    - Batch processing for efficiency
    - Fallback analysis when LLM is unavailable
    """

    def __init__(self, llm: LLMProtocol, batch_size: int = 4):
        """
        Initialize the content analyzer.

        Args:
            llm: LLM instance for AI-powered analysis
            batch_size: Number of items to process concurrently
        """
        self.llm = llm
        self._batch_size = batch_size
        self.logger = logging.getLogger(f"{__name__}.ContentAnalyzer")

    @staticmethod
    def _coerce_message_content(raw_content: Any) -> str:
        """
        Convert LLM response content to a string for JSON parsing.

        Args:
            raw_content: Raw content from LLM response

        Returns:
            String representation of the content
        """
        if isinstance(raw_content, str):
            return raw_content

        if isinstance(raw_content, list):
            parts: list[str] = []
            for item in raw_content:
                if isinstance(item, dict):
                    text_value = item.get("text")
                    if isinstance(text_value, str):
                        parts.append(text_value)
                    else:
                        parts.append(str(text_value))
                else:
                    parts.append(str(item))
            return "".join(parts)

        return str(raw_content)

    def _create_system_message(self, content: str) -> dict[str, Any]:
        """Create a system message dict."""
        return {"role": "system", "content": content}

    def _create_human_message(self, content: str) -> dict[str, Any]:
        """Create a human message dict."""
        return {"role": "user", "content": content}

    async def analyze_content(
        self, content: str, persona: str, analysis_focus: str = "general"
    ) -> dict[str, Any]:
        """
        Analyze content with AI for insights, sentiment, and relevance.

        Args:
            content: Text content to analyze
            persona: Investor persona for perspective
            analysis_focus: Focus area for analysis

        Returns:
            Analysis result dictionary with insights, sentiment, risks, etc.
        """
        persona_focus = PERSONA_RESEARCH_FOCUS.get(
            persona.lower(), PERSONA_RESEARCH_FOCUS["moderate"]
        )

        analysis_prompt = f"""
        Analyze this financial content from the perspective of a {persona} investor.

        Content to analyze:
        {content[:3000]}

        Focus Areas: {", ".join(persona_focus["keywords"])}
        Risk Focus: {persona_focus["risk_focus"]}
        Time Horizon: {persona_focus["time_horizon"]}

        Provide analysis in the following structure:

        1. KEY_INSIGHTS: 3-5 bullet points of most important insights
        2. SENTIMENT: Overall sentiment (bullish/bearish/neutral) with confidence (0-1)
        3. RISK_FACTORS: Key risks identified relevant to {persona} investors
        4. OPPORTUNITIES: Investment opportunities or catalysts identified
        5. CREDIBILITY: Assessment of source credibility (0-1 score)
        6. RELEVANCE: How relevant is this to {persona} investment strategy (0-1 score)
        7. SUMMARY: 2-3 sentence summary for {persona} investors

        Format as JSON with clear structure.
        """

        try:
            # Create messages using dict format for Protocol compatibility
            messages = [
                self._create_system_message(
                    "You are a financial content analyst. Return only valid JSON."
                ),
                self._create_human_message(analysis_prompt),
            ]

            response = await self.llm.ainvoke(messages)

            raw_content = self._coerce_message_content(response.content).strip()

            # Try to extract JSON from the response
            analysis = self._parse_json_response(raw_content)

            return {
                "insights": analysis.get("KEY_INSIGHTS", []),
                "sentiment": {
                    "direction": analysis.get("SENTIMENT", {}).get(
                        "direction", "neutral"
                    ),
                    "confidence": analysis.get("SENTIMENT", {}).get("confidence", 0.5),
                },
                "risk_factors": analysis.get("RISK_FACTORS", []),
                "opportunities": analysis.get("OPPORTUNITIES", []),
                "credibility_score": analysis.get("CREDIBILITY", 0.5),
                "relevance_score": analysis.get("RELEVANCE", 0.5),
                "summary": analysis.get("SUMMARY", ""),
                "analysis_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.warning(f"AI content analysis failed: {e}, using fallback")
            return self._fallback_analysis(content, persona)

    def _parse_json_response(self, raw_content: str) -> dict[str, Any]:
        """
        Parse JSON from LLM response, handling various formats.

        Args:
            raw_content: Raw response string

        Returns:
            Parsed JSON dictionary
        """
        # Try direct JSON parse
        try:
            return json.loads(raw_content)
        except json.JSONDecodeError:
            pass

        # Try to find JSON block in response
        import re

        json_match = re.search(r"\{[\s\S]*\}", raw_content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Return empty dict if parsing fails
        return {}

    def _fallback_analysis(self, content: str, persona: str) -> dict[str, Any]:
        """
        Fallback analysis using keyword matching when LLM is unavailable.

        Args:
            content: Text content to analyze
            persona: Investor persona for perspective

        Returns:
            Basic analysis result dictionary
        """
        persona_focus = PERSONA_RESEARCH_FOCUS.get(
            persona.lower(), PERSONA_RESEARCH_FOCUS["moderate"]
        )

        content_lower = content.lower()

        # Simple sentiment analysis
        positive_words = [
            "growth",
            "increase",
            "profit",
            "success",
            "opportunity",
            "strong",
            "bullish",
            "upgrade",
            "beat",
            "exceed",
        ]
        negative_words = [
            "decline",
            "loss",
            "risk",
            "problem",
            "concern",
            "weak",
            "bearish",
            "downgrade",
            "miss",
            "warning",
        ]

        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)

        if positive_count > negative_count:
            sentiment = "bullish"
            confidence = min(0.6 + (positive_count - negative_count) * 0.05, 0.8)
        elif negative_count > positive_count:
            sentiment = "bearish"
            confidence = min(0.6 + (negative_count - positive_count) * 0.05, 0.8)
        else:
            sentiment = "neutral"
            confidence = 0.5

        # Relevance scoring based on keywords
        keyword_matches = sum(
            1 for keyword in persona_focus["keywords"] if keyword in content_lower
        )
        relevance_score = min(keyword_matches / len(persona_focus["keywords"]), 1.0)

        return {
            "insights": [f"Fallback analysis for {persona} investor perspective"],
            "sentiment": {"direction": sentiment, "confidence": confidence},
            "risk_factors": ["Unable to perform detailed risk analysis"],
            "opportunities": ["Unable to identify specific opportunities"],
            "credibility_score": 0.5,
            "relevance_score": relevance_score,
            "summary": f"Content analysis for {persona} investor using fallback method",
            "analysis_timestamp": datetime.now(),
            "fallback_used": True,
        }

    async def analyze_content_batch(
        self,
        content_items: list[tuple[str, str]],
        persona: str,
        analysis_focus: str = "general",
    ) -> list[dict[str, Any]]:
        """
        Analyze multiple content items in parallel batches for improved performance.

        Args:
            content_items: List of (content, source_identifier) tuples
            persona: Investor persona for analysis perspective
            analysis_focus: Focus area for analysis

        Returns:
            List of analysis results in same order as input
        """
        if not content_items:
            return []

        # Process items in batches to avoid overwhelming the LLM
        results: list[dict[str, Any]] = []
        for i in range(0, len(content_items), self._batch_size):
            batch = content_items[i : i + self._batch_size]

            # Create concurrent tasks for this batch
            tasks = [
                self.analyze_content(content, persona, analysis_focus)
                for content, _ in batch
            ]

            # Wait for all tasks in this batch to complete
            try:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results and handle exceptions
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.warning(f"Batch analysis failed for item {i + j}: {result}")
                        # Use fallback for failed items
                        content, source_id = batch[j]
                        fallback_result = self._fallback_analysis(content, persona)
                        fallback_result["source_identifier"] = source_id
                        fallback_result["batch_processed"] = True
                        results.append(fallback_result)
                    elif isinstance(result, dict):
                        enriched_result = dict(result)
                        enriched_result["source_identifier"] = batch[j][1]
                        enriched_result["batch_processed"] = True
                        results.append(enriched_result)
                    else:
                        content, source_id = batch[j]
                        fallback_result = self._fallback_analysis(content, persona)
                        fallback_result["source_identifier"] = source_id
                        fallback_result["batch_processed"] = True
                        results.append(fallback_result)

            except Exception as e:
                logger.error(f"Batch analysis completely failed: {e}")
                # Fallback for entire batch
                for content, source_id in batch:
                    fallback_result = self._fallback_analysis(content, persona)
                    fallback_result["source_identifier"] = source_id
                    fallback_result["batch_processed"] = True
                    fallback_result["batch_error"] = str(e)
                    results.append(fallback_result)

        logger.info(
            f"Batch content analysis completed: {len(content_items)} items processed "
            f"in {(len(content_items) + self._batch_size - 1) // self._batch_size} batches"
        )

        return results

    async def analyze_content_items(
        self,
        content_items: list[dict[str, Any]],
        focus_areas: list[str],
    ) -> dict[str, Any]:
        """
        Analyze content items for test compatibility.

        Args:
            content_items: List of search result dictionaries with content/text field
            focus_areas: List of focus areas for analysis

        Returns:
            Dictionary with aggregated analysis results
        """
        if not content_items:
            return {
                "insights": [],
                "sentiment_scores": [],
                "credibility_scores": [],
            }

        # Analyze each content item
        analyzed_results = []
        for item in content_items:
            content = item.get("text") or item.get("content") or ""
            if content:
                try:
                    result = await self._analyze_single_content(item, focus_areas)
                    analyzed_results.append(result)
                except Exception as e:
                    logger.warning(f"Content analysis failed: {e}")
                    analyzed_results.append(
                        {
                            "insights": [
                                {"insight": "Analysis failed", "confidence": 0.1}
                            ],
                            "sentiment": {"direction": "neutral", "confidence": 0.5},
                            "credibility": 0.5,
                        }
                    )

        # Aggregate results
        all_insights: list[str] = []
        sentiment_scores: list[dict[str, Any]] = []
        credibility_scores: list[float] = []

        for result in analyzed_results:
            # Handle test format with nested insight objects
            insights = result.get("insights", [])
            if isinstance(insights, list):
                for insight in insights:
                    if isinstance(insight, dict) and "insight" in insight:
                        all_insights.append(insight["insight"])
                    elif isinstance(insight, str):
                        all_insights.append(insight)
                    else:
                        all_insights.append(str(insight))

            sentiment = result.get("sentiment", {})
            if sentiment:
                sentiment_scores.append(sentiment)

            credibility = result.get(
                "credibility_score", result.get("credibility", 0.5)
            )
            credibility_scores.append(credibility)

        return {
            "insights": all_insights,
            "sentiment_scores": sentiment_scores,
            "credibility_scores": credibility_scores,
        }

    async def _analyze_single_content(
        self, content_item: dict[str, Any] | str, focus_areas: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Analyze single content item - used by tests.

        Args:
            content_item: Content item (dict or string)
            focus_areas: Optional focus areas for analysis

        Returns:
            Analysis result dictionary
        """
        if isinstance(content_item, dict):
            content = content_item.get("text") or content_item.get("content") or ""
        else:
            content = content_item

        try:
            result = await self.analyze_content(content, "moderate")
            # Ensure test-compatible format
            if "credibility_score" in result and "credibility" not in result:
                result["credibility"] = result["credibility_score"]
            return result
        except Exception as e:
            logger.warning(f"Single content analysis failed: {e}")
            return {
                "sentiment": {"direction": "neutral", "confidence": 0.5},
                "credibility": 0.5,
                "credibility_score": 0.5,
                "insights": [],
                "risk_factors": [],
                "opportunities": [],
            }

    async def _extract_themes(
        self, content_items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Extract themes from content items - used by tests.

        Args:
            content_items: List of content items

        Returns:
            List of theme dictionaries with theme, relevance, and mentions
        """
        if not content_items:
            return []

        # Use LLM to extract structured themes
        try:
            content_text = "\n".join(
                [item.get("text", item.get("content", "")) for item in content_items]
            )

            prompt = f"""
            Extract key themes from the following content and return as JSON:

            {content_text[:2000]}

            Return format: {{"themes": [{{"theme": "theme_name", "relevance": 0.9, "mentions": 10}}]}}
            """

            messages = [
                self._create_system_message(
                    "You are a theme extraction AI. Return only valid JSON."
                ),
                self._create_human_message(prompt),
            ]

            response = await self.llm.ainvoke(messages)

            result = self._parse_json_response(
                self._coerce_message_content(response.content)
            )
            return result.get("themes", [])

        except Exception as e:
            logger.warning(f"Theme extraction failed: {e}")
            # Fallback to simple keyword-based themes
            themes = []
            seen_themes = set()

            for item in content_items:
                content = item.get("text") or item.get("content") or ""
                if content:
                    content_lower = content.lower()
                    if "growth" in content_lower and "Growth" not in seen_themes:
                        themes.append(
                            {"theme": "Growth", "relevance": 0.8, "mentions": 1}
                        )
                        seen_themes.add("Growth")
                    if "earnings" in content_lower and "Earnings" not in seen_themes:
                        themes.append(
                            {"theme": "Earnings", "relevance": 0.7, "mentions": 1}
                        )
                        seen_themes.add("Earnings")
                    if "technology" in content_lower and "Technology" not in seen_themes:
                        themes.append(
                            {"theme": "Technology", "relevance": 0.6, "mentions": 1}
                        )
                        seen_themes.add("Technology")

            return themes
