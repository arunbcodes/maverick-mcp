"""
Maverick Capabilities Package.

Provides capability registry, orchestration abstraction, audit logging,
and async task queue for MaverickMCP.

Features:
- Python-based capability registry (type-safe, IDE-friendly)
- Orchestrator protocol for swappable execution (LangGraph today, AgentField later)
- Audit logging for compliance and debugging
- Async task queue for long-running operations
"""

from maverick_capabilities.models import (
    Capability,
    CapabilityGroup,
    ExecutionMode,
    ExecutionConfig,
    MCPConfig,
    APIConfig,
    UIConfig,
    AgentConfig,
    AuditConfig,
)
from maverick_capabilities.registry import (
    CapabilityRegistry,
    get_registry,
    reset_registry,
)
from maverick_capabilities.orchestration import (
    Orchestrator,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
    get_orchestrator,
    set_orchestrator,
    reset_orchestrator,
)
from maverick_capabilities.audit import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    get_audit_logger,
    set_audit_logger,
    reset_audit_logger,
)

__all__ = [
    # Models
    "Capability",
    "CapabilityGroup",
    "ExecutionMode",
    "ExecutionConfig",
    "MCPConfig",
    "APIConfig",
    "UIConfig",
    "AgentConfig",
    "AuditConfig",
    # Registry
    "CapabilityRegistry",
    "get_registry",
    "reset_registry",
    # Orchestration
    "Orchestrator",
    "ExecutionContext",
    "ExecutionResult",
    "ExecutionStatus",
    "get_orchestrator",
    "set_orchestrator",
    "reset_orchestrator",
    # Audit
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "get_audit_logger",
    "set_audit_logger",
    "reset_audit_logger",
]
