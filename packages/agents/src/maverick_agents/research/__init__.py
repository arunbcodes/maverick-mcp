"""
Deep research agents and subagents.

Provides multi-agent research capabilities with parallel execution,
content analysis, and persona-aware recommendations.
"""

from maverick_agents.research.config import (
    PERSONA_RESEARCH_FOCUS,
    RESEARCH_DEPTH_LEVELS,
    ResearchDepth,
    ResearchDepthConfig,
    get_depth_config,
    get_persona_focus,
    get_persona_keywords,
    get_persona_sources,
)
from maverick_agents.research.content_analyzer import ContentAnalyzer
from maverick_agents.research.coordinator import (
    ConversationStoreProtocol,
    DeepResearchAgent,
    DefaultParallelConfig,
    ParallelConfigProtocol,
    ParallelOrchestratorProtocol,
    ParallelResearchResult,
    TaskDistributorProtocol,
)
from maverick_agents.research.providers import (
    DefaultPerformanceSettings,
    DefaultSettings,
    ExaSearchProvider,
    SettingsProtocol,
    TavilySearchProvider,
    WebSearchError,
    WebSearchProvider,
    get_cached_search_provider,
)
from maverick_agents.research.subagents import (
    BaseSubagent,
    CompetitiveResearchAgent,
    FundamentalResearchAgent,
    LLMProtocol,
    ResearchTask,
    SentimentResearchAgent,
    TechnicalResearchAgent,
)

# Optimization utilities
from maverick_agents.research.optimization import (
    AdaptiveModelSelector,
    ConfidenceTracker,
    IntelligentContentFilter,
    ModelConfiguration,
    OptimizedPromptEngine,
    ParallelLLMProcessor,
    ProgressiveTokenBudgeter,
    ResearchPhase,
    TokenAllocation,
)

# Optimized agents
from maverick_agents.research.optimized import (
    OptimizedContentAnalyzer,
    OptimizedDeepResearchAgent,
    create_optimized_research_agent,
)

__all__ = [
    # Config
    "RESEARCH_DEPTH_LEVELS",
    "PERSONA_RESEARCH_FOCUS",
    "ResearchDepth",
    "ResearchDepthConfig",
    "get_depth_config",
    "get_persona_focus",
    "get_persona_keywords",
    "get_persona_sources",
    # Content analysis
    "ContentAnalyzer",
    # Coordinator (main agent)
    "DeepResearchAgent",
    "DefaultParallelConfig",
    "ParallelResearchResult",
    "ParallelConfigProtocol",
    "ParallelOrchestratorProtocol",
    "TaskDistributorProtocol",
    "ConversationStoreProtocol",
    # Providers
    "WebSearchProvider",
    "WebSearchError",
    "ExaSearchProvider",
    "TavilySearchProvider",
    "SettingsProtocol",
    "DefaultSettings",
    "DefaultPerformanceSettings",
    "get_cached_search_provider",
    # Subagents
    "BaseSubagent",
    "ResearchTask",
    "LLMProtocol",
    "FundamentalResearchAgent",
    "TechnicalResearchAgent",
    "SentimentResearchAgent",
    "CompetitiveResearchAgent",
    # Optimization utilities
    "AdaptiveModelSelector",
    "ModelConfiguration",
    "ProgressiveTokenBudgeter",
    "ResearchPhase",
    "TokenAllocation",
    "ConfidenceTracker",
    "IntelligentContentFilter",
    "OptimizedPromptEngine",
    "ParallelLLMProcessor",
    # Optimized agents
    "OptimizedContentAnalyzer",
    "OptimizedDeepResearchAgent",
    "create_optimized_research_agent",
]
