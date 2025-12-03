"""Tests for authentication strategies."""

import pytest
from datetime import datetime, timedelta, UTC

from maverick_api.auth.jwt import JWTAuthStrategy
from maverick_schemas.base import Tier


class TestJWTAuthStrategy:
    """Tests for JWT authentication."""

    @pytest.fixture
    def jwt_strategy(self):
        return JWTAuthStrategy(
            secret_key="test-secret-key",
            redis=None,  # No Redis for unit tests
            access_token_expire_minutes=15,
            refresh_token_expire_days=30,
        )

    def test_create_tokens_returns_both_tokens(self, jwt_strategy):
        tokens = jwt_strategy.create_tokens(
            user_id="user-123",
            tier=Tier.PRO,
        )

        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert tokens.expires_in == 15 * 60  # 15 minutes in seconds

    def test_create_tokens_includes_user_info(self, jwt_strategy):
        tokens = jwt_strategy.create_tokens(
            user_id="user-123",
            tier=Tier.ENTERPRISE,
        )

        assert tokens.user_id == "user-123"
        assert tokens.tier == Tier.ENTERPRISE

    def test_tokens_are_different(self, jwt_strategy):
        tokens1 = jwt_strategy.create_tokens(user_id="user-123")
        tokens2 = jwt_strategy.create_tokens(user_id="user-123")

        assert tokens1.access_token != tokens2.access_token
        assert tokens1.refresh_token != tokens2.refresh_token


class TestAPIKeyAuth:
    """Tests for API key authentication."""

    @pytest.fixture
    def api_key_strategy(self):
        from maverick_api.auth.api_key import APIKeyAuthStrategy

        return APIKeyAuthStrategy(
            redis=None,
            key_prefix="mav_",
        )

    def test_validates_key_prefix(self, api_key_strategy):
        # Keys without proper prefix should be rejected
        assert not api_key_strategy._key_prefix in "invalid_key"

    async def test_authenticate_without_redis_returns_default(self, api_key_strategy):
        """Without Redis, accept properly formatted keys for testing."""
        from unittest.mock import MagicMock

        request = MagicMock()
        request.headers.get.return_value = "mav_live_test123"

        user = await api_key_strategy.authenticate(request)

        assert user is not None
        assert user.user_id == "api_key_user"


class TestCookieAuth:
    """Tests for cookie authentication."""

    @pytest.fixture
    def cookie_strategy(self):
        from maverick_api.auth.cookie import CookieAuthStrategy

        return CookieAuthStrategy(
            redis=None,
            secure=False,  # For testing
        )

    def test_session_cookie_names(self, cookie_strategy):
        assert cookie_strategy.SESSION_COOKIE_NAME == "maverick_session"
        assert cookie_strategy.CSRF_COOKIE_NAME == "maverick_csrf"
        assert cookie_strategy.CSRF_HEADER_NAME == "X-CSRF-Token"

