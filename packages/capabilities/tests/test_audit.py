"""Tests for audit logging."""

from datetime import datetime, UTC, timedelta
from uuid import uuid4

import pytest

from maverick_capabilities.audit import (
    AuditEvent,
    AuditEventType,
    MemoryAuditLogger,
    get_audit_logger,
    set_audit_logger,
    reset_audit_logger,
)


@pytest.fixture
def audit_logger():
    """Create a fresh audit logger for each test."""
    reset_audit_logger()
    logger = MemoryAuditLogger()
    set_audit_logger(logger)
    return logger


@pytest.fixture
def sample_event():
    """Create a sample audit event."""
    return AuditEvent(
        event_type=AuditEventType.EXECUTION_COMPLETED,
        execution_id=uuid4(),
        capability_id="test_capability",
        user_id="test_user",
        input_data={"param1": "value1"},
        output_data={"result": "success"},
        ticker="AAPL",
        duration_ms=100,
    )


class TestAuditEvent:
    """Tests for AuditEvent."""

    def test_event_creation(self, sample_event):
        """Test creating an audit event."""
        assert sample_event.event_id is not None
        assert sample_event.event_type == AuditEventType.EXECUTION_COMPLETED
        assert sample_event.capability_id == "test_capability"
        assert sample_event.ticker == "AAPL"

    def test_event_to_dict(self, sample_event):
        """Test serialization to dict."""
        data = sample_event.to_dict()

        assert data["event_type"] == "execution.completed"
        assert data["capability_id"] == "test_capability"
        assert data["ticker"] == "AAPL"
        assert data["duration_ms"] == 100

    def test_event_from_dict(self, sample_event):
        """Test deserialization from dict."""
        data = sample_event.to_dict()
        restored = AuditEvent.from_dict(data)

        assert restored.event_type == sample_event.event_type
        assert restored.capability_id == sample_event.capability_id
        assert restored.ticker == sample_event.ticker

    def test_redact_pii(self, sample_event):
        """Test PII redaction."""
        sample_event.input_data = {"password": "secret", "param1": "value1"}

        redacted = sample_event.redact_pii(["password"])

        assert redacted.input_data["password"] == "[REDACTED]"
        assert redacted.input_data["param1"] == "value1"
        # Original unchanged
        assert sample_event.input_data["password"] == "secret"


class TestMemoryAuditLogger:
    """Tests for MemoryAuditLogger."""

    @pytest.mark.asyncio
    async def test_log_event(self, audit_logger, sample_event):
        """Test logging an event."""
        await audit_logger.log(sample_event)

        assert len(audit_logger) == 1

    @pytest.mark.asyncio
    async def test_query_by_capability(self, audit_logger, sample_event):
        """Test querying by capability ID."""
        await audit_logger.log(sample_event)

        # Create another event with different capability
        other_event = AuditEvent(
            event_type=AuditEventType.EXECUTION_STARTED,
            capability_id="other_capability",
        )
        await audit_logger.log(other_event)

        results = await audit_logger.query(capability_id="test_capability")
        assert len(results) == 1
        assert results[0].capability_id == "test_capability"

    @pytest.mark.asyncio
    async def test_query_by_event_type(self, audit_logger, sample_event):
        """Test querying by event type."""
        await audit_logger.log(sample_event)

        started_event = AuditEvent(
            event_type=AuditEventType.EXECUTION_STARTED,
            capability_id="test_capability",
        )
        await audit_logger.log(started_event)

        results = await audit_logger.query(
            event_type=AuditEventType.EXECUTION_COMPLETED
        )
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_query_by_ticker(self, audit_logger, sample_event):
        """Test querying by ticker."""
        await audit_logger.log(sample_event)

        results = await audit_logger.query(ticker="AAPL")
        assert len(results) == 1

        results = await audit_logger.query(ticker="GOOG")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_query_by_time_range(self, audit_logger):
        """Test querying by time range."""
        now = datetime.now(UTC)

        # Old event
        old_event = AuditEvent(
            event_type=AuditEventType.EXECUTION_COMPLETED,
            capability_id="old",
        )
        old_event.timestamp = now - timedelta(hours=2)
        await audit_logger.log(old_event)

        # Recent event
        recent_event = AuditEvent(
            event_type=AuditEventType.EXECUTION_COMPLETED,
            capability_id="recent",
        )
        await audit_logger.log(recent_event)

        # Query last hour
        results = await audit_logger.query(start_time=now - timedelta(hours=1))
        assert len(results) == 1
        assert results[0].capability_id == "recent"

    @pytest.mark.asyncio
    async def test_get_execution_trace(self, audit_logger):
        """Test getting execution trace."""
        execution_id = uuid4()

        # Log multiple events for same execution
        events = [
            AuditEvent(
                event_type=AuditEventType.EXECUTION_STARTED,
                execution_id=execution_id,
                capability_id="test",
            ),
            AuditEvent(
                event_type=AuditEventType.AGENT_INVOKED,
                execution_id=execution_id,
                capability_id="test",
            ),
            AuditEvent(
                event_type=AuditEventType.EXECUTION_COMPLETED,
                execution_id=execution_id,
                capability_id="test",
            ),
        ]

        for event in events:
            await audit_logger.log(event)

        trace = await audit_logger.get_execution_trace(execution_id)
        assert len(trace) == 3
        assert trace[0].event_type == AuditEventType.EXECUTION_STARTED
        assert trace[2].event_type == AuditEventType.EXECUTION_COMPLETED

    @pytest.mark.asyncio
    async def test_count(self, audit_logger, sample_event):
        """Test counting events."""
        await audit_logger.log(sample_event)
        await audit_logger.log(sample_event)

        count = await audit_logger.count(capability_id="test_capability")
        assert count == 2

    @pytest.mark.asyncio
    async def test_max_events_limit(self):
        """Test max events limit enforcement."""
        logger = MemoryAuditLogger(max_events=5)

        for i in range(10):
            await logger.log(
                AuditEvent(
                    event_type=AuditEventType.EXECUTION_COMPLETED,
                    capability_id=f"cap_{i}",
                )
            )

        assert len(logger) == 5

    @pytest.mark.asyncio
    async def test_clear(self, audit_logger, sample_event):
        """Test clearing events."""
        await audit_logger.log(sample_event)
        assert len(audit_logger) == 1

        audit_logger.clear()
        assert len(audit_logger) == 0


class TestGlobalAuditLogger:
    """Tests for global audit logger functions."""

    def test_get_audit_logger_creates_default(self):
        """Test that get_audit_logger creates default."""
        reset_audit_logger()

        logger = get_audit_logger()
        assert logger is not None
        assert isinstance(logger, MemoryAuditLogger)

    def test_set_audit_logger(self):
        """Test setting custom logger."""
        reset_audit_logger()

        custom_logger = MemoryAuditLogger(max_events=100)
        set_audit_logger(custom_logger)

        assert get_audit_logger() is custom_logger
