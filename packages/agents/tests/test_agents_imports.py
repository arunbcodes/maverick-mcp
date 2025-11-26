"""Test that package imports work correctly."""


class TestPackageImports:
    """Test that all subpackages can be imported."""

    def test_import_maverick_agents(self):
        """Test importing the main package."""
        import maverick_agents

        assert maverick_agents is not None

    def test_import_research(self):
        """Test importing research subpackage."""
        from maverick_agents import research

        assert research is not None

    def test_import_market(self):
        """Test importing market subpackage."""
        from maverick_agents import market

        assert market is not None

    def test_import_supervisor(self):
        """Test importing supervisor subpackage."""
        from maverick_agents import supervisor

        assert supervisor is not None
