"""
Database audit logger.

Persists audit events to PostgreSQL/SQLite for compliance and analytics.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, UTC
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    TypeDecorator,
    select,
    func,
)
from sqlalchemy.ext.asyncio import AsyncSession

from maverick_data.models.base import Base, TimestampMixin


class UUIDType(TypeDecorator):
    """
    Platform-independent UUID type.

    Uses PostgreSQL's UUID type when available, otherwise stores as CHAR(36).
    This allows the same model to work with both PostgreSQL and SQLite.
    """

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        # For SQLite, convert UUID to string
        return str(value) if isinstance(value, UUID) else value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        # For SQLite, convert string back to UUID
        return UUID(value) if isinstance(value, str) else value
from maverick_capabilities.audit.protocols import (
    AuditEvent,
    AuditEventType,
    AuditLogger,
)

if TYPE_CHECKING:
    from collections.abc import Callable, AsyncGenerator

logger = logging.getLogger(__name__)


class AuditLogModel(Base, TimestampMixin):
    """SQLAlchemy model for audit logs.

    Uses UUIDType which is compatible with both PostgreSQL (native UUID)
    and SQLite (CHAR(36) string storage).
    """

    __tablename__ = "audit_logs"

    id = Column(UUIDType(), primary_key=True)
    event_type = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Execution context
    execution_id = Column(UUIDType(), index=True)
    capability_id = Column(String(100), index=True)
    user_id = Column(String(100), index=True)
    correlation_id = Column(String(100), index=True)

    # Event data (stored as JSON)
    input_data = Column(Text)  # JSON
    output_data = Column(Text)  # JSON
    error = Column(Text)
    error_type = Column(String(100))

    # Metrics
    duration_ms = Column(Integer)

    # Agent info (stored as JSON)
    agents_consulted = Column(Text)  # JSON array
    reasoning_trace = Column(Text)  # JSON array

    # Business data
    ticker = Column(String(20), index=True)
    recommendation = Column(String(50))
    confidence = Column(Float)

    # Additional metadata (JSON)
    extra_metadata = Column(Text)

    __table_args__ = (
        Index("ix_audit_execution_time", "execution_id", "timestamp"),
        Index("ix_audit_capability_time", "capability_id", "timestamp"),
        Index("ix_audit_ticker_time", "ticker", "timestamp"),
    )


class DatabaseAuditLogger(AuditLogger):
    """
    Database-backed audit logger.

    Stores events in PostgreSQL or SQLite for persistence
    and queryability.

    Usage:
        >>> from maverick_data.session import get_async_session
        >>> logger = DatabaseAuditLogger(get_async_session)
        >>> await logger.log(event)
    """

    def __init__(
        self,
        session_factory: Callable[[], AsyncGenerator[AsyncSession, None]],
    ):
        """
        Initialize database logger.

        Args:
            session_factory: Async context manager that yields database sessions
        """
        self._session_factory = session_factory

    async def log(self, event: AuditEvent) -> None:
        """Log an audit event to the database."""
        async with self._session_factory() as session:
            model = AuditLogModel(
                id=event.event_id,
                event_type=event.event_type.value,
                timestamp=event.timestamp,
                execution_id=event.execution_id,
                capability_id=event.capability_id,
                user_id=event.user_id,
                correlation_id=event.correlation_id,
                input_data=json.dumps(event.input_data) if event.input_data else None,
                output_data=json.dumps(event.output_data)
                if event.output_data
                else None,
                error=event.error,
                error_type=event.error_type,
                duration_ms=event.duration_ms,
                agents_consulted=json.dumps(event.agents_consulted)
                if event.agents_consulted
                else None,
                reasoning_trace=json.dumps(event.reasoning_trace)
                if event.reasoning_trace
                else None,
                ticker=event.ticker,
                recommendation=event.recommendation,
                confidence=event.confidence,
                extra_metadata=json.dumps(event.metadata) if event.metadata else None,
            )
            session.add(model)
            await session.commit()

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
        """Query audit events from database."""
        async with self._session_factory() as session:
            query = select(AuditLogModel)

            # Apply filters
            if execution_id:
                query = query.where(AuditLogModel.execution_id == execution_id)
            if capability_id:
                query = query.where(AuditLogModel.capability_id == capability_id)
            if user_id:
                query = query.where(AuditLogModel.user_id == user_id)
            if event_type:
                query = query.where(AuditLogModel.event_type == event_type.value)
            if start_time:
                query = query.where(AuditLogModel.timestamp >= start_time)
            if end_time:
                query = query.where(AuditLogModel.timestamp <= end_time)
            if ticker:
                query = query.where(AuditLogModel.ticker == ticker)

            # Order and paginate
            query = (
                query.order_by(AuditLogModel.timestamp.desc())
                .offset(offset)
                .limit(limit)
            )

            result = await session.execute(query)
            models = result.scalars().all()

            return [self._model_to_event(m) for m in models]

    async def get_execution_trace(self, execution_id: UUID) -> list[AuditEvent]:
        """Get all events for an execution, ordered by time."""
        async with self._session_factory() as session:
            query = (
                select(AuditLogModel)
                .where(AuditLogModel.execution_id == execution_id)
                .order_by(AuditLogModel.timestamp.asc())
            )

            result = await session.execute(query)
            models = result.scalars().all()

            return [self._model_to_event(m) for m in models]

    async def count(
        self,
        capability_id: str | None = None,
        event_type: AuditEventType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> int:
        """Count matching events."""
        async with self._session_factory() as session:
            query = select(func.count(AuditLogModel.id))

            if capability_id:
                query = query.where(AuditLogModel.capability_id == capability_id)
            if event_type:
                query = query.where(AuditLogModel.event_type == event_type.value)
            if start_time:
                query = query.where(AuditLogModel.timestamp >= start_time)
            if end_time:
                query = query.where(AuditLogModel.timestamp <= end_time)

            result = await session.execute(query)
            return result.scalar() or 0

    def _model_to_event(self, model: AuditLogModel) -> AuditEvent:
        """Convert database model to audit event."""
        return AuditEvent(
            event_id=model.id,
            event_type=AuditEventType(model.event_type),
            timestamp=model.timestamp or datetime.now(UTC),
            execution_id=model.execution_id,
            capability_id=model.capability_id,
            user_id=model.user_id,
            correlation_id=model.correlation_id,
            input_data=json.loads(model.input_data) if model.input_data else None,
            output_data=json.loads(model.output_data) if model.output_data else None,
            error=model.error,
            error_type=model.error_type,
            duration_ms=model.duration_ms,
            agents_consulted=json.loads(model.agents_consulted)
            if model.agents_consulted
            else [],
            reasoning_trace=json.loads(model.reasoning_trace)
            if model.reasoning_trace
            else [],
            ticker=model.ticker,
            recommendation=model.recommendation,
            confidence=model.confidence,
            metadata=json.loads(model.extra_metadata) if model.extra_metadata else {},
        )

    # Additional utility methods

    async def cleanup_old_events(
        self,
        retention_days: int = 90,
    ) -> int:
        """
        Delete events older than retention period.

        Args:
            retention_days: Delete events older than this many days

        Returns:
            Number of events deleted
        """
        from datetime import timedelta

        cutoff = datetime.now(UTC) - timedelta(days=retention_days)

        async with self._session_factory() as session:
            # Count first
            count_query = select(func.count(AuditLogModel.id)).where(
                AuditLogModel.timestamp < cutoff
            )
            result = await session.execute(count_query)
            count = result.scalar() or 0

            # Delete
            from sqlalchemy import delete

            delete_query = delete(AuditLogModel).where(
                AuditLogModel.timestamp < cutoff
            )
            await session.execute(delete_query)
            await session.commit()

            return count

    async def get_stats(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get audit statistics.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Dictionary with statistics
        """
        async with self._session_factory() as session:
            # Base query conditions
            conditions = []
            if start_time:
                conditions.append(AuditLogModel.timestamp >= start_time)
            if end_time:
                conditions.append(AuditLogModel.timestamp <= end_time)

            # Total count
            total_query = select(func.count(AuditLogModel.id))
            if conditions:
                for cond in conditions:
                    total_query = total_query.where(cond)
            total_result = await session.execute(total_query)
            total = total_result.scalar() or 0

            # Count by event type
            type_query = select(
                AuditLogModel.event_type, func.count(AuditLogModel.id)
            ).group_by(AuditLogModel.event_type)
            if conditions:
                for cond in conditions:
                    type_query = type_query.where(cond)
            type_result = await session.execute(type_query)
            by_type = dict(type_result.all())

            # Count by capability
            cap_query = select(
                AuditLogModel.capability_id, func.count(AuditLogModel.id)
            ).group_by(AuditLogModel.capability_id)
            if conditions:
                for cond in conditions:
                    cap_query = cap_query.where(cond)
            cap_result = await session.execute(cap_query)
            by_capability = dict(cap_result.all())

            return {
                "total_events": total,
                "by_event_type": by_type,
                "by_capability": by_capability,
            }
