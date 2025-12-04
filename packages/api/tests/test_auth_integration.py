"""Integration tests for authentication endpoints."""

import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from maverick_schemas.auth import AuthenticatedUser
from maverick_schemas.base import AuthMethod, Tier


@pytest.fixture
def mock_user_service():
    """Mock user service for testing."""
    service = AsyncMock()
    
    # Default successful register
    service.register = AsyncMock(
        return_value={
            "user_id": str(uuid4()),
            "email": "test@example.com",
            "tier": "free",
        }
    )
    
    # Default successful authenticate (auth_method set by service as "password" string)
    service.authenticate = AsyncMock(
        return_value=AuthenticatedUser(
            user_id=str(uuid4()),
            email="test@example.com",
            auth_method="password",  # UserService returns string for password auth
            tier=Tier.FREE,
        )
    )
    
    # Default get_by_id
    service.get_by_id = AsyncMock(
        return_value={
            "user_id": str(uuid4()),
            "email": "test@example.com",
            "tier": "free",
            "email_verified": False,
            "created_at": datetime.now(UTC).isoformat(),
            "last_login_at": None,
        }
    )
    
    # Default update_password
    service.update_password = AsyncMock(return_value=True)
    
    return service


@pytest.fixture
def mock_jwt_strategy():
    """Mock JWT strategy for testing."""
    from maverick_schemas.auth import TokenResponse
    
    strategy = MagicMock()
    strategy.create_tokens = MagicMock(
        return_value=TokenResponse(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            token_type="bearer",
            expires_in=900,
            user_id=str(uuid4()),
            tier=Tier.FREE,
        )
    )
    strategy.refresh_tokens = AsyncMock(
        return_value=TokenResponse(
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            token_type="bearer",
            expires_in=900,
            user_id=str(uuid4()),
            tier=Tier.FREE,
        )
    )
    return strategy


@pytest.fixture
def mock_cookie_strategy():
    """Mock cookie strategy for testing."""
    strategy = AsyncMock()
    strategy.create_session = AsyncMock(return_value=("session_id", "csrf_token"))
    strategy.invalidate_session = AsyncMock()
    strategy.SESSION_COOKIE_NAME = "maverick_session"
    strategy.CSRF_COOKIE_NAME = "maverick_csrf"
    return strategy


@pytest.fixture
def app_with_mocks(mock_user_service, mock_jwt_strategy, mock_cookie_strategy):
    """Create test app with mocked dependencies."""
    from fastapi import FastAPI
    from maverick_api.routers.v1 import auth
    from maverick_api.routers import health
    from maverick_api.dependencies import get_current_user
    
    # Create minimal test app without auth middleware
    app = FastAPI(title="Test App")
    
    # Include routers (auth.router has prefix="/auth" internally)
    app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
    app.include_router(health.router, tags=["Health"])
    
    # Override dependencies
    async def get_user_service_override():
        return mock_user_service
    
    async def get_jwt_strategy_override():
        return mock_jwt_strategy
    
    async def get_cookie_strategy_override():
        return mock_cookie_strategy
    
    async def get_current_user_override():
        return AuthenticatedUser(
            user_id="test-user-123",
            auth_method=AuthMethod.JWT,
            tier=Tier.FREE,
            email="test@example.com",
        )
    
    app.dependency_overrides[auth.get_user_service] = get_user_service_override
    app.dependency_overrides[auth.get_jwt_strategy] = get_jwt_strategy_override
    app.dependency_overrides[auth.get_cookie_strategy] = get_cookie_strategy_override
    
    # Override get_current_user for protected endpoints
    app.dependency_overrides[get_current_user] = get_current_user_override
    
    return app


@pytest.fixture
def client(app_with_mocks):
    """Test client with mocked dependencies."""
    return TestClient(app_with_mocks)


