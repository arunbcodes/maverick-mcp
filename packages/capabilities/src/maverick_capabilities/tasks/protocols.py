"""
Task queue protocols.

Defines the abstract interface for async task execution.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Protocol, runtime_checkable
from uuid import UUID, uuid4


class TaskPriority(str, Enum):
    """Task priority levels."""

    CRITICAL = "critical"  # Execute immediately
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"  # Created, not yet queued
    QUEUED = "queued"  # In queue, waiting for worker
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Finished successfully
    FAILED = "failed"  # Finished with error
    CANCELLED = "cancelled"  # Manually cancelled
    RETRY = "retry"  # Failed, will retry


@dataclass
class TaskConfig:
    """Configuration for task execution."""

    # Queue settings
    queue: str = "default"
    priority: TaskPriority = TaskPriority.NORMAL

    # Execution settings
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_delay_seconds: float = 60.0

    # Callbacks
    webhook_url: str | None = None
    callback_capability: str | None = None  # Capability to invoke on completion

    # Scheduling
    eta: datetime | None = None  # Execute at specific time
    countdown_seconds: int | None = None  # Execute after N seconds


@dataclass
class TaskResult:
    """Result of an async task."""

    task_id: UUID
    capability_id: str
    status: TaskStatus

    # Result data
    result: Any | None = None
    error: str | None = None
    error_type: str | None = None

    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Progress
    progress_percent: int = 0
    progress_message: str | None = None

    # Retry info
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: datetime | None = None

    @property
    def duration_ms(self) -> int | None:
        """Get execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None

    @property
    def is_complete(self) -> bool:
        """Check if task is complete."""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        )

    @property
    def is_success(self) -> bool:
        """Check if task succeeded."""
        return self.status == TaskStatus.COMPLETED

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": str(self.task_id),
            "capability_id": self.capability_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "error_type": self.error_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "duration_ms": self.duration_ms,
            "progress_percent": self.progress_percent,
            "progress_message": self.progress_message,
            "retry_count": self.retry_count,
        }


@runtime_checkable
class TaskQueue(Protocol):
    """
    Protocol for async task queue.

    Implementations can include:
    - MemoryTaskQueue: In-memory with asyncio (default)
    - RedisTaskQueue: Redis-backed with persistence
    - CeleryTaskQueue: Full Celery integration (future)
    """

    @abstractmethod
    async def enqueue(
        self,
        capability_id: str,
        input_data: dict[str, Any],
        config: TaskConfig | None = None,
    ) -> TaskResult:
        """
        Enqueue a task for async execution.

        Args:
            capability_id: The capability to execute
            input_data: Input parameters for the capability
            config: Optional task configuration

        Returns:
            TaskResult with status=QUEUED and task_id
        """
        ...

    @abstractmethod
    async def get_status(self, task_id: UUID) -> TaskResult:
        """
        Get task status.

        Args:
            task_id: The task to check

        Returns:
            TaskResult with current status
        """
        ...

    @abstractmethod
    async def cancel(self, task_id: UUID) -> bool:
        """
        Cancel a pending or running task.

        Args:
            task_id: The task to cancel

        Returns:
            True if cancelled, False if not found or already complete
        """
        ...

    @abstractmethod
    async def update_progress(
        self,
        task_id: UUID,
        percent: int,
        message: str | None = None,
    ) -> None:
        """
        Update task progress.

        Args:
            task_id: The task to update
            percent: Progress percentage (0-100)
            message: Optional progress message
        """
        ...

    @abstractmethod
    async def list_tasks(
        self,
        capability_id: str | None = None,
        status: TaskStatus | None = None,
        limit: int = 100,
    ) -> list[TaskResult]:
        """
        List tasks.

        Args:
            capability_id: Filter by capability
            status: Filter by status
            limit: Maximum results

        Returns:
            List of TaskResult
        """
        ...

    @abstractmethod
    async def cleanup(self, max_age_seconds: int = 3600) -> int:
        """
        Cleanup old completed tasks.

        Args:
            max_age_seconds: Remove tasks older than this

        Returns:
            Number of tasks removed
        """
        ...
