"""
Capability models for the registry.

These Pydantic models define the structure of capabilities,
providing type safety and IDE support.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Type


class ExecutionMode(str, Enum):
    """How the capability should be executed."""

    SYNC = "sync"  # Executes and returns immediately
    ASYNC = "async"  # Returns task ID, executes in background
    STREAMING = "streaming"  # Streams results back


class CapabilityGroup(str, Enum):
    """Logical grouping of capabilities."""

    SCREENING = "screening"
    PORTFOLIO = "portfolio"
    TECHNICAL = "technical"
    DATA = "data"
    RESEARCH = "research"
    BACKTESTING = "backtesting"
    INDIA = "india"
    RISK = "risk"
    ALERTS = "alerts"
    EXPORT = "export"


@dataclass
class ExecutionConfig:
    """Configuration for capability execution."""

    mode: ExecutionMode = ExecutionMode.SYNC
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: float = 1.0

    # For async execution
    queue: str = "default"
    priority: int = 5  # 1 = highest, 10 = lowest

    # Caching
    cache_enabled: bool = False
    cache_ttl_seconds: int = 300


@dataclass
class MCPConfig:
    """Configuration for MCP tool exposure."""

    expose: bool = True
    tool_name: str = ""
    category: str = ""
    description_override: str | None = None

    # For async tools
    async_pattern: str | None = None  # "polling" or "streaming"
    status_tool: str | None = None  # Tool name to check status


@dataclass
class APIConfig:
    """Configuration for REST API exposure."""

    expose: bool = True
    path: str = ""
    method: str = "POST"

    # For async endpoints
    status_path: str | None = None


@dataclass
class UIConfig:
    """Configuration for UI exposure."""

    expose: bool = False
    component: str | None = None
    route: str | None = None
    menu_group: str | None = None
    menu_label: str | None = None
    menu_order: int = 100
    permissions: list[str] = field(default_factory=list)


@dataclass
class AgentConfig:
    """Configuration for agent invocation."""

    can_invoke: bool = True
    agent_types: list[str] = field(default_factory=list)
    is_agent: bool = False  # This capability IS an agent
    orchestrator: str | None = None  # "langgraph", "agentfield", etc.


@dataclass
class AuditConfig:
    """Configuration for audit logging."""

    log: bool = True
    log_input: bool = True
    log_output: bool = False  # Can be expensive for large outputs
    pii_fields: list[str] = field(default_factory=list)
    retention_days: int = 90


@dataclass
class Capability:
    """
    A single capability definition.

    This is the core unit of the capability registry. Each capability
    represents a discrete piece of functionality that can be exposed
    via MCP tools, REST API, and/or UI.

    Example:
        >>> from maverick_services import ScreeningService
        >>> cap = Capability(
        ...     id="run_screener",
        ...     title="Run Stock Screener",
        ...     description="Screen stocks based on filters",
        ...     group=CapabilityGroup.SCREENING,
        ...     service_class=ScreeningService,
        ...     method_name="get_maverick_stocks",
        ...     mcp=MCPConfig(tool_name="screening_run_screener"),
        ... )
    """

    # Identity
    id: str
    title: str
    description: str
    group: CapabilityGroup

    # Backend binding - actual class and method
    service_class: Type[Any]
    method_name: str

    # Alternative: callable directly (for simple functions)
    handler: Callable[..., Any] | None = None

    # Configuration
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    mcp: MCPConfig | None = None
    api: APIConfig | None = None
    ui: UIConfig | None = None
    agent: AgentConfig | None = None
    audit: AuditConfig = field(default_factory=AuditConfig)

    # Metadata
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    deprecated: bool = False
    deprecation_message: str | None = None

    def __post_init__(self):
        """Validate and set defaults."""
        # Auto-generate MCP tool name if not set
        if self.mcp and not self.mcp.tool_name:
            self.mcp.tool_name = f"{self.group.value}_{self.id}"

        # Auto-generate API path if not set
        if self.api and not self.api.path:
            self.api.path = f"/api/v1/{self.group.value}/{self.id}"

    @property
    def is_async(self) -> bool:
        """Check if this capability runs asynchronously."""
        return self.execution.mode == ExecutionMode.ASYNC

    @property
    def is_streaming(self) -> bool:
        """Check if this capability streams results."""
        return self.execution.mode == ExecutionMode.STREAMING

    def get_method(self, service_instance: Any) -> Callable[..., Any]:
        """Get the method to call on the service instance."""
        if self.handler:
            return self.handler
        return getattr(service_instance, self.method_name)

    def to_dict(self) -> dict[str, Any]:
        """Export capability as dictionary (for JSON serialization)."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "group": self.group.value,
            "service": self.service_class.__name__,
            "method": self.method_name,
            "execution": {
                "mode": self.execution.mode.value,
                "timeout_seconds": self.execution.timeout_seconds,
                "cache_enabled": self.execution.cache_enabled,
            },
            "mcp": {
                "expose": self.mcp.expose,
                "tool_name": self.mcp.tool_name,
            }
            if self.mcp
            else None,
            "api": {
                "expose": self.api.expose,
                "path": self.api.path,
                "method": self.api.method,
            }
            if self.api
            else None,
            "ui": {
                "expose": self.ui.expose,
                "component": self.ui.component,
                "route": self.ui.route,
            }
            if self.ui
            else None,
            "is_async": self.is_async,
            "version": self.version,
            "deprecated": self.deprecated,
        }
