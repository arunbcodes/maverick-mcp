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


class TestEconomicExports:
    """Test economic module exports."""

    def test_export_rbi_data_provider(self):
        """Test RBIDataProvider export."""
        from maverick_india import RBIDataProvider

        assert RBIDataProvider is not None

    def test_export_economic_indicator(self):
        """Test EconomicIndicator export."""
        from maverick_india import EconomicIndicator

        assert EconomicIndicator is not None
        # Test enum values
        assert EconomicIndicator.REPO_RATE is not None
        assert EconomicIndicator.CRR is not None
        assert EconomicIndicator.SLR is not None

    def test_export_exchange_rate_provider(self):
        """Test ExchangeRateProvider export."""
        from maverick_india import ExchangeRateProvider

        assert ExchangeRateProvider is not None

    def test_export_exchange_rate_source(self):
        """Test ExchangeRateSource export."""
        from maverick_india import ExchangeRateSource

        assert ExchangeRateSource is not None
        # Test enum values
        assert ExchangeRateSource.EXCHANGE_RATE_API is not None
        assert ExchangeRateSource.YAHOO_FINANCE is not None
        assert ExchangeRateSource.FALLBACK_CACHE is not None
        assert ExchangeRateSource.APPROXIMATE is not None

    def test_export_get_exchange_rate(self):
        """Test get_exchange_rate export."""
        from maverick_india import get_exchange_rate

        assert get_exchange_rate is not None

    def test_export_convert_currency(self):
        """Test convert_currency export."""
        from maverick_india import convert_currency

        assert convert_currency is not None

    def test_export_get_indian_economic_data(self):
        """Test get_indian_economic_data export."""
        from maverick_india import get_indian_economic_data

        assert get_indian_economic_data is not None

    def test_rbi_data_provider_init(self):
        """Test RBIDataProvider can be instantiated."""
        from maverick_india import RBIDataProvider

        provider = RBIDataProvider()
        assert provider is not None
        assert hasattr(provider, "get_policy_rates")
        assert hasattr(provider, "get_inflation_data")
        assert hasattr(provider, "get_gdp_growth")
        assert hasattr(provider, "get_forex_reserves")

    def test_exchange_rate_provider_init(self):
        """Test ExchangeRateProvider can be instantiated."""
        from maverick_india import ExchangeRateProvider

        provider = ExchangeRateProvider()
        assert provider is not None
        assert hasattr(provider, "get_rate")
        assert hasattr(provider, "get_supported_currencies")
        assert hasattr(provider, "is_rate_stale")


class TestNewsExports:
    """Test news module exports."""

    def test_export_base_news_scraper(self):
        """Test BaseNewsScraper export."""
        from maverick_india import BaseNewsScraper

        assert BaseNewsScraper is not None

    def test_export_news_article_store(self):
        """Test NewsArticleStore export."""
        from maverick_india import NewsArticleStore

        assert NewsArticleStore is not None

    def test_export_indian_stock_symbol_mapper(self):
        """Test IndianStockSymbolMapper export."""
        from maverick_india import IndianStockSymbolMapper

        assert IndianStockSymbolMapper is not None

    def test_export_moneycontrol_scraper(self):
        """Test MoneyControlScraper export."""
        from maverick_india import MoneyControlScraper

        assert MoneyControlScraper is not None

    def test_export_economic_times_scraper(self):
        """Test EconomicTimesScraper export."""
        from maverick_india import EconomicTimesScraper

        assert EconomicTimesScraper is not None

    def test_export_multi_source_news_aggregator(self):
        """Test MultiSourceNewsAggregator export."""
        from maverick_india import MultiSourceNewsAggregator

        assert MultiSourceNewsAggregator is not None

    def test_export_indian_news_provider(self):
        """Test IndianNewsProvider export."""
        from maverick_india import IndianNewsProvider

        assert IndianNewsProvider is not None

    def test_export_fetch_moneycontrol_news(self):
        """Test fetch_moneycontrol_news export."""
        from maverick_india import fetch_moneycontrol_news

        assert fetch_moneycontrol_news is not None

    def test_export_fetch_economic_times_news(self):
        """Test fetch_economic_times_news export."""
        from maverick_india import fetch_economic_times_news

        assert fetch_economic_times_news is not None

    def test_export_get_aggregated_news(self):
        """Test get_aggregated_news export."""
        from maverick_india import get_aggregated_news

        assert get_aggregated_news is not None

    def test_export_get_stock_sentiment(self):
        """Test get_stock_sentiment export."""
        from maverick_india import get_stock_sentiment

        assert get_stock_sentiment is not None

    def test_export_get_indian_stock_news(self):
        """Test get_indian_stock_news export."""
        from maverick_india import get_indian_stock_news

        assert get_indian_stock_news is not None

    def test_export_analyze_stock_sentiment(self):
        """Test analyze_stock_sentiment export."""
        from maverick_india import analyze_stock_sentiment

        assert analyze_stock_sentiment is not None

    def test_symbol_mapper_get_company(self):
        """Test IndianStockSymbolMapper can get company names."""
        from maverick_india import IndianStockSymbolMapper

        name = IndianStockSymbolMapper.get_company_name("RELIANCE")
        assert name == "Reliance Industries"

        name = IndianStockSymbolMapper.get_company_name("TCS")
        assert name == "Tata Consultancy Services"

    def test_moneycontrol_scraper_init(self):
        """Test MoneyControlScraper can be instantiated."""
        from maverick_india import MoneyControlScraper

        scraper = MoneyControlScraper()
        assert scraper is not None
        assert scraper.get_source_name() == "moneycontrol"

    def test_economic_times_scraper_init(self):
        """Test EconomicTimesScraper can be instantiated."""
        from maverick_india import EconomicTimesScraper

        scraper = EconomicTimesScraper()
        assert scraper is not None
        assert scraper.get_source_name() == "economictimes"

    def test_multi_source_aggregator_init(self):
        """Test MultiSourceNewsAggregator can be instantiated."""
        from maverick_india import MultiSourceNewsAggregator

        aggregator = MultiSourceNewsAggregator()
        assert aggregator is not None
        assert hasattr(aggregator, "fetch_latest_news")
        assert hasattr(aggregator, "fetch_stock_news")
        assert hasattr(aggregator, "get_sentiment_summary")

    def test_indian_news_provider_init(self):
        """Test IndianNewsProvider can be instantiated."""
        from maverick_india import IndianNewsProvider

        provider = IndianNewsProvider()
        assert provider is not None
        assert hasattr(provider, "get_stock_news")
        assert hasattr(provider, "analyze_sentiment")


