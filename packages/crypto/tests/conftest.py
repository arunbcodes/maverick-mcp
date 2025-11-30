"""Pytest configuration for maverick_crypto tests."""

import sys
from pathlib import Path

import pytest

# Add package to path
package_path = Path(__file__).parent.parent / "src"
if str(package_path) not in sys.path:
    sys.path.insert(0, str(package_path))


@pytest.fixture
def crypto_provider():
    """Create a CryptoDataProvider instance."""
    from maverick_crypto.providers import CryptoDataProvider
    return CryptoDataProvider()


@pytest.fixture
def calendar_service():
    """Create a CryptoCalendarService instance."""
    from maverick_crypto.calendar import CryptoCalendarService
    return CryptoCalendarService()

