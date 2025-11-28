"""Tests for maverick-data repositories."""

import pytest

from maverick_data.repositories import (
    StockRepository,
    PortfolioRepository,
    ScreeningRepository,
)


class TestRepositoryImports:
    """Test that repository components can be imported."""

    def test_stock_repository_import(self):
        """Test StockRepository import."""
        assert StockRepository is not None

    def test_portfolio_repository_import(self):
        """Test PortfolioRepository import."""
        assert PortfolioRepository is not None

    def test_screening_repository_import(self):
        """Test ScreeningRepository import."""
        assert ScreeningRepository is not None


class TestStockRepository:
    """Test StockRepository class."""

    def test_create_stock_repository(self):
        """Test creating stock repository."""
        repo = StockRepository()
        assert repo is not None

    def test_repository_has_required_methods(self):
        """Test repository has all required interface methods."""
        repo = StockRepository()

        # IStockRepository methods
        assert hasattr(repo, "get_stock")
        assert hasattr(repo, "save_stock")
        assert hasattr(repo, "get_price_history")
        assert hasattr(repo, "save_price_history")
        assert hasattr(repo, "get_stocks_by_sector")
        assert hasattr(repo, "search_stocks")
        assert hasattr(repo, "get_all_symbols")

    def test_additional_methods(self):
        """Test additional utility methods."""
        repo = StockRepository()

        assert hasattr(repo, "get_stocks_by_market")
        assert hasattr(repo, "count_stocks")


class TestPortfolioRepository:
    """Test PortfolioRepository class."""

    def test_create_portfolio_repository(self):
        """Test creating portfolio repository."""
        repo = PortfolioRepository()
        assert repo is not None

    def test_repository_has_required_methods(self):
        """Test repository has all required interface methods."""
        repo = PortfolioRepository()

        # IPortfolioRepository methods
        assert hasattr(repo, "get_portfolio")
        assert hasattr(repo, "save_portfolio")
        assert hasattr(repo, "get_positions")
        assert hasattr(repo, "save_position")
        assert hasattr(repo, "delete_position")
        assert hasattr(repo, "get_user_portfolios")
        assert hasattr(repo, "clear_portfolio")

    def test_additional_methods(self):
        """Test additional utility methods."""
        repo = PortfolioRepository()

        assert hasattr(repo, "get_portfolio_by_id")
        assert hasattr(repo, "get_position")
        assert hasattr(repo, "update_position_shares")
        assert hasattr(repo, "delete_portfolio")
        assert hasattr(repo, "get_or_create_portfolio")


class TestScreeningRepository:
    """Test ScreeningRepository class."""

    def test_create_screening_repository(self):
        """Test creating screening repository."""
        repo = ScreeningRepository()
        assert repo is not None

    def test_repository_has_required_methods(self):
        """Test repository has all required interface methods."""
        repo = ScreeningRepository()

        # IScreeningRepository methods
        assert hasattr(repo, "save_screening_result")
        assert hasattr(repo, "get_screening_results")
        assert hasattr(repo, "get_latest_screening_timestamp")

    def test_additional_methods(self):
        """Test additional utility methods."""
        repo = ScreeningRepository()

        assert hasattr(repo, "get_all_screening_results")
        assert hasattr(repo, "count_screening_results")
        assert hasattr(repo, "clear_screening_results")