class TestConcallExports:
    """Test concall module exports."""

    def test_export_concall_provider(self):
        """Test ConcallProvider export."""
        from maverick_india import ConcallProvider

        assert ConcallProvider is not None

    def test_concall_provider_is_abstract(self):
        """Test ConcallProvider is an abstract base class."""
        from abc import ABC

        from maverick_india import ConcallProvider

        # ConcallProvider should be an ABC
        assert issubclass(ConcallProvider, ABC)

    def test_concall_provider_has_required_methods(self):
        """Test ConcallProvider has required abstract methods."""
        import inspect

        from maverick_india import ConcallProvider

        # Check for abstract methods
        abstract_methods = {
            name
            for name, method in inspect.getmembers(ConcallProvider)
            if getattr(method, "__isabstractmethod__", False)
        }

        assert "fetch_transcript" in abstract_methods
        assert "is_available" in abstract_methods
        assert "name" in abstract_methods


class TestAllExports:
    """Test that __all__ exports are complete."""

    def test_all_exports_importable(self):
        """Test all items in __all__ can be imported."""
        import maverick_india

        for name in maverick_india.__all__:
            assert hasattr(maverick_india, name), f"Missing export: {name}"

    def test_market_exports_in_all(self):
        """Test market exports are in __all__."""
        import maverick_india

        market_exports = [
            "IndianMarket",
            "IndianMarketDataProvider",
            "INDIAN_MARKET_CONFIG",
            "calculate_circuit_breaker_limits",
            "format_indian_currency",
            "get_nifty_sectors",
            "fetch_nse_data",
            "fetch_bse_data",
        ]
        for name in market_exports:
            assert name in maverick_india.__all__, f"Missing in __all__: {name}"

    def test_economic_exports_in_all(self):
        """Test economic exports are in __all__."""
        import maverick_india

        economic_exports = [
            "RBIDataProvider",
            "EconomicIndicator",
            "get_indian_economic_data",
            "ExchangeRateProvider",
            "ExchangeRateSource",
            "get_exchange_rate",
            "convert_currency",
        ]
        for name in economic_exports:
            assert name in maverick_india.__all__, f"Missing in __all__: {name}"

    def test_news_exports_in_all(self):
        """Test news exports are in __all__."""
        import maverick_india

        news_exports = [
            "BaseNewsScraper",
            "NewsArticleStore",
            "IndianStockSymbolMapper",
            "MoneyControlScraper",
            "EconomicTimesScraper",
            "MultiSourceNewsAggregator",
            "IndianNewsProvider",
            "fetch_moneycontrol_news",
            "fetch_economic_times_news",
            "get_aggregated_news",
            "get_stock_sentiment",
            "get_indian_stock_news",
            "analyze_stock_sentiment",
        ]
        for name in news_exports:
            assert name in maverick_india.__all__, f"Missing in __all__: {name}"

    def test_concall_exports_in_all(self):
        """Test concall exports are in __all__."""
        import maverick_india

        concall_exports = [
            "ConcallProvider",
        ]
        for name in concall_exports:
            assert name in maverick_india.__all__, f"Missing in __all__: {name}"
