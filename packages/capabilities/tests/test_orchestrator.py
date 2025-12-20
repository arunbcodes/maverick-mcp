"""Tests for orchestrator."""

import asyncio
import pytest

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
    ExecutionStatus,
    get_orchestrator,
    reset_orchestrator,
)


class MockService:
    """Mock service for testing."""

    async def echo(self, message: str) -> dict:
        return {"message": message}

    async def slow_method(self, delay: float = 0.5) -> dict:
        await asyncio.sleep(delay)
        return {"completed": True}

    async def failing_method(self) -> dict:
        raise ValueError("Test error")

    def sync_method(self, value: int) -> dict:
        return {"value": value * 2}


@pytest.fixture
def setup_registry():
    """Set up registry with test capabilities."""
    reset_registry()
    reset_orchestrator()

    registry = get_registry()

    # Register test capabilities
    registry.register(
        Capability(
            id="echo",
            title="Echo",
            description="Echo a message",
            group=CapabilityGroup.DATA,
            service_class=MockService,
            method_name="echo",
            execution=ExecutionConfig(timeout_seconds=5),
            mcp=MCPConfig(expose=True, tool_name="echo"),
        )
    )

    registry.register(
        Capability(
            id="slow",
            title="Slow",
            description="Slow method",
            group=CapabilityGroup.DATA,
            service_class=MockService,
            method_name="slow_method",
            execution=ExecutionConfig(timeout_seconds=1),
            mcp=MCPConfig(expose=True, tool_name="slow"),
        )
    )

    registry.register(
        Capability(
            id="failing",
            title="Failing",
            description="Always fails",
            group=CapabilityGroup.DATA,
            service_class=MockService,
            method_name="failing_method",
            execution=ExecutionConfig(timeout_seconds=5),
            mcp=MCPConfig(expose=True, tool_name="failing"),
        )
    )

    registry.register(
        Capability(
            id="sync",
            title="Sync",
            description="Sync method",
            group=CapabilityGroup.DATA,
            service_class=MockService,
            method_name="sync_method",
            execution=ExecutionConfig(timeout_seconds=5),
            mcp=MCPConfig(expose=True, tool_name="sync"),
        )
    )

    yield registry

    reset_registry()
    reset_orchestrator()


@pytest.fixture
def orchestrator(setup_registry):
    """Create orchestrator with mock service."""
    orch = ServiceOrchestrator()
    orch.register_service("MockService", MockService())
    return orch


class TestServiceOrchestrator:
    """Tests for ServiceOrchestrator."""

    @pytest.mark.asyncio
    async def test_execute_async_method(self, orchestrator):
        """Test executing an async method."""
        result = await orchestrator.execute("echo", {"message": "hello"})

        assert result.is_success
        assert result.status == ExecutionStatus.COMPLETED
        assert result.result == {"message": "hello"}
        assert result.duration_ms is not None

    @pytest.mark.asyncio
    async def test_execute_sync_method(self, orchestrator):
        """Test executing a sync method."""
        result = await orchestrator.execute("sync", {"value": 21})

        assert result.is_success
        assert result.result == {"value": 42}

    @pytest.mark.asyncio
    async def test_execute_unknown_capability(self, orchestrator):
        """Test executing unknown capability."""
        result = await orchestrator.execute("unknown", {})

        assert not result.is_success
        assert result.status == ExecutionStatus.FAILED
        assert "Unknown capability" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_error(self, orchestrator):
        """Test handling execution errors."""
        result = await orchestrator.execute("failing", {})

        assert not result.is_success
        assert result.status == ExecutionStatus.FAILED
        assert "Test error" in result.error
        assert result.error_type == "ValueError"

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self, orchestrator):
        """Test timeout handling."""
        result = await orchestrator.execute("slow", {"delay": 2.0})

        assert not result.is_success
        assert result.status == ExecutionStatus.TIMEOUT
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_with_context(self, orchestrator):
        """Test execution with context."""
        context = ExecutionContext(
            capability_id="echo",
            user_id="test_user",
            correlation_id="test-123",
        )

        result = await orchestrator.execute("echo", {"message": "test"}, context)

        assert result.is_success
        assert result.execution_id == context.execution_id

    @pytest.mark.asyncio
    async def test_execute_async_returns_immediately(self, orchestrator):
        """Test that execute_async returns immediately."""
        result = await orchestrator.execute_async("slow", {"delay": 0.5})

        assert result.status in (ExecutionStatus.QUEUED, ExecutionStatus.RUNNING)
        assert result.execution_id is not None

    @pytest.mark.asyncio
    async def test_execute_async_completes(self, orchestrator):
        """Test that async execution completes."""
        result = await orchestrator.execute_async("echo", {"message": "async"})

        # Wait for completion
        await asyncio.sleep(0.1)

        final_result = await orchestrator.get_status(result.execution_id)
        assert final_result.is_complete
        assert final_result.result == {"message": "async"}

    @pytest.mark.asyncio
    async def test_cancel_async_execution(self, orchestrator):
        """Test cancelling async execution."""
        result = await orchestrator.execute_async("slow", {"delay": 10.0})

        # Cancel immediately
        cancelled = await orchestrator.cancel(result.execution_id)
        assert cancelled

        final_result = await orchestrator.get_status(result.execution_id)
        assert final_result.status == ExecutionStatus.CANCELLED


class TestGlobalOrchestrator:
    """Tests for global orchestrator functions."""

    def test_get_orchestrator_creates_default(self, setup_registry):
        """Test that get_orchestrator creates default."""
        reset_orchestrator()

        orch = get_orchestrator()
        assert orch is not None
        assert isinstance(orch, ServiceOrchestrator)

    def test_get_orchestrator_returns_same(self, setup_registry):
        """Test that get_orchestrator returns same instance."""
        reset_orchestrator()

        orch1 = get_orchestrator()
        orch2 = get_orchestrator()

        assert orch1 is orch2
