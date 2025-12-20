"""
In-memory audit logger.

Simple implementation for testing and development.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from maverick_capabilities.audit.protocols import (
    AuditEvent,
    AuditEventType,
    AuditLogger,
)

if TYPE_CHECKING:
    pass


class MemoryAuditLogger(AuditLogger):
    """
    In-memory audit logger.

    Stores events in memory. Useful for:
    - Testing
    - Development
    - Short-lived processes

    Note: Events are lost when the process exits.
    """

    def __init__(self, max_events: int = 10000):
        """
        Initialize memory logger.

        Args:
            max_events: Maximum events to retain (FIFO eviction)
        """
        self._events: list[AuditEvent] = []
        self._max_events = max_events
        self._by_execution: dict[UUID, list[AuditEvent]] = {}

    async def log(self, event: AuditEvent) -> None:
        """Log an audit event."""
        self._events.append(event)

        # Index by execution ID
        if event.execution_id:
            if event.execution_id not in self._by_execution:
                self._by_execution[event.execution_id] = []
            self._by_execution[event.execution_id].append(event)

        # Evict old events if over limit
        while len(self._events) > self._max_events:
            old_event = self._events.pop(0)
            if old_event.execution_id and old_event.execution_id in self._by_execution:
                exec_events = self._by_execution[old_event.execution_id]
                if old_event in exec_events:
                    exec_events.remove(old_event)
                if not exec_events:
                    del self._by_execution[old_event.execution_id]

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
        """Query audit events."""
        results = []

        for event in reversed(self._events):  # Most recent first
            # Apply filters
            if execution_id and event.execution_id != execution_id:
                continue
            if capability_id and event.capability_id != capability_id:
                continue
            if user_id and event.user_id != user_id:
                continue
            if event_type and event.event_type != event_type:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            if ticker and event.ticker != ticker:
                continue

            results.append(event)

        # Apply pagination
        return results[offset : offset + limit]

    async def get_execution_trace(self, execution_id: UUID) -> list[AuditEvent]:
        """Get all events for an execution."""
        events = self._by_execution.get(execution_id, [])
        return sorted(events, key=lambda e: e.timestamp)

    async def count(
        self,
        capability_id: str | None = None,
        event_type: AuditEventType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> int:
        """Count matching events."""
        count = 0

        for event in self._events:
            if capability_id and event.capability_id != capability_id:
                continue
            if event_type and event.event_type != event_type:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            count += 1

        return count

    # Utility methods for testing

    def clear(self) -> None:
        """Clear all events."""
        self._events.clear()
        self._by_execution.clear()

    def get_all(self) -> list[AuditEvent]:
        """Get all events (for testing)."""
        return list(self._events)

    def __len__(self) -> int:
        """Get number of stored events."""
        return len(self._events)
