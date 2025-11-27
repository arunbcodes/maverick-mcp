"""
Maverick Agents Package.

AI/LLM agent orchestration for Maverick stock analysis.
Provides research agents, market analysis agents, and multi-agent coordination.
"""

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
from maverick_agents.personas import (
    DEFAULT_PERSONA_PARAMS,
    INVESTOR_PERSONAS,
    InvestorPersona,
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
from maverick_agents.analyzers import MarketAnalysisAgent, TechnicalAnalysisAgent
from maverick_agents.tools import DEFAULT_CACHE_TTL_SECONDS, PersonaAwareTool

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
]
