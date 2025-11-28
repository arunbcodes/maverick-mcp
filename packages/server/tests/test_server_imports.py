"""Test that package imports work correctly."""

import pytest


class TestPackageImports:
    """Test that all subpackages can be imported."""

    def test_import_maverick_server(self):
        """Test importing the main package."""
        import maverick_server

        assert maverick_server is not None
        assert hasattr(maverick_server, "__version__")
        assert maverick_server.__version__ == "0.1.0"

    def test_import_routers(self):
        """Test importing routers subpackage."""
        from maverick_server import routers

        assert routers is not None

    def test_import_tools(self):
        """Test importing tools subpackage."""
        from maverick_server import tools

        assert tools is not None


class TestCoreExports:
    """Test core server exports."""

    def test_export_maverick_server(self):
        """Test MaverickServer class export."""
        from maverick_server import MaverickServer

        assert MaverickServer is not None

    def test_export_fast_mcp_protocol(self):
        """Test FastMCPProtocol export."""
        from maverick_server import FastMCPProtocol

        assert FastMCPProtocol is not None

    def test_export_create_server(self):
        """Test create_server function export."""
        from maverick_server import create_server

        assert create_server is not None
        assert callable(create_server)

    def test_export_configure_warnings(self):
        """Test configure_warnings function export."""
        from maverick_server import configure_warnings

        assert configure_warnings is not None
        assert callable(configure_warnings)


class TestToolRegistryExports:
    """Test tool registry exports."""

    def test_export_tool_registry(self):
        """Test ToolRegistry class export."""
        from maverick_server import ToolRegistry

        assert ToolRegistry is not None

    def test_export_tool_registrar(self):
        """Test ToolRegistrar protocol export."""
        from maverick_server import ToolRegistrar

        assert ToolRegistrar is not None

    def test_export_create_tool_wrapper(self):
        """Test create_tool_wrapper function export."""
        from maverick_server import create_tool_wrapper

        assert create_tool_wrapper is not None
        assert callable(create_tool_wrapper)

    def test_export_register_tool_group(self):
        """Test register_tool_group function export."""
        from maverick_server import register_tool_group

        assert register_tool_group is not None
        assert callable(register_tool_group)

    def test_export_get_default_registry(self):
        """Test get_default_registry function export."""
        from maverick_server import get_default_registry

        assert get_default_registry is not None
        assert callable(get_default_registry)

    def test_export_reset_default_registry(self):
        """Test reset_default_registry function export."""
        from maverick_server import reset_default_registry

        assert reset_default_registry is not None
        assert callable(reset_default_registry)


class TestMaverickServerClass:
    """Test MaverickServer class functionality."""

    def test_server_initialization(self):
        """Test server can be initialized."""
        from maverick_server import MaverickServer

        server = MaverickServer(name="TestServer", configure_warnings_filter=False)
        assert server is not None
        assert server.name == "TestServer"

    def test_server_mcp_property(self):
        """Test server mcp property returns FastMCP instance."""
        from maverick_server import MaverickServer

        server = MaverickServer(name="TestServer", configure_warnings_filter=False)
        mcp = server.mcp
        assert mcp is not None

    def test_create_server_function(self):
        """Test create_server convenience function."""
        from maverick_server import create_server

        server = create_server(name="TestServer", configure_warnings_filter=False)
        assert server is not None
        assert server.name == "TestServer"


class TestToolRegistry:
    """Test ToolRegistry functionality."""

    def test_registry_initialization(self):
        """Test registry can be initialized."""
        from maverick_server import ToolRegistry

        registry = ToolRegistry()
        assert registry is not None
        assert len(registry.registered_groups) == 0

    def test_registry_add_registrar(self):
        """Test adding a registrar to registry."""
        from maverick_server import ToolRegistry

        registry = ToolRegistry()

        def dummy_registrar(mcp):
            pass

        registry.add_registrar("dummy", dummy_registrar)
        # Registrar is added but not yet registered
        assert "dummy" not in registry.registered_groups

    def test_default_registry(self):
        """Test get_default_registry returns singleton."""
        from maverick_server import get_default_registry, reset_default_registry

        # Reset to start fresh
        reset_default_registry()

        registry1 = get_default_registry()
        registry2 = get_default_registry()
        assert registry1 is registry2

        # Clean up
        reset_default_registry()

    def test_reset_default_registry(self):
        """Test reset_default_registry clears singleton."""
        from maverick_server import get_default_registry, reset_default_registry

        registry1 = get_default_registry()
        reset_default_registry()
        registry2 = get_default_registry()
        assert registry1 is not registry2


class TestToolWrapperUtilities:
    """Test tool wrapper utilities."""

    def test_create_tool_wrapper(self):
        """Test create_tool_wrapper function."""
        from maverick_server import create_tool_wrapper

        def sample_func():
            return "test"

        name, func, desc = create_tool_wrapper(
            "test_tool", sample_func, "A test tool"
        )
        assert name == "test_tool"
        assert func is sample_func
        assert desc == "A test tool"

    def test_create_tool_wrapper_no_description(self):
        """Test create_tool_wrapper without description."""
        from maverick_server import create_tool_wrapper

        def sample_func():
            return "test"

        name, func, desc = create_tool_wrapper("test_tool", sample_func, None)
        assert name == "test_tool"
        assert func is sample_func
        assert desc is None


class TestConfigureWarnings:
    """Test warning configuration."""

    def test_configure_warnings_runs(self):
        """Test configure_warnings executes without error."""
        from maverick_server import configure_warnings

        # Should not raise
        configure_warnings()


class TestAllExportsAvailable:
    """Test that all documented exports are available."""

    def test_all_exports_in_all_list(self):
        """Test __all__ contains expected exports."""
        import maverick_server

        expected_exports = [
            "MaverickServer",
            "FastMCPProtocol",
            "create_server",
            "configure_warnings",
            "ToolRegistry",
            "ToolRegistrar",
            "create_tool_wrapper",
            "register_tool_group",
            "get_default_registry",
            "reset_default_registry",
            "__version__",
        ]

        for export in expected_exports:
            assert export in maverick_server.__all__, f"{export} not in __all__"
            assert hasattr(maverick_server, export), f"{export} not accessible"
