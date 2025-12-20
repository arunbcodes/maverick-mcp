"""
Orchestrator Factory.

Provides factory functions for creating and accessing orchestrators.
This is the entry point for getting an orchestrator instance.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from maverick_capabilities.orchestration.protocols import Orchestrator
from maverick_capabilities.orchestration.service_orchestrator import ServiceOrchestrator


class OrchestratorType(str, Enum):
    """Available orchestrator types."""

    SERVICE = "service"  # Direct service calls (default)
    LANGGRAPH = "langgraph"  # LangGraph-based (future)
    AGENTFIELD = "agentfield"  # AgentField control plane (future)


# Global orchestrator instance
_orchestrator: Orchestrator | None = None
_orchestrator_type: OrchestratorType = OrchestratorType.SERVICE


def create_orchestrator(
    orchestrator_type: OrchestratorType = OrchestratorType.SERVICE,
    service_factory: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Orchestrator:
    """
    Create an orchestrator instance.

    Args:
        orchestrator_type: Type of orchestrator to create
        service_factory: Map of service names to instances
        **kwargs: Additional arguments for specific orchestrator types

    Returns:
        Orchestrator instance

    Raises:
        ValueError: If orchestrator type is not supported
    """
    if orchestrator_type == OrchestratorType.SERVICE:
        return ServiceOrchestrator(service_factory=service_factory)

    elif orchestrator_type == OrchestratorType.LANGGRAPH:
        # Future: LangGraph orchestrator
        raise NotImplementedError(
            "LangGraph orchestrator is not yet implemented. "
            "Use OrchestratorType.SERVICE for now."
        )

    elif orchestrator_type == OrchestratorType.AGENTFIELD:
        # Future: AgentField orchestrator
        raise NotImplementedError(
            "AgentField orchestrator is not yet implemented. "
            "Use OrchestratorType.SERVICE for now."
        )

    else:
        raise ValueError(f"Unknown orchestrator type: {orchestrator_type}")


def get_orchestrator() -> Orchestrator:
    """
    Get the global orchestrator instance.

    Creates a default ServiceOrchestrator if none exists.

    Returns:
        The global orchestrator instance
    """
    global _orchestrator

    if _orchestrator is None:
        _orchestrator = create_orchestrator(_orchestrator_type)

    return _orchestrator


def set_orchestrator(
    orchestrator: Orchestrator | None = None,
    orchestrator_type: OrchestratorType | None = None,
    **kwargs: Any,
) -> None:
    """
    Set the global orchestrator instance.

    Args:
        orchestrator: Orchestrator instance to use, or None to create one
        orchestrator_type: Type of orchestrator to create if orchestrator is None
        **kwargs: Additional arguments for orchestrator creation
    """
    global _orchestrator, _orchestrator_type

    if orchestrator is not None:
        _orchestrator = orchestrator
    elif orchestrator_type is not None:
        _orchestrator_type = orchestrator_type
        _orchestrator = create_orchestrator(orchestrator_type, **kwargs)


def reset_orchestrator() -> None:
    """Reset the global orchestrator (for testing)."""
    global _orchestrator
    _orchestrator = None
