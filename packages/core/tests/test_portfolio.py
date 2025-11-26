"""Tests for Portfolio domain entities."""

from datetime import datetime, UTC
from decimal import Decimal

import pytest

from maverick_core.domain.portfolio import Portfolio, Position


class TestPosition:
    """Tests for Position value object."""

    def test_create_position(self):
        """Test creating a valid position."""
        pos = Position(
            ticker="AAPL",
            shares=Decimal("10"),
            average_cost_basis=Decimal("150.00"),
            total_cost=Decimal("1500.00"),
            purchase_date=datetime.now(UTC),
        )
        assert pos.ticker == "AAPL"
        assert pos.shares == Decimal("10")
        assert pos.average_cost_basis == Decimal("150.00")

    def test_ticker_normalized_to_uppercase(self):
        """Test that ticker is normalized to uppercase."""
        pos = Position(
            ticker="aapl",
            shares=Decimal("10"),
            average_cost_basis=Decimal("150.00"),
            total_cost=Decimal("1500.00"),
            purchase_date=datetime.now(UTC),
        )
        assert pos.ticker == "AAPL"

    def test_invalid_shares_raises_error(self):
        """Test that zero or negative shares raises ValueError."""
        with pytest.raises(ValueError, match="Shares must be positive"):
            Position(
                ticker="AAPL",
                shares=Decimal("0"),
                average_cost_basis=Decimal("150.00"),
                total_cost=Decimal("0"),
                purchase_date=datetime.now(UTC),
            )

    def test_invalid_cost_basis_raises_error(self):
        """Test that zero or negative cost basis raises ValueError."""
        with pytest.raises(ValueError, match="Average cost basis must be positive"):
            Position(
                ticker="AAPL",
                shares=Decimal("10"),
                average_cost_basis=Decimal("-150.00"),
                total_cost=Decimal("1500.00"),
                purchase_date=datetime.now(UTC),
            )

    def test_add_shares_averages_cost(self):
        """Test that adding shares properly averages cost basis."""
        pos = Position(
            ticker="AAPL",
            shares=Decimal("10"),
            average_cost_basis=Decimal("150.00"),
            total_cost=Decimal("1500.00"),
            purchase_date=datetime.now(UTC),
        )

        new_pos = pos.add_shares(
            shares=Decimal("10"),
            price=Decimal("170.00"),
            date=datetime.now(UTC),
        )

        assert new_pos.shares == Decimal("20")
        # (1500 + 1700) / 20 = 160
        assert new_pos.average_cost_basis == Decimal("160.0000")
        assert new_pos.total_cost == Decimal("3200.00")

    def test_add_shares_invalid_raises_error(self):
        """Test that adding invalid shares raises ValueError."""
        pos = Position(
            ticker="AAPL",
            shares=Decimal("10"),
            average_cost_basis=Decimal("150.00"),
            total_cost=Decimal("1500.00"),
            purchase_date=datetime.now(UTC),
        )

        with pytest.raises(ValueError, match="Shares to add must be positive"):
            pos.add_shares(Decimal("0"), Decimal("150.00"), datetime.now(UTC))

    def test_remove_shares_partial(self):
        """Test removing some shares from position."""
        pos = Position(
            ticker="AAPL",
            shares=Decimal("20"),
            average_cost_basis=Decimal("160.00"),
            total_cost=Decimal("3200.00"),
            purchase_date=datetime.now(UTC),
        )

        new_pos = pos.remove_shares(Decimal("10"))

        assert new_pos is not None
        assert new_pos.shares == Decimal("10")
        assert new_pos.average_cost_basis == Decimal("160.00")  # Unchanged

    def test_remove_all_shares_returns_none(self):
        """Test removing all shares returns None."""
        pos = Position(
            ticker="AAPL",
            shares=Decimal("10"),
            average_cost_basis=Decimal("150.00"),
            total_cost=Decimal("1500.00"),
            purchase_date=datetime.now(UTC),
        )

        result = pos.remove_shares(Decimal("10"))
        assert result is None

    def test_calculate_current_value_profit(self):
        """Test calculating P&L when in profit."""
        pos = Position(
            ticker="AAPL",
            shares=Decimal("10"),
            average_cost_basis=Decimal("150.00"),
            total_cost=Decimal("1500.00"),
            purchase_date=datetime.now(UTC),
        )

        metrics = pos.calculate_current_value(Decimal("175.00"))

        assert metrics["current_value"] == Decimal("1750.00")
        assert metrics["unrealized_pnl"] == Decimal("250.00")
        assert metrics["pnl_percentage"] == Decimal("16.67")

    def test_calculate_current_value_loss(self):
        """Test calculating P&L when at loss."""
        pos = Position(
            ticker="AAPL",
            shares=Decimal("10"),
            average_cost_basis=Decimal("150.00"),
            total_cost=Decimal("1500.00"),
            purchase_date=datetime.now(UTC),
        )

        metrics = pos.calculate_current_value(Decimal("125.00"))

        assert metrics["current_value"] == Decimal("1250.00")
        assert metrics["unrealized_pnl"] == Decimal("-250.00")
        assert metrics["pnl_percentage"] == Decimal("-16.67")

    def test_to_dict(self):
        """Test converting position to dictionary."""
        now = datetime.now(UTC)
        pos = Position(
            ticker="AAPL",
            shares=Decimal("10"),
            average_cost_basis=Decimal("150.00"),
            total_cost=Decimal("1500.00"),
            purchase_date=now,
            notes="Test position",
        )

        data = pos.to_dict()

        assert data["ticker"] == "AAPL"
        assert data["shares"] == 10.0
        assert data["average_cost_basis"] == 150.0
        assert data["notes"] == "Test position"


