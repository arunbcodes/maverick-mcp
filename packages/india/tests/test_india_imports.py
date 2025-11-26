"""Test that package imports work correctly."""


class TestPackageImports:
    """Test that all subpackages can be imported."""

    def test_import_maverick_india(self):
        """Test importing the main package."""
        import maverick_india

        assert maverick_india is not None

    def test_import_market(self):
        """Test importing market subpackage."""
        from maverick_india import market

        assert market is not None

    def test_import_news(self):
        """Test importing news subpackage."""
        from maverick_india import news

        assert news is not None

    def test_import_economic(self):
        """Test importing economic subpackage."""
        from maverick_india import economic

        assert economic is not None

    def test_import_concall(self):
        """Test importing concall subpackage."""
        from maverick_india import concall

        assert concall is not None
