"""
Orchestration module.

Provides the orchestrator protocol and implementations for
executing capabilities through different backends.
"""

from maverick_capabilities.orchestration.protocols import (
    Orchestrator,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
)
from maverick_capabilities.orchestration.service_orchestrator import (
    ServiceOrchestrator,
)
from maverick_capabilities.orchestration.factory import (
    get_orchestrator,
    create_orchestrator,
    set_orchestrator,
    reset_orchestrator,
    OrchestratorType,
)

__all__ = [
    # Protocols
    "Orchestrator",
    "ExecutionContext",
    "ExecutionResult",
    "ExecutionStatus",
    # Implementations
    "ServiceOrchestrator",
    # Factory
    "get_orchestrator",
    "create_orchestrator",
    "set_orchestrator",
    "reset_orchestrator",
    "OrchestratorType",
]
