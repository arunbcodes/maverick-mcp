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


class TestMarketProviderExports:
    """Test market provider exports."""

    def test_export_indian_market_enum(self):
        """Test IndianMarket enum export."""
        from maverick_india import IndianMarket

        assert IndianMarket is not None
        assert IndianMarket.NSE.value == "NSE"
        assert IndianMarket.BSE.value == "BSE"

    def test_export_indian_market_data_provider(self):
        """Test IndianMarketDataProvider export."""
        from maverick_india import IndianMarketDataProvider

        assert IndianMarketDataProvider is not None

    def test_export_indian_market_config(self):
        """Test INDIAN_MARKET_CONFIG export."""
        from maverick_india import INDIAN_MARKET_CONFIG

        assert INDIAN_MARKET_CONFIG is not None
        assert len(INDIAN_MARKET_CONFIG) >= 2

    def test_export_circuit_breaker_limits(self):
        """Test calculate_circuit_breaker_limits export."""
        from maverick_india import calculate_circuit_breaker_limits

        assert calculate_circuit_breaker_limits is not None

    def test_export_format_indian_currency(self):
        """Test format_indian_currency export."""
        from maverick_india import format_indian_currency

        assert format_indian_currency is not None

    def test_export_get_nifty_sectors(self):
        """Test get_nifty_sectors export."""
        from maverick_india import get_nifty_sectors

        assert get_nifty_sectors is not None

    def test_export_fetch_nse_data(self):
        """Test fetch_nse_data export."""
        from maverick_india import fetch_nse_data

        assert fetch_nse_data is not None

    def test_export_fetch_bse_data(self):
        """Test fetch_bse_data export."""
        from maverick_india import fetch_bse_data

        assert fetch_bse_data is not None


class TestScreeningExports:
    """Test screening strategy exports."""

    def test_export_maverick_bullish_india(self):
        """Test get_maverick_bullish_india export."""
        from maverick_india import get_maverick_bullish_india

        assert get_maverick_bullish_india is not None

    def test_export_maverick_bearish_india(self):
        """Test get_maverick_bearish_india export."""
        from maverick_india import get_maverick_bearish_india

        assert get_maverick_bearish_india is not None

    def test_export_nifty50_momentum(self):
        """Test get_nifty50_momentum export."""
        from maverick_india import get_nifty50_momentum

        assert get_nifty50_momentum is not None

    def test_export_nifty_sector_rotation(self):
        """Test get_nifty_sector_rotation export."""
        from maverick_india import get_nifty_sector_rotation

        assert get_nifty_sector_rotation is not None

    def test_export_value_picks_india(self):
        """Test get_value_picks_india export."""
        from maverick_india import get_value_picks_india

        assert get_value_picks_india is not None

    def test_export_smallcap_breakouts_india(self):
        """Test get_smallcap_breakouts_india export."""
        from maverick_india import get_smallcap_breakouts_india

        assert get_smallcap_breakouts_india is not None


class TestUtilityFunctions:
    """Test utility function behavior."""

    def test_format_indian_currency_crores(self):
        """Test formatting amount in crores."""
        from maverick_india import format_indian_currency

        result = format_indian_currency(15000000)  # 1.5 crores
        assert "₹" in result
        assert "Cr" in result

    def test_format_indian_currency_lakhs(self):
        """Test formatting amount in lakhs."""
        from maverick_india import format_indian_currency

        result = format_indian_currency(500000)  # 5 lakhs
        assert "₹" in result
        assert "L" in result

    def test_circuit_breaker_calculation(self):
        """Test circuit breaker limit calculation."""
        from maverick_india import calculate_circuit_breaker_limits, IndianMarket

        limits = calculate_circuit_breaker_limits(100.0, IndianMarket.NSE)
        assert abs(limits["upper_limit"] - 110.0) < 0.01  # 10% up
        assert abs(limits["lower_limit"] - 90.0) < 0.01  # 10% down
        assert limits["circuit_breaker_pct"] == 10

    def test_get_nifty_sectors_list(self):
        """Test that nifty sectors returns a list."""
        from maverick_india import get_nifty_sectors

        sectors = get_nifty_sectors()
        assert isinstance(sectors, list)
        assert len(sectors) > 0
        assert "Banking & Financial Services" in sectors
