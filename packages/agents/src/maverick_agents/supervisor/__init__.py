"""
Supervisor Agent.

Multi-agent orchestration and coordination.
"""

from maverick_agents.supervisor.agent import SupervisorAgent
from maverick_agents.supervisor.classifier import QueryClassifier
from maverick_agents.supervisor.routing import (
    AGENT_WEIGHTS,
    CLASSIFICATION_KEYWORDS,
    ROUTING_MATRIX,
    classify_query_by_keywords,
    get_agent_weights,
    get_routing_config,
)
from maverick_agents.supervisor.synthesizer import ResultSynthesizer

__all__ = [
    # Main agent
    "SupervisorAgent",
    # Classification
    "QueryClassifier",
    # Synthesis
    "ResultSynthesizer",
    # Routing configuration
    "ROUTING_MATRIX",
    "AGENT_WEIGHTS",
    "CLASSIFICATION_KEYWORDS",
    "get_routing_config",
    "get_agent_weights",
    "classify_query_by_keywords",
]
