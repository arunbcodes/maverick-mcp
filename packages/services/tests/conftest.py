"""Pytest configuration for services tests."""

import pytest
from datetime import datetime, UTC
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pandas as pd


@pytest.fixture
def sample_ticker():
    """Sample ticker for testing."""
    return "AAPL"


@pytest.fixture
def mock_stock_data():
    """Sample stock data as DataFrame."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    return pd.DataFrame(
        {
            "Open": [150.0 + i * 0.1 for i in range(100)],
            "High": [152.0 + i * 0.1 for i in range(100)],
            "Low": [148.0 + i * 0.1 for i in range(100)],
            "Close": [151.0 + i * 0.1 for i in range(100)],
            "Volume": [50000000 + i * 1000 for i in range(100)],
        },
        index=dates,
    )


@pytest.fixture
def mock_provider(mock_stock_data):
    """Mock stock data provider."""
    provider = AsyncMock()
    provider.get_stock_data = AsyncMock(return_value=mock_stock_data)
    provider.get_stock_info = AsyncMock(
        return_value={
            "longName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "marketCap": 3000000000000,
            "trailingPE": 30.5,
        }
    )
    return provider


@pytest.fixture
def mock_cache():
    """Mock cache provider."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=None)
    return cache


@pytest.fixture
def mock_portfolio_repository():
    """Mock portfolio repository."""
    repo = AsyncMock()
    repo.get_portfolio = AsyncMock(return_value={"name": "My Portfolio"})
    repo.get_positions = AsyncMock(
        return_value=[
            {
                "id": "1",
                "ticker": "AAPL",
                "shares": 10,
                "avg_cost": 150.0,
                "total_cost": 1500.0,
            }
        ]
    )
    repo.get_position = AsyncMock(return_value=None)
    repo.create_position = AsyncMock(
        return_value={"id": "2", "ticker": "MSFT", "shares": 5}
    )
    repo.update_position = AsyncMock(return_value={"id": "1", "ticker": "AAPL"})
    repo.delete_position = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_screening_repository():
    """Mock screening repository."""
    repo = AsyncMock()
    repo.get_maverick_stocks = AsyncMock(
        return_value=[
            {
                "ticker": "NVDA",
                "name": "NVIDIA Corporation",
                "maverick_score": 85.5,
                "momentum_score": 78.0,
                "current_price": 450.0,
                "rsi": 55.0,
                "above_sma_50": True,
                "above_sma_200": True,
            },
            {
                "ticker": "TSLA",
                "name": "Tesla Inc.",
                "maverick_score": 72.0,
                "momentum_score": 65.0,
                "current_price": 250.0,
                "rsi": 48.0,
                "above_sma_50": True,
                "above_sma_200": False,
            },
        ]
    )
    repo.get_maverick_bear_stocks = AsyncMock(return_value=[])
    repo.get_breakout_stocks = AsyncMock(return_value=[])
    return repo

