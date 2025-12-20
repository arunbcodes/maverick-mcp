"""
Orchestration protocols.

Defines the abstract interface for capability execution.
This allows swapping between different orchestration backends
(e.g., direct service calls, LangGraph, AgentField).
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, AsyncIterator, Callable, Protocol, runtime_checkable
from uuid import UUID, uuid4


class ExecutionStatus(str, Enum):
    """Status of a capability execution."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class ExecutionContext:
    """
    Context for capability execution.

    Contains metadata about the execution that can be used
    for logging, tracing, and debugging.
    """

    execution_id: UUID = field(default_factory=uuid4)
    capability_id: str = ""
    user_id: str | None = None
    correlation_id: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # For async execution
    webhook_url: str | None = None
    callback: Callable[["ExecutionResult"], None] | None = None

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    # Service instance override (for dependency injection)
    service_instance: Any | None = None


@dataclass
class ExecutionResult:
    """
    Result of a capability execution.

    Contains the result data, status, timing information,
    and any error details.
    """

    execution_id: UUID
    capability_id: str
    status: ExecutionStatus

    # Result data
    result: Any | None = None
    error: str | None = None
    error_type: str | None = None

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Progress tracking (for async)
    progress_percent: int = 0
    progress_message: str | None = None

    # Trace (for debugging)
    trace: list[dict[str, Any]] = field(default_factory=list)

    @property
    def duration_ms(self) -> int | None:
        """Get execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None

    @property
    def is_complete(self) -> bool:
        """Check if execution is complete (success or failure)."""
        return self.status in (
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMEOUT,
        )

    @property
    def is_success(self) -> bool:
        """Check if execution succeeded."""
        return self.status == ExecutionStatus.COMPLETED

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "execution_id": str(self.execution_id),
            "capability_id": self.capability_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "error_type": self.error_type,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "duration_ms": self.duration_ms,
            "progress_percent": self.progress_percent,
            "progress_message": self.progress_message,
        }


@runtime_checkable
class Orchestrator(Protocol):
    """
    Protocol for capability orchestration.

    This is the core abstraction that allows swapping between
    different execution backends. Implementations include:

    - ServiceOrchestrator: Direct service method calls (current)
    - LangGraphOrchestrator: LangGraph-based agent execution
    - AgentFieldOrchestrator: AgentField control plane (future)

    Example:
        >>> orchestrator = get_orchestrator()
        >>> result = await orchestrator.execute("run_screener", {"strategy": "bullish"})
        >>> if result.is_success:
        ...     print(result.result)
    """

    @abstractmethod
    async def execute(
        self,
        capability_id: str,
        input_data: dict[str, Any],
        context: ExecutionContext | None = None,
    ) -> ExecutionResult:
        """
        Execute a capability synchronously.

        Args:
            capability_id: The capability to execute
            input_data: Input parameters for the capability
            context: Optional execution context

        Returns:
            ExecutionResult with the result or error
        """
        ...

    @abstractmethod
    async def execute_async(
        self,
        capability_id: str,
        input_data: dict[str, Any],
        context: ExecutionContext | None = None,
    ) -> ExecutionResult:
        """
        Start async execution.

        Returns immediately with a pending result containing
        the execution_id. Use get_status() to check progress.

        Args:
            capability_id: The capability to execute
            input_data: Input parameters for the capability
            context: Optional execution context

        Returns:
            ExecutionResult with status=PENDING and execution_id
        """
        ...

    @abstractmethod
    async def get_status(
        self,
        execution_id: UUID,
    ) -> ExecutionResult:
        """
        Get status of an async execution.

        Args:
            execution_id: The execution to check

        Returns:
            ExecutionResult with current status
        """
        ...

    @abstractmethod
    async def cancel(
        self,
        execution_id: UUID,
    ) -> bool:
        """
        Cancel a running or pending execution.

        Args:
            execution_id: The execution to cancel

        Returns:
            True if cancelled, False if not found or already complete
        """
        ...

    @abstractmethod
    async def stream(
        self,
        capability_id: str,
        input_data: dict[str, Any],
        context: ExecutionContext | None = None,
    ) -> AsyncIterator[ExecutionResult]:
        """
        Stream execution results.

        Yields partial results as they become available.

        Args:
            capability_id: The capability to execute
            input_data: Input parameters for the capability
            context: Optional execution context

        Yields:
            ExecutionResult with progressive updates
        """
        ...
