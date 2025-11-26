"""Test that package imports work correctly."""


class TestPackageImports:
    """Test that all subpackages can be imported."""

    def test_import_maverick_backtest(self):
        """Test importing the main package."""
        import maverick_backtest

        assert maverick_backtest is not None

    def test_import_strategies(self):
        """Test importing strategies subpackage."""
        from maverick_backtest import strategies

        assert strategies is not None

    def test_import_engine(self):
        """Test importing engine subpackage."""
        from maverick_backtest import engine

        assert engine is not None

    def test_import_analysis(self):
        """Test importing analysis subpackage."""
        from maverick_backtest import analysis

        assert analysis is not None
