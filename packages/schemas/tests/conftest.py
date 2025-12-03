"""Pytest configuration for schemas tests."""

import pytest


@pytest.fixture
def sample_ticker():
    """Sample ticker for testing."""
    return "AAPL"


@pytest.fixture
def sample_request_id():
    """Sample request ID for testing."""
    return "test-request-123"