class TestRegisterEndpoint:
    """Tests for POST /api/v1/auth/register"""

    def test_register_success(self, client, mock_user_service):
        """Successfully register a new user."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure_password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "test@example.com"
        mock_user_service.register.assert_called_once()

    def test_register_invalid_email(self, client):
        """Invalid email returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "secure_password123"},
        )

        assert response.status_code == 422

    def test_register_short_password(self, client):
        """Short password returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "short"},
        )

        assert response.status_code == 422

    def test_register_missing_fields(self, client):
        """Missing fields returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={},
        )

        assert response.status_code == 422

    def test_register_duplicate_email(self, client, mock_user_service):
        """Duplicate email returns 409."""
        from maverick_services.exceptions import ConflictError

        mock_user_service.register.side_effect = ConflictError("Email already exists")

        response = client.post(
            "/api/v1/auth/register",
            json={"email": "existing@example.com", "password": "secure_password123"},
        )

        assert response.status_code == 409


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login"""

    def test_login_success(self, client, mock_user_service, mock_jwt_strategy):
        """Successfully login returns tokens."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "correct_password"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        mock_user_service.authenticate.assert_called_once()

    def test_login_invalid_credentials(self, client, mock_user_service):
        """Invalid credentials returns 401."""
        from maverick_services.exceptions import AuthenticationError

        mock_user_service.authenticate.side_effect = AuthenticationError(
            "Invalid email or password"
        )

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrong_password"},
        )

        assert response.status_code == 401

    def test_login_missing_password(self, client):
        """Missing password returns 422."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com"},
        )

        assert response.status_code == 422

    def test_login_sets_cookies(self, client, mock_cookie_strategy):
        """Login sets session cookies for web clients."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "correct_password"},
        )

        assert response.status_code == 200
        mock_cookie_strategy.create_session.assert_called_once()


class TestRefreshEndpoint:
    """Tests for POST /api/v1/auth/refresh"""

    def test_refresh_success(self, client, mock_jwt_strategy):
        """Successfully refresh tokens."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "valid_refresh_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["access_token"] == "new_access_token"
        assert data["data"]["refresh_token"] == "new_refresh_token"
        mock_jwt_strategy.refresh_tokens.assert_called_once()

    def test_refresh_invalid_token(self, client, mock_jwt_strategy):
        """Invalid refresh token returns 401."""
        from fastapi import HTTPException

        mock_jwt_strategy.refresh_tokens.side_effect = HTTPException(
            status_code=401, detail="Invalid refresh token"
        )

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )

        assert response.status_code == 401

    def test_refresh_missing_token(self, client):
        """Missing refresh token returns 422."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={},
        )

        assert response.status_code == 422


class TestLogoutEndpoint:
    """Tests for POST /api/v1/auth/logout"""

    def test_logout_success(self, client, mock_cookie_strategy):
        """Successfully logout clears session."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "logged out" in data["data"]["message"].lower()


class TestMeEndpoint:
    """Tests for GET /api/v1/auth/me"""

    def test_me_success(self, client, mock_user_service):
        """Get current user profile."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user_id" in data["data"]
        assert "email" in data["data"]
        mock_user_service.get_by_id.assert_called_once()

    def test_me_user_not_found(self, client, mock_user_service):
        """User not found returns 404."""
        from maverick_services.exceptions import NotFoundError

        mock_user_service.get_by_id.side_effect = NotFoundError("User not found")

        response = client.get("/api/v1/auth/me")

        assert response.status_code == 404


