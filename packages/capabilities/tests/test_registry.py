"""Tests for capability registry."""

import pytest

from maverick_capabilities.models import (
    Capability,
    CapabilityGroup,
    ExecutionConfig,
    MCPConfig,
    APIConfig,
)
from maverick_capabilities.registry import (
    CapabilityRegistry,
    get_registry,
    reset_registry,
)


class MockService:
    """Mock service for testing."""

    async def test_method(self, param1: str) -> dict:
        return {"result": param1}


@pytest.fixture
def registry():
    """Create a fresh registry for each test."""
    reset_registry()
    return CapabilityRegistry()


@pytest.fixture
def sample_capability():
    """Create a sample capability for testing."""
    return Capability(
        id="test_capability",
        title="Test Capability",
        description="A test capability",
        group=CapabilityGroup.SCREENING,
        service_class=MockService,
        method_name="test_method",
        mcp=MCPConfig(
            expose=True,
            tool_name="test_tool",
            category="test",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/test",
            method="POST",
        ),
    )


class TestCapabilityRegistry:
    """Tests for CapabilityRegistry."""

    def test_register_capability(self, registry, sample_capability):
        """Test registering a capability."""
        registry.register(sample_capability)

        assert registry.get("test_capability") is not None
        assert registry.get("test_capability").title == "Test Capability"

    def test_register_duplicate_raises(self, registry, sample_capability):
        """Test that registering duplicate ID raises."""
        registry.register(sample_capability)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(sample_capability)

    def test_get_nonexistent_returns_none(self, registry):
        """Test that getting nonexistent capability returns None."""
        assert registry.get("nonexistent") is None

    def test_get_or_raise(self, registry, sample_capability):
        """Test get_or_raise behavior."""
        registry.register(sample_capability)

        cap = registry.get_or_raise("test_capability")
        assert cap.id == "test_capability"

        with pytest.raises(KeyError, match="Unknown capability"):
            registry.get_or_raise("nonexistent")

    def test_list_all(self, registry, sample_capability):
        """Test listing all capabilities."""
        registry.register(sample_capability)

        caps = registry.list_all()
        assert len(caps) == 1
        assert caps[0].id == "test_capability"

    def test_list_by_group(self, registry, sample_capability):
        """Test listing by group."""
        registry.register(sample_capability)

        screening_caps = registry.list_by_group(CapabilityGroup.SCREENING)
        assert len(screening_caps) == 1

        portfolio_caps = registry.list_by_group(CapabilityGroup.PORTFOLIO)
        assert len(portfolio_caps) == 0

    def test_list_mcp(self, registry, sample_capability):
        """Test listing MCP-exposed capabilities."""
        registry.register(sample_capability)

        mcp_caps = registry.list_mcp()
        assert len(mcp_caps) == 1
        assert mcp_caps[0].mcp.tool_name == "test_tool"

    def test_list_api(self, registry, sample_capability):
        """Test listing API-exposed capabilities."""
        registry.register(sample_capability)

        api_caps = registry.list_api()
        assert len(api_caps) == 1
        assert api_caps[0].api.path == "/api/v1/test"

    def test_search(self, registry, sample_capability):
        """Test searching capabilities."""
        registry.register(sample_capability)

        # Search by title
        results = registry.search("Test")
        assert len(results) == 1

        # Search by description
        results = registry.search("test capability")
        assert len(results) == 1

        # No results
        results = registry.search("nonexistent")
        assert len(results) == 0

    def test_export_json(self, registry, sample_capability):
        """Test JSON export."""
        registry.register(sample_capability)

        json_str = registry.export_json()
        assert "test_capability" in json_str
        assert "Test Capability" in json_str

    def test_stats(self, registry, sample_capability):
        """Test statistics."""
        registry.register(sample_capability)

        stats = registry.stats()
        assert stats["total"] == 1
        assert stats["mcp_exposed"] == 1
        assert stats["api_exposed"] == 1


class TestGlobalRegistry:
    """Tests for global registry functions."""

    def test_get_registry_singleton(self):
        """Test that get_registry returns singleton."""
        reset_registry()

        reg1 = get_registry()
        reg2 = get_registry()

        assert reg1 is reg2

    def test_reset_registry(self):
        """Test registry reset."""
        reset_registry()

        reg1 = get_registry()
        reset_registry()
        reg2 = get_registry()

        assert reg1 is not reg2
