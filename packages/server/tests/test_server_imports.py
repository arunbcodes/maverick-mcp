"""Test that package imports work correctly."""


class TestPackageImports:
    """Test that all subpackages can be imported."""

    def test_import_maverick_server(self):
        """Test importing the main package."""
        import maverick_server

        assert maverick_server is not None
        assert hasattr(maverick_server, "__version__")

    def test_import_routers(self):
        """Test importing routers subpackage."""
        from maverick_server import routers

        assert routers is not None

    def test_import_tools(self):
        """Test importing tools subpackage."""
        from maverick_server import tools

        assert tools is not None
