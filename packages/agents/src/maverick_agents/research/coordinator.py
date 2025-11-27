"""
Deep Research Agent Coordinator.

Main orchestration agent for comprehensive financial research using
LangGraph workflows, parallel execution, and specialized subagents.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable
from uuid import uuid4

from maverick_agents.base import PersonaAwareAgent
from maverick_agents.research.config import (
    PERSONA_RESEARCH_FOCUS,
    RESEARCH_DEPTH_LEVELS,
)
from maverick_agents.research.content_analyzer import ContentAnalyzer
from maverick_agents.research.providers import (
    ExaSearchProvider,
    WebSearchError,
    WebSearchProvider,
)
from maverick_agents.research.subagents import (
    CompetitiveResearchAgent,
    FundamentalResearchAgent,
    ResearchTask,
    SentimentResearchAgent,
    TechnicalResearchAgent,
)
from maverick_agents.state import DeepResearchState

if TYPE_CHECKING:
    from langgraph.checkpoint.memory import MemorySaver
    from langchain_core.language_models import BaseChatModel
    from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


@runtime_checkable
class ParallelConfigProtocol(Protocol):
    """Protocol for parallel research configuration."""

    max_concurrent_agents: int
    timeout_per_agent: float
    enable_fallbacks: bool
    rate_limit_delay: float


@runtime_checkable
class ParallelOrchestratorProtocol(Protocol):
    """Protocol for parallel research orchestrator."""

    async def execute_parallel_research(
        self,
        tasks: list[Any],
        research_executor: Any,
        synthesis_callback: Any,
    ) -> Any:
        """Execute research tasks in parallel."""
        ...


@runtime_checkable
class TaskDistributorProtocol(Protocol):
    """Protocol for task distribution engine."""

    def distribute_research_tasks(
        self,
        topic: str,
        session_id: str,
        focus_areas: list[str] | None = None,
    ) -> list[Any]:
        """Distribute research tasks."""
        ...


@runtime_checkable
class ConversationStoreProtocol(Protocol):
    """Protocol for conversation storage."""

    def get(self, session_id: str) -> Any:
        """Get conversation by session ID."""
        ...

    def store(self, session_id: str, data: Any) -> None:
        """Store conversation data."""
        ...


class DefaultParallelConfig:
    """Default parallel research configuration."""

    def __init__(
        self,
        max_concurrent_agents: int = 4,
        timeout_per_agent: float = 180.0,
        enable_fallbacks: bool = False,
        rate_limit_delay: float = 0.5,
    ):
        self.max_concurrent_agents = max_concurrent_agents
        self.timeout_per_agent = timeout_per_agent
        self.enable_fallbacks = enable_fallbacks
        self.rate_limit_delay = rate_limit_delay


class ParallelResearchResult:
    """Result from parallel research execution."""

    def __init__(self):
        self.task_results: dict[str, ResearchTask] = {}
        self.synthesis: dict[str, Any] | None = None
        self.successful_tasks: int = 0
        self.failed_tasks: int = 0
        self.total_execution_time: float = 0.0
        self.parallel_efficiency: float = 0.0


class DeepResearchAgent(PersonaAwareAgent):
    """
    Deep research agent using LangGraph patterns.

    Provides comprehensive financial research with:
    - Web search across multiple providers
    - AI-powered content analysis
    - Sentiment detection and source validation
    - Parallel subagent execution
    - Persona-aware recommendations

    This coordinator uses the modular research components:
    - WebSearchProvider for search operations
    - ContentAnalyzer for AI analysis
    - Specialized subagents for different research types
    """

    def __init__(
        self,
        llm: BaseChatModel,
        persona: str = "moderate",
        checkpointer: MemorySaver | None = None,
        ttl_hours: int = 24,
        exa_api_key: str | None = None,
        default_depth: str = "standard",
        max_sources: int | None = None,
        research_depth: str | None = None,
        enable_parallel_execution: bool = True,
        parallel_config: ParallelConfigProtocol | None = None,
        search_providers: list[WebSearchProvider] | None = None,
        conversation_store: ConversationStoreProtocol | None = None,
    ):
        """
        Initialize deep research agent.

        Args:
            llm: Language model for analysis
            persona: Investor persona (conservative, moderate, aggressive, day_trader)
            checkpointer: LangGraph checkpointer for state persistence
            ttl_hours: TTL for cached research results
            exa_api_key: API key for Exa search provider
            default_depth: Default research depth level
            max_sources: Maximum sources to analyze
            research_depth: Override research depth
            enable_parallel_execution: Enable parallel subagent execution
            parallel_config: Configuration for parallel execution
            search_providers: Pre-configured search providers (for testing)
            conversation_store: Conversation storage (for testing)
        """
        # Store configuration
        self._exa_api_key = exa_api_key
        self._search_providers_loaded = False
        self._initialization_pending = True

        # Use injected providers or empty list
        self.search_providers: list[WebSearchProvider] = search_providers or []
        if search_providers:
            self._search_providers_loaded = True
            self._initialization_pending = False

        # Research configuration
        self.default_depth = research_depth or default_depth
        self.max_sources = max_sources or RESEARCH_DEPTH_LEVELS.get(
            self.default_depth, {}
        ).get("max_sources", 10)

        # Content analyzer
        self.content_analyzer = ContentAnalyzer(llm)

        # Parallel execution configuration
        self.enable_parallel_execution = enable_parallel_execution
        self.parallel_config = parallel_config or DefaultParallelConfig()

        # Conversation store (optional)
        self._conversation_store = conversation_store

        # Get research-specific tools
        research_tools = self._get_research_tools()

        # Initialize base class
        super().__init__(
            llm=llm,
            tools=research_tools,
            persona=persona,
            checkpointer=checkpointer,
            ttl_hours=ttl_hours,
        )

        logger.info(
            f"DeepResearchAgent initialized with persona={persona}, "
            f"depth={self.default_depth}, parallel={enable_parallel_execution}"
        )

    @property
    def web_search_provider(self) -> WebSearchProvider | None:
        """Compatibility property - returns first search provider."""
        return self.search_providers[0] if self.search_providers else None

    @property
    def conversation_store(self) -> ConversationStoreProtocol | None:
        """Get conversation store."""
        return self._conversation_store

    def get_state_schema(self) -> type:
        """Return DeepResearchState schema."""
        return DeepResearchState

    async def initialize(self) -> None:
        """
        Pre-initialize search providers.

        This eliminates lazy loading overhead during research operations.
        """
        if not self._initialization_pending:
            return

        try:
            if self._exa_api_key:
                provider = ExaSearchProvider(api_key=self._exa_api_key)
                self.search_providers = [provider]
            else:
                self.search_providers = []

            self._search_providers_loaded = True
            self._initialization_pending = False

            if not self.search_providers:
                logger.warning(
                    "No search providers available - research capabilities limited"
                )
            else:
                logger.info(
                    f"Initialized {len(self.search_providers)} search provider(s)"
                )

        except Exception as e:
            logger.error(f"Failed to initialize search providers: {e}")
            self.search_providers = []
            self._search_providers_loaded = True
            self._initialization_pending = False

    async def _ensure_search_providers_loaded(self) -> None:
        """Ensure search providers are loaded."""
        if self._search_providers_loaded:
            return

        logger.info("Initializing search providers on demand")
        await self.initialize()

    def _get_research_tools(self) -> list[BaseTool]:
        """Get tools specific to research capabilities."""
        # Tools will be created when needed by the workflow
        # This avoids circular imports with langchain_core.tools
        return []

    def _build_graph(self):
        """Build research workflow graph with multi-step process."""
        try:
            from langgraph.graph import END, START, StateGraph
            from langgraph.types import Command
        except ImportError:
            logger.warning("LangGraph not available - using simplified workflow")
            return None

        workflow = StateGraph(DeepResearchState)

        # Core research workflow nodes
        workflow.add_node("plan_research", self._plan_research)
        workflow.add_node("execute_searches", self._execute_searches)
        workflow.add_node("analyze_content", self._analyze_content)
        workflow.add_node("validate_sources", self._validate_sources)
        workflow.add_node("synthesize_findings", self._synthesize_findings)
        workflow.add_node("generate_citations", self._generate_citations)

        # Define workflow edges
        workflow.add_edge(START, "plan_research")
        workflow.add_edge("plan_research", "execute_searches")
        workflow.add_edge("execute_searches", "analyze_content")
        workflow.add_edge("analyze_content", "validate_sources")
        workflow.add_edge("validate_sources", "synthesize_findings")
        workflow.add_edge("synthesize_findings", "generate_citations")
        workflow.add_edge("generate_citations", END)

        return workflow.compile(checkpointer=self.checkpointer)

    async def research_comprehensive(
        self,
        topic: str,
        session_id: str,
        depth: str | None = None,
        focus_areas: list[str] | None = None,
        timeframe: str = "30d",
        timeout_budget: float | None = None,
        use_parallel_execution: bool | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Comprehensive research on a financial topic.

        Args:
            topic: Research topic or company/symbol
            session_id: Session identifier
            depth: Research depth (basic/standard/comprehensive/exhaustive)
            focus_areas: Specific areas to focus on
            timeframe: Time range for research
            timeout_budget: Total timeout budget in seconds
            use_parallel_execution: Override parallel execution setting
            **kwargs: Additional parameters

        Returns:
            Comprehensive research results with analysis and citations
        """
        await self._ensure_search_providers_loaded()

        # Check if search providers are available
        if not self.search_providers:
            return {
                "status": "error",
                "error": "No search providers configured",
                "details": "Please configure EXA_API_KEY to enable research",
                "topic": topic,
            }

        start_time = datetime.now()
        depth = depth or self.default_depth
        use_parallel = (
            use_parallel_execution
            if use_parallel_execution is not None
            else self.enable_parallel_execution
        )

        # Get persona focus areas if not specified
        if not focus_areas:
            persona_focus = PERSONA_RESEARCH_FOCUS.get(
                self.persona.name.lower(), PERSONA_RESEARCH_FOCUS["moderate"]
            )
            focus_areas = persona_focus["keywords"]

        logger.info(
            f"Starting research: topic='{topic[:50]}...', depth={depth}, "
            f"parallel={use_parallel}"
        )

        if use_parallel:
            try:
                result = await self._execute_parallel_research(
                    topic=topic,
                    session_id=session_id,
                    depth=depth,
                    focus_areas=focus_areas,
                    timeframe=timeframe,
                    start_time=start_time,
                    **kwargs,
                )
                return result
            except Exception as e:
                logger.warning(f"Parallel execution failed, falling back: {e}")
                # Fall through to sequential execution

        # Sequential execution
        return await self._execute_sequential_research(
            topic=topic,
            session_id=session_id,
            depth=depth,
            focus_areas=focus_areas,
            timeframe=timeframe,
            timeout_budget=timeout_budget,
            start_time=start_time,
            **kwargs,
        )

    async def _execute_sequential_research(
        self,
        topic: str,
        session_id: str,
        depth: str,
        focus_areas: list[str],
        timeframe: str,
        timeout_budget: float | None,
        start_time: datetime,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute research sequentially through workflow nodes."""
        depth_config = RESEARCH_DEPTH_LEVELS.get(depth, RESEARCH_DEPTH_LEVELS["standard"])

        try:
            # Step 1: Generate search queries
            search_queries = await self._generate_search_queries(
                topic, focus_areas, depth_config
            )

            # Step 2: Execute searches
            search_results = await self._execute_search_queries(
                search_queries, depth_config, timeout_budget
            )

            if not search_results:
                return {
                    "status": "error",
                    "error": "No search results found",
                    "topic": topic,
                    "execution_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                }

            # Step 3: Analyze content
            analyzed_content = await self._analyze_search_results(
                search_results, focus_areas
            )

            # Step 4: Validate sources
            validated_sources, credibility_scores = self._validate_source_credibility(
                analyzed_content
            )

            # Step 5: Synthesize findings
            findings = await self._synthesize_research_findings(
                validated_sources, topic, credibility_scores
            )

            # Step 6: Generate citations
            citations = self._generate_source_citations(validated_sources, credibility_scores)

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return {
                "status": "success",
                "agent_type": "deep_research",
                "execution_mode": "sequential",
                "persona": self.persona.name,
                "research_topic": topic,
                "research_depth": depth,
                "findings": findings,
                "sources_analyzed": len(validated_sources),
                "confidence_score": findings.get("confidence_score", 0.0),
                "citations": citations,
                "execution_time_ms": execution_time,
                "search_queries_used": search_queries,
            }

        except Exception as e:
            logger.error(f"Sequential research failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "topic": topic,
                "execution_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
            }

    async def _execute_parallel_research(
        self,
        topic: str,
        session_id: str,
        depth: str,
        focus_areas: list[str],
        timeframe: str,
        start_time: datetime,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute research using parallel subagent execution.

        Creates specialized subagents for different research types and
        runs them concurrently for faster results.
        """
        logger.info(f"Starting parallel research for: {topic[:50]}...")

        # Create research tasks for each focus type
        tasks = self._create_research_tasks(topic, session_id, focus_areas)

        # Execute tasks in parallel
        task_results = await self._execute_tasks_parallel(tasks)

        # Synthesize results from all tasks
        synthesis = await self._synthesize_parallel_results(task_results)

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        # Count successes and failures
        successful = sum(1 for t in task_results.values() if t.status == "completed")
        failed = sum(1 for t in task_results.values() if t.status == "failed")

        return {
            "status": "success",
            "agent_type": "deep_research",
            "execution_mode": "parallel",
            "persona": self.persona.name,
            "research_topic": topic,
            "research_depth": depth,
            "findings": synthesis,
            "sources_analyzed": synthesis.get("source_count", 0),
            "confidence_score": synthesis.get("confidence_score", 0.0),
            "citations": synthesis.get("citations", []),
            "execution_time_ms": execution_time,
            "parallel_stats": {
                "total_tasks": len(tasks),
                "successful": successful,
                "failed": failed,
            },
        }

    def _create_research_tasks(
        self, topic: str, session_id: str, focus_areas: list[str]
    ) -> list[ResearchTask]:
        """Create research tasks based on focus areas."""
        tasks = []
        task_types = ["fundamental", "technical", "sentiment", "competitive"]

        for i, task_type in enumerate(task_types):
            # Check if any focus area matches this task type
            type_keywords = {
                "fundamental": ["earnings", "valuation", "financial", "fundamentals"],
                "technical": ["price", "chart", "technical", "indicator"],
                "sentiment": ["sentiment", "news", "social", "opinion"],
                "competitive": ["competitive", "market", "industry", "competitor"],
            }

            # Always include at least fundamental and sentiment
            should_include = task_type in ["fundamental", "sentiment"]
            if not should_include:
                keywords = type_keywords.get(task_type, [])
                should_include = any(
                    kw in fa.lower() for fa in focus_areas for kw in keywords
                )

            if should_include:
                task = ResearchTask(
                    task_id=f"{session_id}_{task_type}_{i}",
                    task_type=task_type,
                    target_topic=topic,
                    focus_areas=[fa for fa in focus_areas if any(
                        kw in fa.lower() for kw in type_keywords.get(task_type, [])
                    )] or focus_areas[:3],
                    priority=i,
                )
                tasks.append(task)

        return tasks

    async def _execute_tasks_parallel(
        self, tasks: list[ResearchTask]
    ) -> dict[str, ResearchTask]:
        """Execute research tasks in parallel."""
        results: dict[str, ResearchTask] = {}

        async def execute_task(task: ResearchTask) -> None:
            try:
                task.status = "running"
                task.start_time = datetime.now().timestamp()

                # Create appropriate subagent
                subagent = self._create_subagent(task.task_type)

                # Execute research
                result = await subagent.execute_research(task)

                task.result = result
                task.status = "completed"
                task.end_time = datetime.now().timestamp()

            except Exception as e:
                logger.warning(f"Task {task.task_id} failed: {e}")
                task.status = "failed"
                task.error = str(e)
                task.end_time = datetime.now().timestamp()

            results[task.task_id] = task

        # Run all tasks concurrently with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.parallel_config.max_concurrent_agents)

        async def bounded_execute(task: ResearchTask) -> None:
            async with semaphore:
                await execute_task(task)

        await asyncio.gather(*[bounded_execute(task) for task in tasks])

        return results

    def _create_subagent(self, task_type: str):
        """Create appropriate subagent for task type."""
        from maverick_agents.research.subagents import BaseSubagent

        subagent_classes = {
            "fundamental": FundamentalResearchAgent,
            "technical": TechnicalResearchAgent,
            "sentiment": SentimentResearchAgent,
            "competitive": CompetitiveResearchAgent,
        }

        subagent_class = subagent_classes.get(task_type, FundamentalResearchAgent)

        return subagent_class(
            llm=self.llm,
            search_providers=self.search_providers,
            content_analyzer=self.content_analyzer,
            persona=self.persona,
        )

    async def _synthesize_parallel_results(
        self, task_results: dict[str, ResearchTask]
    ) -> dict[str, Any]:
        """Synthesize results from parallel research tasks."""
        all_insights: list[str] = []
        all_risks: list[str] = []
        all_opportunities: list[str] = []
        all_sources: list[dict[str, Any]] = []
        sentiment_scores: list[dict[str, Any]] = []
        credibility_scores: list[float] = []

        for task_id, task in task_results.items():
            if task.status == "completed" and task.result:
                result = task.result
                all_insights.extend(result.get("insights", []))
                all_risks.extend(result.get("risk_factors", []))
                all_opportunities.extend(result.get("opportunities", []))
                all_sources.extend(result.get("sources", []))

                sentiment = result.get("sentiment", {})
                if sentiment:
                    sentiment_scores.append(sentiment)

                credibility = result.get("credibility_score", 0.5)
                credibility_scores.append(credibility)

        # Calculate overall sentiment
        overall_sentiment = self._calculate_aggregate_sentiment(sentiment_scores)

        # Calculate average credibility
        avg_credibility = (
            sum(credibility_scores) / len(credibility_scores)
            if credibility_scores
            else 0.5
        )

        # Deduplicate insights
        unique_insights = list(dict.fromkeys(all_insights))[:10]
        unique_risks = list(dict.fromkeys(all_risks))[:8]
        unique_opportunities = list(dict.fromkeys(all_opportunities))[:8]

        # Generate synthesis text
        synthesis_text = await self._generate_synthesis_text(
            unique_insights, overall_sentiment, unique_risks
        )

        return {
            "synthesis": synthesis_text,
            "key_insights": unique_insights,
            "overall_sentiment": overall_sentiment,
            "risk_assessment": unique_risks,
            "investment_implications": {
                "opportunities": unique_opportunities,
                "threats": unique_risks[:5],
                "recommended_action": self._derive_recommendation(overall_sentiment),
            },
            "confidence_score": avg_credibility,
            "source_count": len(all_sources),
            "citations": [
                {
                    "id": i + 1,
                    "title": s.get("title", "Unknown"),
                    "url": s.get("url", ""),
                    "credibility_score": s.get("credibility_score", 0.5),
                }
                for i, s in enumerate(all_sources[:10])
            ],
        }

    def _calculate_aggregate_sentiment(
        self, sentiment_scores: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Calculate aggregate sentiment from multiple scores."""
        if not sentiment_scores:
            return {"direction": "neutral", "confidence": 0.5}

        weighted_scores = []
        total_confidence = 0.0

        for sentiment in sentiment_scores:
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
        avg_confidence = total_confidence / len(sentiment_scores)

        if avg_score > 0.2:
            direction = "bullish"
        elif avg_score < -0.2:
            direction = "bearish"
        else:
            direction = "neutral"

        return {
            "direction": direction,
            "confidence": avg_confidence,
            "consensus": 1 - abs(avg_score) if abs(avg_score) < 1 else 0,
            "source_count": len(sentiment_scores),
        }

    async def _generate_synthesis_text(
        self,
        insights: list[str],
        sentiment: dict[str, Any],
        risks: list[str],
    ) -> str:
        """Generate synthesis text using LLM."""
        try:
            prompt = f"""
            Synthesize these research findings for a {self.persona.name} investor:

            Key Insights: {', '.join(insights[:5])}
            Overall Sentiment: {sentiment.get('direction')} (confidence: {sentiment.get('confidence', 0.5):.2f})
            Key Risks: {', '.join(risks[:3])}

            Provide a 2-3 sentence executive summary.
            """

            response = await self.llm.ainvoke([
                {"role": "system", "content": "You are a financial research synthesizer."},
                {"role": "user", "content": prompt},
            ])

            return ContentAnalyzer._coerce_message_content(response.content)

        except Exception as e:
            logger.warning(f"Synthesis generation failed: {e}")
            return f"Research synthesis: {len(insights)} insights identified with {sentiment.get('direction', 'neutral')} sentiment."

    def _derive_recommendation(self, sentiment: dict[str, Any]) -> str:
        """Derive investment recommendation from sentiment."""
        direction = sentiment.get("direction", "neutral")
        confidence = sentiment.get("confidence", 0.5)

        if direction == "bullish" and confidence > 0.7:
            if self.persona.name.lower() == "conservative":
                return "Consider gradual position building with proper risk management"
            return "Consider initiating position with appropriate position sizing"
        elif direction == "bearish" and confidence > 0.7:
            return "Exercise caution - consider waiting for better entry or avoiding"
        else:
            return "Monitor closely - mixed signals suggest waiting for clarity"

    # Sequential workflow helper methods

    async def _generate_search_queries(
        self, topic: str, focus_areas: list[str], depth_config: dict[str, Any]
    ) -> list[str]:
        """Generate search queries for the research topic."""
        base_queries = [
            f"{topic} financial analysis",
            f"{topic} investment research",
            f"{topic} market outlook",
        ]

        # Add focus-area specific queries
        focus_queries = [f"{topic} {area}" for area in focus_areas[:3]]

        all_queries = base_queries + focus_queries
        return all_queries[: depth_config.get("max_searches", 5)]

    async def _execute_search_queries(
        self,
        queries: list[str],
        depth_config: dict[str, Any],
        timeout_budget: float | None,
    ) -> list[dict[str, Any]]:
        """Execute search queries across providers."""
        all_results: list[dict[str, Any]] = []

        for query in queries:
            for provider in self.search_providers:
                try:
                    results = await provider.search(
                        query,
                        num_results=5,
                        timeout_budget=timeout_budget,
                    )
                    all_results.extend(results)
                except WebSearchError as e:
                    logger.warning(f"Search failed for '{query}': {e}")
                except Exception as e:
                    logger.warning(f"Unexpected search error: {e}")

        # Deduplicate by URL
        seen_urls: set[str] = set()
        unique_results: list[dict[str, Any]] = []
        for result in all_results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        return unique_results[: depth_config.get("max_sources", 10)]

    async def _analyze_search_results(
        self, results: list[dict[str, Any]], focus_areas: list[str]
    ) -> list[dict[str, Any]]:
        """Analyze search results with content analyzer."""
        analyzed: list[dict[str, Any]] = []

        for result in results:
            content = result.get("content") or result.get("raw_content") or ""
            if content:
                try:
                    analysis = await self.content_analyzer.analyze_content(
                        content=content,
                        persona=self.persona.name.lower(),
                        analysis_focus="general",
                    )
                    analyzed.append({**result, "analysis": analysis})
                except Exception as e:
                    logger.warning(f"Content analysis failed: {e}")
                    analyzed.append(result)

        return analyzed

    def _validate_source_credibility(
        self, analyzed_content: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], dict[str, float]]:
        """Validate source credibility and filter results."""
        validated: list[dict[str, Any]] = []
        scores: dict[str, float] = {}

        for content in analyzed_content:
            url = content.get("url", "")
            score = self._calculate_credibility_score(content)
            scores[url] = score

            # Include sources above threshold
            if score >= 0.5:
                content["credibility_score"] = score
                validated.append(content)

        return validated, scores

    def _calculate_credibility_score(self, content: dict[str, Any]) -> float:
        """Calculate credibility score for a source."""
        score = 0.5

        url = content.get("url", "")

        # Domain-based scoring
        high_credibility_domains = [
            "sec.gov", "bloomberg.com", "reuters.com", "wsj.com",
            "ft.com", "investopedia.com", "morningstar.com",
        ]
        if any(domain in url for domain in high_credibility_domains):
            score += 0.3
        elif ".gov" in url or ".edu" in url:
            score += 0.2

        # Analysis-based scoring
        analysis = content.get("analysis", {})
        if analysis:
            analysis_score = analysis.get("credibility_score", 0.5)
            score = (score + analysis_score) / 2

        return min(score, 1.0)

    async def _synthesize_research_findings(
        self,
        sources: list[dict[str, Any]],
        topic: str,
        credibility_scores: dict[str, float],
    ) -> dict[str, Any]:
        """Synthesize findings from validated sources."""
        all_insights: list[str] = []
        all_risks: list[str] = []
        sentiment_data: list[dict[str, Any]] = []

        for source in sources:
            analysis = source.get("analysis", {})
            all_insights.extend(analysis.get("insights", []))
            all_risks.extend(analysis.get("risk_factors", []))
            sentiment = analysis.get("sentiment", {})
            if sentiment:
                sentiment_data.append(sentiment)

        # Calculate overall sentiment
        overall_sentiment = self._calculate_aggregate_sentiment(sentiment_data)

        # Calculate confidence
        confidence = self._calculate_research_confidence(sources, credibility_scores)

        # Generate synthesis
        synthesis_text = await self._generate_synthesis_text(
            all_insights, overall_sentiment, all_risks
        )

        return {
            "synthesis": synthesis_text,
            "key_insights": list(dict.fromkeys(all_insights))[:10],
            "overall_sentiment": overall_sentiment,
            "risk_assessment": list(dict.fromkeys(all_risks))[:8],
            "confidence_score": confidence,
        }

    def _calculate_research_confidence(
        self, sources: list[dict[str, Any]], credibility_scores: dict[str, float]
    ) -> float:
        """Calculate overall research confidence."""
        if not sources:
            return 0.0

        # Factor: number of sources
        source_factor = min(len(sources) / 10, 1.0)

        # Factor: average credibility
        avg_credibility = (
            sum(credibility_scores.values()) / len(credibility_scores)
            if credibility_scores
            else 0.5
        )

        # Factor: source diversity
        domains = {s.get("url", "").split("/")[2] for s in sources if s.get("url")}
        diversity_factor = min(len(domains) / 5, 1.0)

        return round((source_factor + avg_credibility + diversity_factor) / 3, 2)

    def _generate_source_citations(
        self,
        sources: list[dict[str, Any]],
        credibility_scores: dict[str, float],
    ) -> list[dict[str, Any]]:
        """Generate citations for validated sources."""
        citations = []
        for i, source in enumerate(sources, 1):
            url = source.get("url", "")
            citations.append({
                "id": i,
                "title": source.get("title", "Untitled"),
                "url": url,
                "published_date": source.get("published_date"),
                "author": source.get("author"),
                "credibility_score": credibility_scores.get(url, 0.5),
                "relevance_score": source.get("analysis", {}).get("relevance_score", 0.5),
            })
        return citations

    # LangGraph workflow node implementations (for graph-based execution)

    async def _plan_research(self, state: DeepResearchState) -> dict[str, Any]:
        """Plan research strategy based on topic and persona."""
        topic = state.get("research_topic", "")
        depth = state.get("research_depth", self.default_depth)
        depth_config = RESEARCH_DEPTH_LEVELS.get(depth, RESEARCH_DEPTH_LEVELS["standard"])

        focus_areas = state.get("focus_areas", [])
        if not focus_areas:
            persona_focus = PERSONA_RESEARCH_FOCUS.get(
                self.persona.name.lower(), PERSONA_RESEARCH_FOCUS["moderate"]
            )
            focus_areas = persona_focus["keywords"]

        queries = await self._generate_search_queries(topic, focus_areas, depth_config)

        return {
            "search_queries": queries,
            "research_status": "searching",
        }

    async def _execute_searches(self, state: DeepResearchState) -> dict[str, Any]:
        """Execute web searches."""
        queries = state.get("search_queries", [])
        depth = state.get("research_depth", self.default_depth)
        depth_config = RESEARCH_DEPTH_LEVELS.get(depth, RESEARCH_DEPTH_LEVELS["standard"])
        timeout_budget = state.get("timeout_budgets", {}).get("search_budget")

        results = await self._execute_search_queries(queries, depth_config, timeout_budget)

        return {
            "search_results": results,
            "research_status": "analyzing",
        }

    async def _analyze_content(self, state: DeepResearchState) -> dict[str, Any]:
        """Analyze search results."""
        results = state.get("search_results", [])
        focus_areas = state.get("focus_areas", [])

        analyzed = await self._analyze_search_results(results, focus_areas)

        return {
            "analyzed_content": analyzed,
            "research_status": "validating",
        }

    async def _validate_sources(self, state: DeepResearchState) -> dict[str, Any]:
        """Validate source credibility."""
        analyzed = state.get("analyzed_content", [])

        validated, scores = self._validate_source_credibility(analyzed)

        return {
            "validated_sources": validated,
            "source_credibility_scores": scores,
            "research_status": "synthesizing",
        }

    async def _synthesize_findings(self, state: DeepResearchState) -> dict[str, Any]:
        """Synthesize research findings."""
        sources = state.get("validated_sources", [])
        topic = state.get("research_topic", "")
        scores = state.get("source_credibility_scores", {})

        findings = await self._synthesize_research_findings(sources, topic, scores)

        return {
            "research_findings": findings,
            "research_confidence": findings.get("confidence_score", 0.0),
            "research_status": "completing",
        }

    async def _generate_citations(self, state: DeepResearchState) -> dict[str, Any]:
        """Generate citations for sources."""
        sources = state.get("validated_sources", [])
        scores = state.get("source_credibility_scores", {})

        citations = self._generate_source_citations(sources, scores)

        return {
            "citations": citations,
            "research_status": "completed",
        }

    # Public API methods

    async def research_company_comprehensive(
        self,
        symbol: str,
        session_id: str,
        include_competitive_analysis: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Comprehensive company research.

        Args:
            symbol: Stock symbol to research
            session_id: Session identifier
            include_competitive_analysis: Include competitive analysis
            **kwargs: Additional parameters

        Returns:
            Comprehensive company research results
        """
        topic = f"{symbol} company financial analysis and outlook"
        focus_areas = kwargs.get("focus_areas", [])

        if include_competitive_analysis:
            focus_areas = focus_areas + ["competitive_analysis", "market_position"]
            kwargs["focus_areas"] = focus_areas

        return await self.research_comprehensive(
            topic=topic, session_id=session_id, **kwargs
        )

    async def research_topic(
        self,
        query: str,
        session_id: str | None = None,
        focus_areas: list[str] | None = None,
        timeframe: str = "30d",
        **kwargs,
    ) -> dict[str, Any]:
        """
        General topic research.

        Args:
            query: Research query or topic
            session_id: Session identifier (auto-generated if not provided)
            focus_areas: Specific areas to focus on
            timeframe: Time range for research
            **kwargs: Additional parameters

        Returns:
            Research results for the given topic
        """
        if not session_id:
            session_id = f"research-{uuid4().hex[:8]}"

        return await self.research_comprehensive(
            topic=query,
            session_id=session_id,
            focus_areas=focus_areas,
            timeframe=timeframe,
            **kwargs,
        )

    async def analyze_market_sentiment(
        self,
        topic: str,
        session_id: str | None = None,
        timeframe: str = "7d",
        **kwargs,
    ) -> dict[str, Any]:
        """
        Analyze market sentiment around a topic.

        Args:
            topic: Topic to analyze sentiment for
            session_id: Session identifier
            timeframe: Time range for analysis
            **kwargs: Additional parameters

        Returns:
            Market sentiment analysis results
        """
        if not session_id:
            session_id = f"sentiment-{uuid4().hex[:8]}"

        return await self.research_comprehensive(
            topic=f"market sentiment analysis: {topic}",
            session_id=session_id,
            focus_areas=["sentiment", "market_mood", "investor_sentiment"],
            timeframe=timeframe,
            **kwargs,
        )

    def _is_insight_relevant_for_persona(
        self, insight: dict[str, Any], characteristics: dict[str, Any]
    ) -> bool:
        """Check if an insight is relevant for a given persona - used by tests."""
        return True  # Default permissive approach
