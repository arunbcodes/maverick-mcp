"""
Pytest configuration for service tests.

These are unit tests that don't require Docker/database/Redis.
This conftest prevents the parent conftest from loading heavy fixtures.
"""

import pytest


# Prevent parent conftest fixtures from being auto-used
def pytest_configure(config):
    """Configure pytest for service tests."""
    # Mark these as unit tests
    config.addinivalue_line(
        "markers", "services: mark test as a service unit test"
    )

