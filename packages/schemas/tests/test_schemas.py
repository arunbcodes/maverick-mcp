"""Tests for schema models."""

from datetime import date, datetime, UTC
from decimal import Decimal

from maverick_schemas import (
    APIResponse,
    ErrorResponse,
    PaginatedResponse,
    StockQuote,
    StockInfo,
    OHLCV,
    Position,
    AuthenticatedUser,
)
from maverick_schemas.base import Market, Tier, AuthMethod
from maverick_schemas.responses import PaginationMeta, ResponseMeta


class TestResponseEnvelopes:
    """Tests for API response envelope models."""

    def test_api_response_create(self, sample_request_id):
        data = {"ticker": "AAPL", "price": 150.0}
        response = APIResponse.create(data=data, request_id=sample_request_id)

        assert response.success is True
        assert response.data == data
        assert response.meta.request_id == sample_request_id

    def test_error_response_create(self, sample_request_id):
        response = ErrorResponse.create(
            code="NOT_FOUND",
            message="Stock not found",
            request_id=sample_request_id,
            field="ticker",
        )

        assert response.success is False
        assert response.error.code == "NOT_FOUND"
        assert response.error.message == "Stock not found"
        assert response.error.field == "ticker"

    def test_paginated_response_create(self, sample_request_id):
        data = [{"ticker": "AAPL"}, {"ticker": "MSFT"}]
        response = PaginatedResponse.create(
            data=data,
            request_id=sample_request_id,
            page=1,
            page_size=20,
            total=100,
        )

        assert response.success is True
        assert len(response.data) == 2
        assert response.pagination.page == 1
        assert response.pagination.total == 100
        assert response.pagination.has_next is True

    def test_pagination_meta_calculation(self):
        meta = PaginationMeta.create(page=3, page_size=20, total=100)

        assert meta.total_pages == 5
        assert meta.has_next is True
        assert meta.has_prev is True


class TestStockModels:
    """Tests for stock-related models."""

    def test_stock_quote_creation(self):
        quote = StockQuote(
            ticker="AAPL",
            price=Decimal("150.25"),
            change=Decimal("2.50"),
            change_percent=Decimal("1.69"),
            volume=50000000,
            timestamp=datetime.now(UTC),
        )

        assert quote.ticker == "AAPL"
        assert quote.price == Decimal("150.25")

    def test_stock_info_with_optionals(self):
        info = StockInfo(
            ticker="AAPL",
            name="Apple Inc.",
            market=Market.US,
            sector="Technology",
        )

        assert info.ticker == "AAPL"
        assert info.market == Market.US
        assert info.pe_ratio is None

    def test_ohlcv_creation(self):
        ohlcv = OHLCV(
            date=date(2024, 1, 15),
            open=Decimal("150.00"),
            high=Decimal("152.00"),
            low=Decimal("149.00"),
            close=Decimal("151.50"),
            volume=50000000,
        )

        assert ohlcv.date == date(2024, 1, 15)
        assert ohlcv.close == Decimal("151.50")


class TestPortfolioModels:
    """Tests for portfolio models."""

    def test_position_creation(self):
        position = Position(
            ticker="AAPL",
            shares=Decimal("10"),
            avg_cost=Decimal("150.00"),
            total_cost=Decimal("1500.00"),
        )

        assert position.ticker == "AAPL"
        assert position.shares == Decimal("10")

    def test_position_with_pnl(self):
        position = Position(
            ticker="AAPL",
            shares=Decimal("10"),
            avg_cost=Decimal("150.00"),
            total_cost=Decimal("1500.00"),
            current_price=Decimal("160.00"),
            current_value=Decimal("1600.00"),
            unrealized_pnl=Decimal("100.00"),
            unrealized_pnl_percent=Decimal("6.67"),
        )

        assert position.unrealized_pnl == Decimal("100.00")


class TestAuthModels:
    """Tests for authentication models."""

    def test_authenticated_user_creation(self):
        user = AuthenticatedUser(
            user_id="user-123",
            auth_method=AuthMethod.JWT,
            tier=Tier.PRO,
            rate_limit=1000,
        )

        assert user.user_id == "user-123"
        assert user.auth_method == AuthMethod.JWT
        assert user.tier == Tier.PRO
        assert user.rate_limit == 1000

    def test_authenticated_user_defaults(self):
        user = AuthenticatedUser(
            user_id="user-123",
            auth_method=AuthMethod.API_KEY,
        )

        assert user.tier == Tier.FREE
        assert user.rate_limit == 100


class TestModelSerialization:
    """Tests for model serialization."""

    def test_response_meta_timestamp(self):
        meta = ResponseMeta(request_id="test-123")

        assert meta.timestamp is not None
        assert meta.version == "1.0.0"

    def test_model_to_dict(self):
        quote = StockQuote(
            ticker="AAPL",
            price=Decimal("150.25"),
            change=Decimal("2.50"),
            change_percent=Decimal("1.69"),
            volume=50000000,
            timestamp=datetime.now(UTC),
        )

        data = quote.model_dump()
        assert isinstance(data, dict)
        assert data["ticker"] == "AAPL"

    def test_model_to_json(self):
        quote = StockQuote(
            ticker="AAPL",
            price=Decimal("150.25"),
            change=Decimal("2.50"),
            change_percent=Decimal("1.69"),
            volume=50000000,
            timestamp=datetime.now(UTC),
        )

        json_str = quote.model_dump_json()
        assert isinstance(json_str, str)
        assert "AAPL" in json_str

