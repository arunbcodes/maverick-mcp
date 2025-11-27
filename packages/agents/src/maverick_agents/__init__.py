"""
Maverick Agents Package.

AI/LLM agent orchestration for Maverick stock analysis.
Provides research agents, market analysis agents, and multi-agent coordination.
"""

from maverick_agents.analyzers import MarketAnalysisAgent, TechnicalAnalysisAgent
from maverick_agents.base import BaseAgentState, PersonaAwareAgent
from maverick_agents.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitState,
    circuit_breaker,
    circuit_manager,
)
from maverick_agents.exceptions import (
    AgentError,
    AgentExecutionError,
    AgentInitializationError,
    AgentTimeoutError,
    QueryClassificationError,
    SynthesisError,
)
from maverick_agents.llm import (
    MODEL_PROFILES,
    ModelProfile,
    OpenRouterProvider,
    TaskType,
    check_ollama_available,
    get_llm,
    get_ollama_llm,
    get_openrouter_llm,
    list_ollama_models,
)
from maverick_agents.memory import ConversationStore, MemoryStore, UserMemoryStore
from maverick_agents.personas import (
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_PERSONA_PARAMS,
    INVESTOR_PERSONAS,
    InvestorPersona,
    PersonaAwareTool,
    create_default_personas,
    get_persona,
)
from maverick_agents.supervisor import (
    AGENT_WEIGHTS,
    CLASSIFICATION_KEYWORDS,
    ROUTING_MATRIX,
    QueryClassifier,
    ResultSynthesizer,
    SupervisorAgent,
    classify_query_by_keywords,
    get_agent_weights,
    get_routing_config,
)
from maverick_agents.tools import (
    MarketBreadthTool,
    NewsSentimentTool,
    SectorSentimentTool,
)

__all__ = [
    # Base classes
    "BaseAgentState",
    "PersonaAwareAgent",
    # Personas
    "InvestorPersona",
    "INVESTOR_PERSONAS",
    "DEFAULT_PERSONA_PARAMS",
    "create_default_personas",
    "get_persona",
    # Tools
    "PersonaAwareTool",
    "DEFAULT_CACHE_TTL_SECONDS",
    "NewsSentimentTool",
    "MarketBreadthTool",
    "SectorSentimentTool",
    # Circuit breaker
    "CircuitBreaker",
    "CircuitBreakerManager",
    "CircuitState",
    "circuit_breaker",
    "circuit_manager",
    # Exceptions
    "AgentError",
    "AgentInitializationError",
    "AgentExecutionError",
    "QueryClassificationError",
    "AgentTimeoutError",
    "SynthesisError",
    # Supervisor
    "SupervisorAgent",
    "QueryClassifier",
    "ResultSynthesizer",
    "ROUTING_MATRIX",
    "AGENT_WEIGHTS",
    "CLASSIFICATION_KEYWORDS",
    "get_routing_config",
    "get_agent_weights",
    "classify_query_by_keywords",
    # Analyzers
    "TechnicalAnalysisAgent",
    "MarketAnalysisAgent",
    # LLM providers
    "TaskType",
    "ModelProfile",
    "MODEL_PROFILES",
    "OpenRouterProvider",
    "get_openrouter_llm",
    "get_ollama_llm",
    "check_ollama_available",
    "list_ollama_models",
    "get_llm",
    # Memory stores
    "MemoryStore",
    "ConversationStore",
    "UserMemoryStore",
]