class TestPortfolio:
    """Tests for Portfolio aggregate root."""

    def test_create_portfolio(self):
        """Test creating a portfolio."""
        portfolio = Portfolio(
            portfolio_id="test-id",
            user_id="default",
            name="My Portfolio",
        )

        assert portfolio.portfolio_id == "test-id"
        assert portfolio.name == "My Portfolio"
        assert len(portfolio.positions) == 0

    def test_add_new_position(self):
        """Test adding a new position to portfolio."""
        portfolio = Portfolio("id", "default", "Test")

        portfolio.add_position(
            ticker="AAPL",
            shares=Decimal("10"),
            price=Decimal("150.00"),
            date=datetime.now(UTC),
        )

        assert len(portfolio.positions) == 1
        pos = portfolio.get_position("AAPL")
        assert pos is not None
        assert pos.shares == Decimal("10")

    def test_add_to_existing_position_averages_cost(self):
        """Test that adding to existing position averages cost basis."""
        portfolio = Portfolio("id", "default", "Test")

        portfolio.add_position("AAPL", Decimal("10"), Decimal("150.00"), datetime.now(UTC))
        portfolio.add_position("AAPL", Decimal("10"), Decimal("170.00"), datetime.now(UTC))

        assert len(portfolio.positions) == 1
        pos = portfolio.get_position("AAPL")
        assert pos.shares == Decimal("20")
        assert pos.average_cost_basis == Decimal("160.0000")

    def test_remove_position_full(self):
        """Test removing entire position."""
        portfolio = Portfolio("id", "default", "Test")
        portfolio.add_position("AAPL", Decimal("10"), Decimal("150.00"), datetime.now(UTC))

        result = portfolio.remove_position("AAPL")

        assert result is True
        assert len(portfolio.positions) == 0

    def test_remove_position_partial(self):
        """Test removing partial position."""
        portfolio = Portfolio("id", "default", "Test")
        portfolio.add_position("AAPL", Decimal("20"), Decimal("150.00"), datetime.now(UTC))

        result = portfolio.remove_position("AAPL", Decimal("10"))

        assert result is True
        pos = portfolio.get_position("AAPL")
        assert pos.shares == Decimal("10")

    def test_remove_nonexistent_position_returns_false(self):
        """Test removing non-existent position returns False."""
        portfolio = Portfolio("id", "default", "Test")

        result = portfolio.remove_position("AAPL")

        assert result is False

    def test_get_position_case_insensitive(self):
        """Test that get_position is case insensitive."""
        portfolio = Portfolio("id", "default", "Test")
        portfolio.add_position("AAPL", Decimal("10"), Decimal("150.00"), datetime.now(UTC))

        assert portfolio.get_position("aapl") is not None
        assert portfolio.get_position("AAPL") is not None
        assert portfolio.get_position("Aapl") is not None

    def test_get_total_invested(self):
        """Test calculating total invested."""
        portfolio = Portfolio("id", "default", "Test")
        portfolio.add_position("AAPL", Decimal("10"), Decimal("150.00"), datetime.now(UTC))
        portfolio.add_position("MSFT", Decimal("5"), Decimal("300.00"), datetime.now(UTC))

        total = portfolio.get_total_invested()

        assert total == Decimal("3000.00")  # 1500 + 1500

    def test_get_tickers(self):
        """Test getting list of tickers."""
        portfolio = Portfolio("id", "default", "Test")
        portfolio.add_position("AAPL", Decimal("10"), Decimal("150.00"), datetime.now(UTC))
        portfolio.add_position("MSFT", Decimal("5"), Decimal("300.00"), datetime.now(UTC))

        tickers = portfolio.get_tickers()

        assert set(tickers) == {"AAPL", "MSFT"}

    def test_calculate_portfolio_metrics(self):
        """Test calculating portfolio metrics."""
        portfolio = Portfolio("id", "default", "Test")
        portfolio.add_position("AAPL", Decimal("10"), Decimal("150.00"), datetime.now(UTC))
        portfolio.add_position("MSFT", Decimal("5"), Decimal("300.00"), datetime.now(UTC))

        prices = {
            "AAPL": Decimal("175.00"),  # Profit
            "MSFT": Decimal("280.00"),  # Loss
        }

        metrics = portfolio.calculate_portfolio_metrics(prices)

        assert metrics["position_count"] == 2
        assert metrics["total_invested"] == 3000.0
        # AAPL: 10 * 175 = 1750, MSFT: 5 * 280 = 1400, Total = 3150
        assert metrics["total_value"] == 3150.0
        assert metrics["total_pnl"] == 150.0

    def test_clear_all_positions(self):
        """Test clearing all positions."""
        portfolio = Portfolio("id", "default", "Test")
        portfolio.add_position("AAPL", Decimal("10"), Decimal("150.00"), datetime.now(UTC))
        portfolio.add_position("MSFT", Decimal("5"), Decimal("300.00"), datetime.now(UTC))

        portfolio.clear_all_positions()

        assert len(portfolio.positions) == 0

    def test_to_dict(self):
        """Test converting portfolio to dictionary."""
        portfolio = Portfolio("id", "default", "Test Portfolio")
        portfolio.add_position("AAPL", Decimal("10"), Decimal("150.00"), datetime.now(UTC))

        data = portfolio.to_dict()

        assert data["portfolio_id"] == "id"
        assert data["name"] == "Test Portfolio"
        assert data["position_count"] == 1
        assert len(data["positions"]) == 1