class TestChangePasswordEndpoint:
    """Tests for PUT /api/v1/auth/password"""

    def test_change_password_success(self, client, mock_user_service):
        """Successfully change password."""
        response = client.put(
            "/api/v1/auth/password",
            json={
                "current_password": "old_password123",
                "new_password": "new_secure_password123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "updated" in data["data"]["message"].lower()
        mock_user_service.update_password.assert_called_once()

    def test_change_password_wrong_current(self, client, mock_user_service):
        """Wrong current password returns 401."""
        from maverick_services.exceptions import AuthenticationError

        mock_user_service.update_password.side_effect = AuthenticationError(
            "Current password is incorrect"
        )

        response = client.put(
            "/api/v1/auth/password",
            json={
                "current_password": "wrong_password",
                "new_password": "new_secure_password123",
            },
        )

        assert response.status_code == 401

    def test_change_password_short_new(self, client):
        """Short new password returns 422."""
        response = client.put(
            "/api/v1/auth/password",
            json={
                "current_password": "current123",
                "new_password": "short",  # Less than 8 characters
            },
        )

        assert response.status_code == 422

    def test_change_password_missing_fields(self, client):
        """Missing fields returns 422."""
        response = client.put(
            "/api/v1/auth/password",
            json={},
        )

        assert response.status_code == 422


class TestResponseFormat:
    """Tests for consistent API response format."""

    def test_success_response_has_meta(self, client):
        """Successful responses include meta with request_id and timestamp."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "secure_password123"},
        )

        data = response.json()
        assert "meta" in data
        assert "request_id" in data["meta"]
        assert "timestamp" in data["meta"]

    def test_error_response_format(self, client, mock_user_service):
        """Error responses have consistent format."""
        from maverick_services.exceptions import AuthenticationError

        mock_user_service.authenticate.side_effect = AuthenticationError("Invalid")

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword123"},  # Valid format
        )

        assert response.status_code == 401
        # FastAPI HTTPException returns detail field
        data = response.json()
        assert "detail" in data


# --- API Key Endpoint Tests ---


@pytest.fixture
def mock_api_key_service():
    """Mock API key service for testing."""
    service = AsyncMock()
    
    # Default successful create
    service.create_key = AsyncMock(
        return_value={
            "key_id": str(uuid4()),
            "key": "mav_abc12345xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "key_prefix": "mav_abc12345",
            "name": "Test Key",
            "tier": "free",
            "created_at": datetime.now(UTC).isoformat(),
            "expires_at": None,
        }
    )
    
    # Default successful list
    service.list_keys = AsyncMock(
        return_value=[
            {
                "key_id": str(uuid4()),
                "key_prefix": "mav_abc12345",
                "name": "Test Key 1",
                "tier": "free",
                "rate_limit": None,
                "last_used_at": None,
                "created_at": datetime.now(UTC).isoformat(),
                "expires_at": None,
            },
            {
                "key_id": str(uuid4()),
                "key_prefix": "mav_def67890",
                "name": "Test Key 2",
                "tier": "pro",
                "rate_limit": 1000,
                "last_used_at": datetime.now(UTC).isoformat(),
                "created_at": datetime.now(UTC).isoformat(),
                "expires_at": None,
            },
        ]
    )
    
    # Default successful revoke
    service.revoke_key = AsyncMock(return_value=True)
    
    return service


@pytest.fixture
def app_with_api_key_mocks(mock_user_service, mock_jwt_strategy, mock_cookie_strategy, mock_api_key_service):
    """Create test app with API key service mocked."""
    from fastapi import FastAPI
    from maverick_api.routers.v1 import auth
    from maverick_api.dependencies import get_current_user
    
    app = FastAPI(title="Test App")
    app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
    
    async def get_user_service_override():
        return mock_user_service
    
    async def get_jwt_strategy_override():
        return mock_jwt_strategy
    
    async def get_cookie_strategy_override():
        return mock_cookie_strategy
    
    async def get_api_key_service_override():
        return mock_api_key_service
    
    async def get_current_user_override():
        return AuthenticatedUser(
            user_id="test-user-123",
            auth_method=AuthMethod.JWT,
            tier=Tier.FREE,
            email="test@example.com",
        )
    
    app.dependency_overrides[auth.get_user_service] = get_user_service_override
    app.dependency_overrides[auth.get_jwt_strategy] = get_jwt_strategy_override
    app.dependency_overrides[auth.get_cookie_strategy] = get_cookie_strategy_override
    app.dependency_overrides[auth.get_api_key_service] = get_api_key_service_override
    app.dependency_overrides[get_current_user] = get_current_user_override
    
    return app


@pytest.fixture
def api_key_client(app_with_api_key_mocks):
    """Test client for API key endpoints."""
    return TestClient(app_with_api_key_mocks)


class TestCreateAPIKeyEndpoint:
    """Tests for POST /api/v1/auth/api-keys"""

    def test_create_api_key_success(self, api_key_client, mock_api_key_service):
        """Successfully create an API key."""
        response = api_key_client.post(
            "/api/v1/auth/api-keys",
            json={"name": "My API Key"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "key" in data["data"]
        assert data["data"]["key"].startswith("mav_")
        assert "key_prefix" in data["data"]
        mock_api_key_service.create_key.assert_called_once()

    def test_create_api_key_with_expiration(self, api_key_client, mock_api_key_service):
        """Create API key with expiration."""
        response = api_key_client.post(
            "/api/v1/auth/api-keys",
            json={"name": "Expiring Key", "expires_in_days": 30},
        )

        assert response.status_code == 200
        # Verify expires_in_days was passed to service
        call_args = mock_api_key_service.create_key.call_args
        assert call_args.kwargs.get("expires_in_days") == 30

    def test_create_api_key_missing_name(self, api_key_client):
        """Missing name returns 422."""
        response = api_key_client.post(
            "/api/v1/auth/api-keys",
            json={},
        )

        assert response.status_code == 422

    def test_create_api_key_empty_name(self, api_key_client):
        """Empty name returns 422."""
        response = api_key_client.post(
            "/api/v1/auth/api-keys",
            json={"name": ""},
        )

        assert response.status_code == 422

    def test_create_api_key_name_too_long(self, api_key_client):
        """Name over 100 chars returns 422."""
        response = api_key_client.post(
            "/api/v1/auth/api-keys",
            json={"name": "x" * 101},
        )

        assert response.status_code == 422

    def test_create_api_key_invalid_expiration(self, api_key_client):
        """Expiration over 365 days returns 422."""
        response = api_key_client.post(
            "/api/v1/auth/api-keys",
            json={"name": "Test Key", "expires_in_days": 400},
        )

        assert response.status_code == 422

    def test_create_api_key_negative_expiration(self, api_key_client):
        """Negative expiration returns 422."""
        response = api_key_client.post(
            "/api/v1/auth/api-keys",
            json={"name": "Test Key", "expires_in_days": -1},
        )

        assert response.status_code == 422


class TestListAPIKeysEndpoint:
    """Tests for GET /api/v1/auth/api-keys"""

    def test_list_api_keys_success(self, api_key_client, mock_api_key_service):
        """Successfully list API keys."""
        response = api_key_client.get("/api/v1/auth/api-keys")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2
        mock_api_key_service.list_keys.assert_called_once()

    def test_list_api_keys_empty(self, api_key_client, mock_api_key_service):
        """List returns empty array when no keys."""
        mock_api_key_service.list_keys.return_value = []

        response = api_key_client.get("/api/v1/auth/api-keys")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []

    def test_list_api_keys_excludes_full_key(self, api_key_client, mock_api_key_service):
        """Listed keys should not include full key value."""
        response = api_key_client.get("/api/v1/auth/api-keys")

        data = response.json()
        for key in data["data"]:
            # Full key should not be present, only prefix
            assert "key" not in key or not key.get("key", "").startswith("mav_")
            assert "key_prefix" in key


class TestRevokeAPIKeyEndpoint:
    """Tests for DELETE /api/v1/auth/api-keys/{key_id}"""

    def test_revoke_api_key_success(self, api_key_client, mock_api_key_service):
        """Successfully revoke an API key."""
        key_id = str(uuid4())

        response = api_key_client.delete(f"/api/v1/auth/api-keys/{key_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "revoked" in data["data"]["message"].lower()
        mock_api_key_service.revoke_key.assert_called_once()

    def test_revoke_api_key_not_found(self, api_key_client, mock_api_key_service):
        """Non-existent key returns 404."""
        from maverick_services.exceptions import NotFoundError

        mock_api_key_service.revoke_key.side_effect = NotFoundError("Key not found")

        response = api_key_client.delete(f"/api/v1/auth/api-keys/{uuid4()}")

        assert response.status_code == 404

    def test_revoke_api_key_wrong_user(self, api_key_client, mock_api_key_service):
        """Revoking another user's key returns 403."""
        from maverick_services.exceptions import AuthorizationError

        mock_api_key_service.revoke_key.side_effect = AuthorizationError(
            "Cannot revoke another user's key"
        )

        response = api_key_client.delete(f"/api/v1/auth/api-keys/{uuid4()}")

        assert response.status_code == 403

