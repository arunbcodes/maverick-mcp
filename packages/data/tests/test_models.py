"""Tests for maverick-data models."""

import pytest

from maverick_data.models import (
    Base,
    TimestampMixin,
    Stock,
    PriceCache,
    ExchangeRate,
    NewsArticle,
    TechnicalCache,
    MaverickStocks,
    MaverickBearStocks,
    SupplyDemandBreakoutStocks,
    BacktestResult,
    BacktestTrade,
    OptimizationResult,
    WalkForwardTest,
    BacktestPortfolio,
    UserPortfolio,
    PortfolioPosition,
)


class TestModelsImport:
    """Test that all models can be imported."""

    def test_base_imports(self):
        """Test Base and TimestampMixin import."""
        assert Base is not None
        assert TimestampMixin is not None

    def test_core_models_import(self):
        """Test core models import."""
        assert Stock is not None
        assert PriceCache is not None
        assert ExchangeRate is not None
        assert NewsArticle is not None
        assert TechnicalCache is not None

    def test_screening_models_import(self):
        """Test screening models import."""
        assert MaverickStocks is not None
        assert MaverickBearStocks is not None
        assert SupplyDemandBreakoutStocks is not None

    def test_backtest_models_import(self):
        """Test backtest models import."""
        assert BacktestResult is not None
        assert BacktestTrade is not None
        assert OptimizationResult is not None
        assert WalkForwardTest is not None
        assert BacktestPortfolio is not None

    def test_portfolio_models_import(self):
        """Test portfolio models import."""
        assert UserPortfolio is not None
        assert PortfolioPosition is not None


class TestModelTableNames:
    """Test that models have correct table names."""

    def test_stock_table_name(self):
        """Test Stock table name."""
        assert Stock.__tablename__ == "mcp_stocks"

    def test_price_cache_table_name(self):
        """Test PriceCache table name."""
        assert PriceCache.__tablename__ == "mcp_price_cache"

    def test_exchange_rate_table_name(self):
        """Test ExchangeRate table name."""
        assert ExchangeRate.__tablename__ == "mcp_exchange_rates"

    def test_news_article_table_name(self):
        """Test NewsArticle table name."""
        assert NewsArticle.__tablename__ == "mcp_news_articles"

    def test_technical_cache_table_name(self):
        """Test TechnicalCache table name."""
        assert TechnicalCache.__tablename__ == "mcp_technical_cache"

    def test_maverick_stocks_table_name(self):
        """Test MaverickStocks table name."""
        assert MaverickStocks.__tablename__ == "mcp_maverick_stocks"

    def test_maverick_bear_stocks_table_name(self):
        """Test MaverickBearStocks table name."""
        assert MaverickBearStocks.__tablename__ == "mcp_maverick_bear_stocks"

    def test_supply_demand_breakouts_table_name(self):
        """Test SupplyDemandBreakoutStocks table name."""
        assert SupplyDemandBreakoutStocks.__tablename__ == "mcp_supply_demand_breakouts"

    def test_backtest_result_table_name(self):
        """Test BacktestResult table name."""
        assert BacktestResult.__tablename__ == "mcp_backtest_results"

    def test_backtest_trade_table_name(self):
        """Test BacktestTrade table name."""
        assert BacktestTrade.__tablename__ == "mcp_backtest_trades"

    def test_optimization_result_table_name(self):
        """Test OptimizationResult table name."""
        assert OptimizationResult.__tablename__ == "mcp_optimization_results"

    def test_walk_forward_test_table_name(self):
        """Test WalkForwardTest table name."""
        assert WalkForwardTest.__tablename__ == "mcp_walk_forward_tests"

    def test_backtest_portfolio_table_name(self):
        """Test BacktestPortfolio table name."""
        assert BacktestPortfolio.__tablename__ == "mcp_backtest_portfolios"

    def test_user_portfolio_table_name(self):
        """Test UserPortfolio table name."""
        assert UserPortfolio.__tablename__ == "mcp_portfolios"

    def test_portfolio_position_table_name(self):
        """Test PortfolioPosition table name."""
        assert PortfolioPosition.__tablename__ == "mcp_portfolio_positions"


class TestModelInheritance:
    """Test that models inherit from correct base classes."""

    def test_stock_inherits_base(self):
        """Test Stock inherits from Base."""
        assert issubclass(Stock, Base)

    def test_price_cache_inherits_base(self):
        """Test PriceCache inherits from Base."""
        assert issubclass(PriceCache, Base)

    def test_backtest_result_inherits_base(self):
        """Test BacktestResult inherits from Base."""
        assert issubclass(BacktestResult, Base)

    def test_user_portfolio_inherits_base(self):
        """Test UserPortfolio inherits from Base."""
        assert issubclass(UserPortfolio, Base)
