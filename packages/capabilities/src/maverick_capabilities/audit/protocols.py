"""
Audit logging protocols.

Defines the abstract interface for audit logging.
"""

from __future__ import annotations

import copy
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Protocol, runtime_checkable
from uuid import UUID, uuid4


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Execution lifecycle
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    EXECUTION_TIMEOUT = "execution.timeout"
    EXECUTION_CANCELLED = "execution.cancelled"

    # Agent events
    AGENT_INVOKED = "agent.invoked"
    AGENT_RESPONSE = "agent.response"

    # Business events
    RECOMMENDATION_MADE = "recommendation.made"
    POSITION_ADDED = "position.added"
    POSITION_REMOVED = "position.removed"
    ALERT_TRIGGERED = "alert.triggered"

    # Data access
    DATA_ACCESSED = "data.accessed"
    DATA_EXPORTED = "data.exported"


@dataclass
class AuditEvent:
    """
    An auditable event.

    Contains all information needed to reconstruct what happened
    during a capability execution for compliance and debugging.
    """

    # Identity
    event_id: UUID = field(default_factory=uuid4)
    event_type: AuditEventType = AuditEventType.EXECUTION_STARTED
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Execution context
    execution_id: UUID | None = None
    capability_id: str | None = None
    user_id: str | None = None
    correlation_id: str | None = None

    # Event data
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    error: str | None = None
    error_type: str | None = None

    # Execution metrics
    duration_ms: int | None = None

    # Agent-specific
    agents_consulted: list[str] = field(default_factory=list)
    reasoning_trace: list[dict[str, Any]] = field(default_factory=list)

    # Recommendation-specific (for compliance)
    ticker: str | None = None
    recommendation: str | None = None
    confidence: float | None = None

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def redact_pii(self, pii_fields: list[str]) -> "AuditEvent":
        """
        Return a copy with PII fields redacted.

        Args:
            pii_fields: List of field names to redact

        Returns:
            New AuditEvent with sensitive fields redacted
        """
        event = copy.deepcopy(self)

        def redact_dict(d: dict | None, fields: list[str]) -> dict | None:
            if d is None:
                return None
            result = {}
            for key, value in d.items():
                if key in fields:
                    result[key] = "[REDACTED]"
                elif isinstance(value, dict):
                    result[key] = redact_dict(value, fields)
                else:
                    result[key] = value
            return result

        event.input_data = redact_dict(event.input_data, pii_fields)
        event.output_data = redact_dict(event.output_data, pii_fields)
        event.metadata = redact_dict(event.metadata, pii_fields) or {}

        return event

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "execution_id": str(self.execution_id) if self.execution_id else None,
            "capability_id": self.capability_id,
            "user_id": self.user_id,
            "correlation_id": self.correlation_id,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "error_type": self.error_type,
            "duration_ms": self.duration_ms,
            "agents_consulted": self.agents_consulted,
            "ticker": self.ticker,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditEvent":
        """Create from dictionary."""
        return cls(
            event_id=UUID(data["event_id"]) if data.get("event_id") else uuid4(),
            event_type=AuditEventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if data.get("timestamp")
            else datetime.now(UTC),
            execution_id=UUID(data["execution_id"])
            if data.get("execution_id")
            else None,
            capability_id=data.get("capability_id"),
            user_id=data.get("user_id"),
            correlation_id=data.get("correlation_id"),
            input_data=data.get("input_data"),
            output_data=data.get("output_data"),
            error=data.get("error"),
            error_type=data.get("error_type"),
            duration_ms=data.get("duration_ms"),
            agents_consulted=data.get("agents_consulted", []),
            reasoning_trace=data.get("reasoning_trace", []),
            ticker=data.get("ticker"),
            recommendation=data.get("recommendation"),
            confidence=data.get("confidence"),
            metadata=data.get("metadata", {}),
        )


@runtime_checkable
class AuditLogger(Protocol):
    """
    Protocol for audit logging.

    Implementations can include:
    - DatabaseAuditLogger: Store in PostgreSQL/SQLite
    - MemoryAuditLogger: In-memory (for testing)
    - FileAuditLogger: JSON lines file (future)
    - CloudAuditLogger: AWS CloudWatch, etc. (future)
    """

    @abstractmethod
    async def log(self, event: AuditEvent) -> None:
        """
        Log an audit event.

        Args:
            event: The event to log
        """
        ...

    @abstractmethod
    async def query(
        self,
        execution_id: UUID | None = None,
        capability_id: str | None = None,
        user_id: str | None = None,
        event_type: AuditEventType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        ticker: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        """
        Query audit events.

        Args:
            execution_id: Filter by execution ID
            capability_id: Filter by capability ID
            user_id: Filter by user ID
            event_type: Filter by event type
            start_time: Filter events after this time
            end_time: Filter events before this time
            ticker: Filter by ticker symbol
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of matching audit events
        """
        ...

    @abstractmethod
    async def get_execution_trace(
        self,
        execution_id: UUID,
    ) -> list[AuditEvent]:
        """
        Get all events for an execution, ordered by time.

        Args:
            execution_id: The execution to get events for

        Returns:
            List of audit events for the execution
        """
        ...

    @abstractmethod
    async def count(
        self,
        capability_id: str | None = None,
        event_type: AuditEventType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> int:
        """
        Count audit events matching criteria.

        Args:
            capability_id: Filter by capability ID
            event_type: Filter by event type
            start_time: Filter events after this time
            end_time: Filter events before this time

        Returns:
            Count of matching events
        """
        ...
