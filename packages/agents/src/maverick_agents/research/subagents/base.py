"""
Base subagent for specialized research tasks.

Provides common functionality for all research subagents including
search execution, content analysis, and credibility scoring.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from maverick_agents.personas import InvestorPersona
    from maverick_agents.research.content_analyzer import ContentAnalyzer
    from maverick_agents.research.providers.base import WebSearchProvider

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMProtocol(Protocol):
    """Protocol for LLM interface."""

    async def ainvoke(self, messages: list[Any]) -> Any:
        """Invoke the LLM with messages."""
        ...


class ResearchTask:
    """Task definition for research operations."""

    def __init__(
        self,
        task_id: str,
        task_type: str,
        target_topic: str,
        focus_areas: list[str] | None = None,
        priority: int = 0,
    ):
        """
        Initialize a research task.

        Args:
            task_id: Unique task identifier
            task_type: Type of research task (fundamental, technical, sentiment, competitive)
            target_topic: Topic to research
            focus_areas: Specific areas to focus on
            priority: Task priority (higher = more important)
        """
        self.task_id = task_id
        self.task_type = task_type
        self.target_topic = target_topic
        self.focus_areas = focus_areas or []
        self.priority = priority
        self.status = "pending"
        self.result: dict[str, Any] | None = None
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.error: str | None = None


class BaseSubagent:
    """
    Base class for specialized research subagents.

    Provides common functionality for:
    - Safe search execution with error handling
    - Content analysis integration
    - Credibility scoring
    - Result aggregation
    """

    def __init__(
        self,
        llm: LLMProtocol,
        search_providers: list[WebSearchProvider],
        content_analyzer: ContentAnalyzer,
        persona: InvestorPersona,
    ):
        """
        Initialize the base subagent.

        Args:
            llm: LLM for analysis
            search_providers: List of search providers
            content_analyzer: Content analyzer instance
            persona: Investor persona
        """
        self.llm = llm
        self.search_providers = search_providers
        self.content_analyzer = content_analyzer
        self.persona = persona
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def execute_research(self, task: ResearchTask) -> dict[str, Any]:
        """
        Execute research task - to be implemented by subclasses.

        Args:
            task: Research task to execute

        Returns:
            Research results dictionary
        """
        raise NotImplementedError("Subclasses must implement execute_research")

    async def _safe_search(
        self,
        provider: WebSearchProvider,
        query: str,
        num_results: int = 5,
        timeout_budget: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Safely execute search with a provider, handling exceptions gracefully.

        Args:
            provider: Search provider to use
            query: Search query
            num_results: Number of results to return
            timeout_budget: Optional timeout budget

        Returns:
            List of search results (empty list on failure)
        """
        try:
            return await provider.search(
                query, num_results=num_results, timeout_budget=timeout_budget
            )
        except Exception as e:
            self.logger.warning(
                f"Search failed for '{query}' with provider {type(provider).__name__}: {e}"
            )
            return []

    async def _perform_specialized_search(
        self,
        topic: str,
        specialized_queries: list[str],
        max_results: int = 10,
        timeout_budget: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform specialized web search for this subagent type.

        Args:
            topic: Main research topic
            specialized_queries: List of specialized search queries
            max_results: Maximum results to return
            timeout_budget: Optional timeout budget

        Returns:
            List of deduplicated search results
        """
        all_results: list[dict[str, Any]] = []

        # Create all search tasks for parallel execution
        search_tasks = []
        results_per_query = (
            max_results // len(specialized_queries)
            if specialized_queries
            else max_results
        )

        # Calculate timeout per search if budget provided
        if timeout_budget:
            total_searches = len(specialized_queries) * len(self.search_providers)
            timeout_per_search = timeout_budget / max(total_searches, 1)
        else:
            timeout_per_search = None

        for query in specialized_queries:
            for provider in self.search_providers:
                # Create async task for each provider/query combination
                search_tasks.append(
                    self._safe_search(
                        provider,
                        query,
                        num_results=results_per_query,
                        timeout_budget=timeout_per_search,
                    )
                )

        # Execute all searches in parallel using asyncio.gather()
        if search_tasks:
            parallel_results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # Process results and filter out exceptions
            for result in parallel_results:
                if isinstance(result, Exception):
                    self.logger.warning(f"Search task failed: {result}")
                elif isinstance(result, list):
                    all_results.extend(result)
                elif result is not None:
                    all_results.append(result)

        # Deduplicate results
        seen_urls: set[str] = set()
        unique_results: list[dict[str, Any]] = []
        for result in all_results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        return unique_results[:max_results]

    async def _analyze_search_results(
        self, results: list[dict[str, Any]], analysis_focus: str
    ) -> list[dict[str, Any]]:
        """
        Analyze search results with specialized focus.

        Args:
            results: List of search results to analyze
            analysis_focus: Focus area for analysis

        Returns:
            List of analyzed results with credibility scores
        """
        analyzed_results: list[dict[str, Any]] = []

        for result in results:
            content = result.get("content") or result.get("raw_content") or ""
            if content:
                try:
                    analysis = await self.content_analyzer.analyze_content(
                        content=content,
                        persona=self.persona.name.lower(),
                        analysis_focus=analysis_focus,
                    )

                    # Add source credibility
                    credibility_score = self._calculate_source_credibility(result)
                    analysis["credibility_score"] = credibility_score

                    analyzed_results.append(
                        {
                            **result,
                            "analysis": analysis,
                            "credibility_score": credibility_score,
                        }
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Content analysis failed for {result.get('url', 'unknown')}: {e}"
                    )

        return analyzed_results

    def _calculate_source_credibility(self, source: dict[str, Any]) -> float:
        """
        Calculate credibility score for a source.

        Args:
            source: Source dictionary with url and other metadata

        Returns:
            Credibility score between 0.0 and 1.0
        """
        score = 0.5  # Base score

        url = source.get("url", "")

        # Domain credibility
        if any(domain in url for domain in [".gov", ".edu", ".org"]):
            score += 0.2
        elif any(
            domain in url
            for domain in [
                "sec.gov",
                "investopedia.com",
                "bloomberg.com",
                "reuters.com",
            ]
        ):
            score += 0.3

        # Publication date recency
        pub_date = source.get("published_date")
        if pub_date:
            try:
                from datetime import datetime

                date_obj = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                days_old = (datetime.now() - date_obj).days
                if days_old < 30:
                    score += 0.1
                elif days_old < 90:
                    score += 0.05
            except (ValueError, TypeError, AttributeError):
                pass

        # Content analysis credibility
        if "analysis" in source:
            analysis_cred = source["analysis"].get("credibility_score", 0.5)
            score = (score + analysis_cred) / 2

        return min(score, 1.0)

    def _aggregate_insights(
        self, analyzed_results: list[dict[str, Any]], max_items: int = 8
    ) -> tuple[list[str], list[str], list[str], list[dict[str, Any]]]:
        """
        Aggregate insights, risks, opportunities, and sources from analyzed results.

        Args:
            analyzed_results: List of analyzed search results
            max_items: Maximum items per category

        Returns:
            Tuple of (insights, risks, opportunities, sources)
        """
        insights: list[str] = []
        risks: list[str] = []
        opportunities: list[str] = []
        sources: list[dict[str, Any]] = []

        for result in analyzed_results:
            analysis = result.get("analysis", {})
            insights.extend(analysis.get("insights", []))
            risks.extend(analysis.get("risk_factors", []))
            opportunities.extend(analysis.get("opportunities", []))
            sources.append(
                {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "credibility_score": result.get("credibility_score", 0.5),
                    "published_date": result.get("published_date"),
                    "author": result.get("author"),
                }
            )

        # Deduplicate using dict.fromkeys (preserves order)
        return (
            list(dict.fromkeys(insights))[:max_items],
            list(dict.fromkeys(risks))[:max_items - 2],  # Slightly fewer risks
            list(dict.fromkeys(opportunities))[:max_items - 2],
            sources,
        )

    def _calculate_sentiment(
        self, analyzed_results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Calculate aggregate sentiment from analyzed results.

        Args:
            analyzed_results: List of analyzed results

        Returns:
            Sentiment dictionary with direction and confidence
        """
        sentiments = []
        for result in analyzed_results:
            analysis = result.get("analysis", {})
            sentiment = analysis.get("sentiment", {})
            if sentiment:
                sentiments.append(sentiment)

        if not sentiments:
            return {"direction": "neutral", "confidence": 0.5}

        # Count sentiment directions
        bullish_count = sum(1 for s in sentiments if s.get("direction") == "bullish")
        bearish_count = sum(1 for s in sentiments if s.get("direction") == "bearish")
        total = len(sentiments)

        if bullish_count > bearish_count:
            confidence = 0.5 + (bullish_count / total) * 0.3
            return {"direction": "bullish", "confidence": min(confidence, 0.9)}
        elif bearish_count > bullish_count:
            confidence = 0.5 + (bearish_count / total) * 0.3
            return {"direction": "bearish", "confidence": min(confidence, 0.9)}
        else:
            return {"direction": "neutral", "confidence": 0.5}

    def _calculate_average_credibility(self, results: list[dict[str, Any]]) -> float:
        """
        Calculate average credibility of sources.

        Args:
            results: List of results with credibility scores

        Returns:
            Average credibility score
        """
        if not results:
            return 0.5

        credibility_scores = [r.get("credibility_score", 0.5) for r in results]
        return sum(credibility_scores) / len(credibility_scores)
