"""
LLM provider interfaces.

This module defines abstract interfaces for LLM operations and AI agents.
"""

from enum import Enum
from typing import Any, AsyncIterator, Protocol, runtime_checkable


class TaskType(str, Enum):
    """Task types for LLM routing and model selection.

    These task types are used by:
    - ILLMProvider for routing requests to appropriate models
    - OpenRouterProvider for intelligent model selection
    - Research agents for adaptive processing
    """

    # Analysis tasks
    DEEP_RESEARCH = "deep_research"
    MARKET_ANALYSIS = "market_analysis"
    TECHNICAL_ANALYSIS = "technical_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    RISK_ASSESSMENT = "risk_assessment"

    # Synthesis tasks
    RESULT_SYNTHESIS = "result_synthesis"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"

    # Query processing
    QUERY_CLASSIFICATION = "query_classification"
    QUICK_ANSWER = "quick_answer"

    # Complex reasoning
    COMPLEX_REASONING = "complex_reasoning"
    MULTI_AGENT_ORCHESTRATION = "multi_agent_orchestration"

    # Default/general
    GENERAL = "general"

    # Legacy aliases (for backward compatibility with ILLMProvider interface)
    ANALYSIS = "analysis"
    SENTIMENT = "sentiment"
    SUMMARY = "summary"
    RESEARCH = "research"
    CHAT = "chat"
    EXTRACTION = "extraction"
    CLASSIFICATION = "classification"


@runtime_checkable
class ILLMProvider(Protocol):
    """
    Interface for LLM providers.

    This interface defines the contract for interacting with LLM services
    like OpenRouter, Anthropic, OpenAI, or Ollama.

    Implemented by: maverick-agents (OpenRouterProvider, OllamaProvider)
    """

    async def complete(
        self,
        prompt: str,
        task_type: TaskType = TaskType.CHAT,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate completion.

        Args:
            prompt: Input prompt
            task_type: Type of task (affects model selection)
            max_tokens: Maximum response tokens
            temperature: Sampling temperature (0-2)
            system_prompt: Optional system prompt

        Returns:
            Generated text
        """
        ...

    async def complete_stream(
        self,
        prompt: str,
        task_type: TaskType = TaskType.CHAT,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """
        Generate streaming completion.

        Args:
            prompt: Input prompt
            task_type: Type of task
            max_tokens: Maximum response tokens
            temperature: Sampling temperature

        Yields:
            Text chunks as they're generated
        """
        ...

    async def analyze_sentiment(
        self,
        text: str,
    ) -> dict[str, Any]:
        """
        Analyze text sentiment.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with:
            - sentiment: "positive", "negative", "neutral"
            - score: Confidence score (0-1)
            - reasoning: Explanation of sentiment
        """
        ...

    async def extract_entities(
        self,
        text: str,
        entity_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Extract named entities from text.

        Args:
            text: Text to analyze
            entity_types: Types of entities to extract
                         (e.g., ["company", "person", "money"])

        Returns:
            List of extracted entities with type and value
        """
        ...

    def get_model_for_task(self, task_type: TaskType) -> str:
        """
        Get recommended model for task type.

        Args:
            task_type: Type of task

        Returns:
            Model identifier string
        """
        ...

    async def get_usage_stats(self) -> dict[str, Any]:
        """
        Get token usage statistics.

        Returns:
            Dictionary with:
            - total_tokens: Total tokens used
            - prompt_tokens: Prompt tokens
            - completion_tokens: Completion tokens
            - cost_estimate: Estimated cost in USD
        """
        ...


@runtime_checkable
class IResearchAgent(Protocol):
    """
    Interface for research agents.

    This interface defines the contract for AI-powered research
    that combines web search with LLM analysis.

    Implemented by: maverick-agents (DeepResearchAgent, OptimizedResearchAgent)
    """

    async def research_topic(
        self,
        query: str,
        scope: str = "standard",
        max_sources: int = 10,
        timeframe: str = "1m",
    ) -> dict[str, Any]:
        """
        Research a topic using web search and analysis.

        Args:
            query: Research query
            scope: Research depth ("basic", "standard", "comprehensive", "exhaustive")
            max_sources: Maximum sources to analyze
            timeframe: Time range for search ("1d", "1w", "1m", "3m", "1y")

        Returns:
            Dictionary with:
            - summary: Executive summary
            - insights: Key insights list
            - sources: List of sources with analysis
            - sentiment: Overall sentiment assessment
            - confidence: Confidence score (0-1)
            - metadata: Research metadata
        """
        ...

    async def analyze_company(
        self,
        symbol: str,
        include_competitors: bool = False,
        include_financials: bool = True,
    ) -> dict[str, Any]:
        """
        Analyze a specific company.

        Args:
            symbol: Stock ticker symbol
            include_competitors: Include competitive analysis
            include_financials: Include financial analysis

        Returns:
            Dictionary with:
            - company_overview: Company summary
            - financial_analysis: Financial metrics and trends
            - competitive_position: Market position analysis
            - risks: Identified risk factors
            - opportunities: Growth opportunities
            - sentiment: Market sentiment
            - recommendation: Investment recommendation
        """
        ...

    async def analyze_market_sentiment(
        self,
        topic: str,
        timeframe: str = "1w",
    ) -> dict[str, Any]:
        """
        Analyze market sentiment for topic.

        Args:
            topic: Topic to analyze (company, sector, theme)
            timeframe: Analysis time range

        Returns:
            Dictionary with:
            - overall_sentiment: "bullish", "bearish", "neutral"
            - sentiment_score: Numeric score (-1 to 1)
            - key_themes: Main themes identified
            - news_summary: Summary of recent news
            - social_sentiment: Social media sentiment
            - confidence: Confidence score
        """
        ...

    async def get_research_status(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        """
        Get status of ongoing research.

        Args:
            session_id: Research session identifier

        Returns:
            Dictionary with:
            - status: "running", "completed", "failed"
            - progress: Progress percentage (0-100)
            - current_step: Current step description
            - estimated_completion: Estimated completion time
        """
        ...
