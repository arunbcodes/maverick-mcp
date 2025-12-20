"""Tests for capabilities integration module.

Tests for execute_capability() and with_orchestrator() decorators.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from maverick_capabilities.models import (
    Capability,
    CapabilityGroup,
    ExecutionConfig,
    MCPConfig,
)
from maverick_capabilities.registry import get_registry, reset_registry
from maverick_capabilities.orchestration import (
    ServiceOrchestrator,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
    reset_orchestrator,
    set_orchestrator,
)
from maverick_capabilities.audit import (
    MemoryAuditLogger,
    AuditEventType,
    reset_audit_logger,
    set_audit_logger,
)

from maverick_server.capabilities_integration import (
    execute_capability,
    with_orchestrator,
    with_audit,
    initialize_capabilities,
    shutdown_capabilities,
)


class MockService:
    """Mock service for testing."""

    async def get_stocks(self, limit: int = 10) -> dict:
        return {"stocks": [{"ticker": "AAPL"}] * limit}

    async def failing_method(self) -> dict:
        raise ValueError("Service error")


@pytest.fixture
def clean_state():
    """Ensure clean global state before and after tests."""
    reset_registry()
    reset_orchestrator()
    reset_audit_logger()
    yield
    reset_registry()
    reset_orchestrator()
    reset_audit_logger()


@pytest.fixture
def mock_orchestrator(clean_state):
    """Create and register mock orchestrator."""
    registry = get_registry()

    # Register test capability
    registry.register(
        Capability(
            id="get_maverick_stocks",
            title="Get Maverick Stocks",
            description="Get top Maverick stocks",
            group=CapabilityGroup.SCREENING,
            service_class=MockService,
            method_name="get_stocks",
            execution=ExecutionConfig(timeout_seconds=30),
            mcp=MCPConfig(expose=True, tool_name="screening_get_maverick_stocks"),
        )
    )

    registry.register(
        Capability(
            id="failing_capability",
            title="Failing Capability",
            description="Always fails",
            group=CapabilityGroup.DATA,
            service_class=MockService,
            method_name="failing_method",
            execution=ExecutionConfig(timeout_seconds=5),
            mcp=MCPConfig(expose=True, tool_name="failing"),
        )
    )

    # Create orchestrator with mock service
    orchestrator = ServiceOrchestrator(registry=registry)
    orchestrator.register_service("MockService", MockService())
    set_orchestrator(orchestrator)

    return orchestrator


@pytest.fixture
def mock_audit_logger(clean_state):
    """Create and register mock audit logger."""
    audit_logger = MemoryAuditLogger(max_events=1000)
    set_audit_logger(audit_logger)
    return audit_logger


class TestExecuteCapability:
    """Tests for execute_capability function."""

    @pytest.mark.asyncio
    async def test_execute_capability_success(self, mock_orchestrator):
        """Test successful capability execution returns expected format."""
        result = await execute_capability("get_maverick_stocks", {"limit": 5})

        assert result["success"] is True
        assert "data" in result
        assert result["data"]["stocks"] is not None
        assert len(result["data"]["stocks"]) == 5
        assert "execution_id" in result
        assert "duration_ms" in result

    @pytest.mark.asyncio
    async def test_execute_capability_with_user_id(self, mock_orchestrator):
        """Test capability execution includes user context."""
        result = await execute_capability(
            "get_maverick_stocks",
            {"limit": 10},
            user_id="test_user_123",
        )

        assert result["success"] is True
        assert "execution_id" in result

    @pytest.mark.asyncio
    async def test_execute_capability_with_empty_input(self, mock_orchestrator):
        """Test capability execution with no input uses defaults."""
        result = await execute_capability("get_maverick_stocks")

        assert result["success"] is True
        assert len(result["data"]["stocks"]) == 10  # Default limit

    @pytest.mark.asyncio
    async def test_execute_capability_unknown_returns_error(self, mock_orchestrator):
        """Test unknown capability returns error response."""
        result = await execute_capability("unknown_capability", {})

        assert result["success"] is False
        assert "error" in result
        assert "execution_id" in result

    @pytest.mark.asyncio
    async def test_execute_capability_failure_returns_error_type(self, mock_orchestrator):
        """Test failed execution includes error type."""
        result = await execute_capability("failing_capability", {})

        assert result["success"] is False
        assert result["error_type"] == "ValueError"
        assert "Service error" in result["error"]


class TestWithOrchestrator:
    """Tests for with_orchestrator decorator."""

    @pytest.mark.asyncio
    async def test_with_orchestrator_routes_through_orchestrator(self, mock_orchestrator):
        """Test decorator routes execution through orchestrator."""

        @with_orchestrator("get_maverick_stocks")
        async def decorated_tool(limit: int = 20):
            # Body should not execute
            raise RuntimeError("Should not reach here")

        result = await decorated_tool(limit=5)

        assert result["stocks"] is not None
        assert len(result["stocks"]) == 5

    @pytest.mark.asyncio
    async def test_with_orchestrator_preserves_function_name(self, mock_orchestrator):
        """Test decorator preserves original function metadata."""

        @with_orchestrator("get_maverick_stocks")
        async def my_custom_tool(limit: int = 20):
            pass

        assert my_custom_tool.__name__ == "my_custom_tool"

    @pytest.mark.asyncio
    async def test_with_orchestrator_handles_errors(self, mock_orchestrator):
        """Test decorator returns error dict on failure."""

        @with_orchestrator("failing_capability")
        async def failing_tool():
            pass

        result = await failing_tool()

        assert "error" in result
        assert "error_type" in result

    @pytest.mark.asyncio
    async def test_with_orchestrator_unknown_capability(self, mock_orchestrator):
        """Test decorator handles unknown capability."""

        @with_orchestrator("nonexistent_capability")
        async def unknown_tool():
            pass

        result = await unknown_tool()

        assert "error" in result


class TestWithAudit:
    """Tests for with_audit decorator."""

    @pytest.mark.asyncio
    async def test_with_audit_logs_execution_start(self, mock_audit_logger):
        """Test decorator logs execution started event."""

        @with_audit("test_capability")
        async def audited_tool(value: int) -> dict:
            return {"result": value * 2}

        await audited_tool(value=21)

        events = await mock_audit_logger.query(capability_id="test_capability")
        event_types = [e.event_type for e in events]

        assert AuditEventType.EXECUTION_STARTED in event_types

    @pytest.mark.asyncio
    async def test_with_audit_logs_execution_completed(self, mock_audit_logger):
        """Test decorator logs completion event with duration."""

        @with_audit("test_capability")
        async def audited_tool() -> dict:
            return {"success": True}

        await audited_tool()

        events = await mock_audit_logger.query(capability_id="test_capability")
        completed_events = [
            e for e in events if e.event_type == AuditEventType.EXECUTION_COMPLETED
        ]

        assert len(completed_events) == 1
        assert completed_events[0].duration_ms is not None
        assert completed_events[0].duration_ms >= 0

    @pytest.mark.asyncio
    async def test_with_audit_logs_execution_failed(self, mock_audit_logger):
        """Test decorator logs failure event with error details."""

        @with_audit("failing_tool")
        async def audited_failing_tool() -> dict:
            raise ValueError("Test failure")

        with pytest.raises(ValueError, match="Test failure"):
            await audited_failing_tool()

        events = await mock_audit_logger.query(capability_id="failing_tool")
        failed_events = [
            e for e in events if e.event_type == AuditEventType.EXECUTION_FAILED
        ]

        assert len(failed_events) == 1
        assert failed_events[0].error == "Test failure"
        assert failed_events[0].error_type == "ValueError"

    @pytest.mark.asyncio
    async def test_with_audit_respects_log_input_flag(self, mock_audit_logger):
        """Test log_input=False excludes input from audit."""

        @with_audit("sensitive_tool", log_input=False)
        async def sensitive_tool(password: str) -> dict:
            return {"authenticated": True}

        await sensitive_tool(password="secret123")

        events = await mock_audit_logger.query(capability_id="sensitive_tool")
        started_event = next(
            e for e in events if e.event_type == AuditEventType.EXECUTION_STARTED
        )

        assert started_event.input_data is None

    @pytest.mark.asyncio
    async def test_with_audit_respects_log_output_flag(self, mock_audit_logger):
        """Test log_output=False excludes output from audit."""

        @with_audit("sensitive_output", log_output=False)
        async def sensitive_output() -> dict:
            return {"secret": "data"}

        await sensitive_output()

        events = await mock_audit_logger.query(capability_id="sensitive_output")
        completed_event = next(
            e for e in events if e.event_type == AuditEventType.EXECUTION_COMPLETED
        )

        assert completed_event.output_data is None

    @pytest.mark.asyncio
    async def test_with_audit_uses_function_name_as_default_id(self, mock_audit_logger):
        """Test decorator uses function name when no capability_id provided."""

        @with_audit()
        async def auto_named_tool() -> dict:
            return {}

        await auto_named_tool()

        events = await mock_audit_logger.query(capability_id="auto_named_tool")
        assert len(events) >= 1

    @pytest.mark.asyncio
    async def test_with_audit_same_execution_id_for_start_and_complete(
        self, mock_audit_logger
    ):
        """Test start and complete events share same execution ID."""

        @with_audit("linked_events")
        async def linked_tool() -> dict:
            return {"done": True}

        await linked_tool()

        events = await mock_audit_logger.query(capability_id="linked_events")
        execution_ids = {e.execution_id for e in events}

        # All events for this execution should have the same execution_id
        assert len(execution_ids) == 1


class TestInitializeShutdown:
    """Tests for initialize_capabilities and shutdown_capabilities."""

    def test_initialize_capabilities_registers_capabilities(self, clean_state):
        """Test initialization registers capability definitions."""
        initialize_capabilities()

        registry = get_registry()
        capabilities = registry.list_all()

        assert len(capabilities) > 0

    def test_initialize_capabilities_creates_orchestrator(self, clean_state):
        """Test initialization creates orchestrator."""
        reset_orchestrator()
        initialize_capabilities()

        from maverick_capabilities import get_orchestrator

        orchestrator = get_orchestrator()
        assert orchestrator is not None

    def test_initialize_capabilities_creates_audit_logger(self, clean_state):
        """Test initialization creates audit logger."""
        initialize_capabilities(enable_audit=True)

        from maverick_capabilities import get_audit_logger

        audit_logger = get_audit_logger()
        assert audit_logger is not None

    def test_initialize_capabilities_idempotent(self, clean_state):
        """Test calling initialize twice does not raise error."""
        initialize_capabilities()
        initialize_capabilities()  # Should not raise

    def test_shutdown_capabilities_resets_state(self, clean_state):
        """Test shutdown resets global state."""
        initialize_capabilities()
        shutdown_capabilities()

        # After shutdown, registry should be empty
        registry = get_registry()
        assert len(registry.list_all()) == 0
