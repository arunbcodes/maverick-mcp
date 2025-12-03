"""Pytest configuration for API tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from httpx import AsyncClient

from maverick_api import create_app
from maverick_api.config import Settings


@pytest.fixture
def test_settings():
    """Test settings with sensible defaults."""
    return Settings(
        environment="development",
        debug=True,
        jwt_secret="test-secret-key-for-testing-only",
        rate_limit_enabled=False,
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:56379",
    )


@pytest.fixture
def app(test_settings):
    """Create test application."""
    return create_app(settings=test_settings, testing=True)


@pytest.fixture
def client(app):
    """Synchronous test client."""
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """Async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_stock_service():
    """Mock stock service."""
    from decimal import Decimal
    from datetime import datetime, UTC
    from maverick_schemas.stock import StockQuote, StockInfo, StockHistory, OHLCV
    from maverick_schemas.base import Market

    service = AsyncMock()

    service.get_quote = AsyncMock(
        return_value=StockQuote(
            ticker="AAPL",
            price=Decimal("150.25"),
            change=Decimal("2.50"),
            change_percent=Decimal("1.69"),
            volume=50000000,
            timestamp=datetime.now(UTC),
        )
    )

    service.get_info = AsyncMock(
        return_value=StockInfo(
            ticker="AAPL",
            name="Apple Inc.",
            market=Market.US,
            sector="Technology",
        )
    )

    service.get_history = AsyncMock(
        return_value=StockHistory(
            ticker="AAPL",
            data=[
                OHLCV(
                    date="2024-01-15",
                    open=Decimal("150.00"),
                    high=Decimal("152.00"),
                    low=Decimal("149.00"),
                    close=Decimal("151.00"),
                    volume=50000000,
                )
            ],
            start_date="2024-01-15",
            end_date="2024-01-15",
            data_points=1,
        )
    )

    return service


@pytest.fixture
def auth_headers():
    """Headers for authenticated requests."""
    return {"X-API-Key": "mav_test_key_for_testing"}


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    from maverick_schemas.auth import AuthenticatedUser
    from maverick_schemas.base import AuthMethod, Tier

    return AuthenticatedUser(
        user_id="test-user-123",
        auth_method=AuthMethod.API_KEY,
        tier=Tier.PRO,
        rate_limit=1000,
    )

