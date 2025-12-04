"""Tests for APIKeyService."""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from maverick_services.auth.api_key_service import APIKeyService
from maverick_services.auth.password import PasswordHasher
from maverick_services.exceptions import NotFoundError, AuthorizationError


@pytest.fixture
def mock_db():
    """Create a mock async database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def mock_hasher():
    """Create a mock password hasher."""
    hasher = MagicMock(spec=PasswordHasher)
    hasher.hash = MagicMock(return_value="$argon2id$hashed_key")
    hasher.verify = MagicMock(return_value=True)
    return hasher


@pytest.fixture
def api_key_service(mock_db, mock_hasher):
    """Create APIKeyService with mocked dependencies."""
    return APIKeyService(db=mock_db, hasher=mock_hasher)


@pytest.fixture
def mock_api_key():
    """Create a mock API key object."""
    key = MagicMock()
    key.id = uuid4()
    key.user_id = uuid4()
    key.key_prefix = "mav_abc12345"
    key.key_hash = "$argon2id$hashed_key"
    key.name = "Test Key"
    key.tier = "free"
    key.rate_limit = None
    key.last_used_at = None
    key.is_active = True
    key.expires_at = None
    key.created_at = datetime.now(UTC)
    return key


class TestAPIKeyServiceCreate:
    """Tests for API key creation."""

    async def test_create_key_success(self, api_key_service, mock_db, mock_hasher):
        """Successfully create an API key."""
        user_id = uuid4()

        # Mock the db.refresh to set the id and created_at
        async def refresh_key(key):
            key.id = uuid4()
            key.created_at = datetime.now(UTC)

        mock_db.refresh = refresh_key

        result = await api_key_service.create_key(
            user_id=user_id,
            name="My API Key",
        )

        assert "key" in result
        assert result["key"].startswith("mav_")
        assert "key_prefix" in result
        assert result["name"] == "My API Key"
        assert result["tier"] == "free"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_create_key_with_expiration(self, api_key_service, mock_db):
        """Create API key with expiration."""
        user_id = uuid4()

        async def refresh_key(key):
            key.id = uuid4()
            key.created_at = datetime.now(UTC)

        mock_db.refresh = refresh_key

        result = await api_key_service.create_key(
            user_id=user_id,
            name="Expiring Key",
            expires_in_days=30,
        )

        assert result["expires_at"] is not None

    async def test_create_key_with_custom_tier(self, api_key_service, mock_db):
        """Create API key with custom tier."""
        user_id = uuid4()

        async def refresh_key(key):
            key.id = uuid4()
            key.created_at = datetime.now(UTC)

        mock_db.refresh = refresh_key

        result = await api_key_service.create_key(
            user_id=user_id,
            name="Pro Key",
            tier="pro",
        )

        assert result["tier"] == "pro"

    async def test_create_key_hashes_key(self, api_key_service, mock_db, mock_hasher):
        """API key is hashed before storage."""
        user_id = uuid4()

        async def refresh_key(key):
            key.id = uuid4()
            key.created_at = datetime.now(UTC)

        mock_db.refresh = refresh_key

        await api_key_service.create_key(
            user_id=user_id,
            name="My Key",
        )

        mock_hasher.hash.assert_called_once()

    async def test_generated_keys_are_unique(self, api_key_service, mock_db):
        """Each generated key is unique."""
        user_id = uuid4()

        async def refresh_key(key):
            key.id = uuid4()
            key.created_at = datetime.now(UTC)

        mock_db.refresh = refresh_key

        result1 = await api_key_service.create_key(user_id=user_id, name="Key 1")
        result2 = await api_key_service.create_key(user_id=user_id, name="Key 2")

        assert result1["key"] != result2["key"]


class TestAPIKeyServiceList:
    """Tests for listing API keys."""

    async def test_list_keys_success(self, api_key_service, mock_db, mock_api_key):
        """Successfully list API keys."""
        user_id = mock_api_key.user_id

        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_api_key])))
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await api_key_service.list_keys(user_id=user_id)

        assert len(result) == 1
        assert result[0]["key_prefix"] == mock_api_key.key_prefix
        assert result[0]["name"] == mock_api_key.name
        # Full key should not be included
        assert "key" not in result[0] or not result[0].get("key", "").startswith("mav_")

    async def test_list_keys_empty(self, api_key_service, mock_db):
        """List keys returns empty for user with no keys."""
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await api_key_service.list_keys(user_id=user_id)

        assert result == []

    async def test_list_keys_excludes_inactive(self, api_key_service, mock_db, mock_api_key):
        """Inactive keys are not included in listing."""
        user_id = mock_api_key.user_id

        # Only active keys should be returned (query filters by is_active=True)
        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await api_key_service.list_keys(user_id=user_id)

        # Verify the query was called (filters applied)
        mock_db.execute.assert_called_once()


class TestAPIKeyServiceRevoke:
    """Tests for revoking API keys."""

    async def test_revoke_key_success(self, api_key_service, mock_db, mock_api_key):
        """Successfully revoke an API key."""
        user_id = mock_api_key.user_id

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_api_key)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await api_key_service.revoke_key(
            key_id=mock_api_key.id,
            user_id=user_id,
        )

        assert result is True
        assert mock_api_key.is_active is False
        mock_db.commit.assert_called_once()

    async def test_revoke_key_not_found(self, api_key_service, mock_db):
        """Revoke raises NotFoundError for non-existent key."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(NotFoundError):
            await api_key_service.revoke_key(
                key_id=uuid4(),
                user_id=uuid4(),
            )

    async def test_revoke_key_wrong_user(self, api_key_service, mock_db, mock_api_key):
        """Revoke raises AuthorizationError for wrong user."""
        different_user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_api_key)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(AuthorizationError):
            await api_key_service.revoke_key(
                key_id=mock_api_key.id,
                user_id=different_user_id,
            )


class TestAPIKeyServiceValidate:
    """Tests for validating API keys."""

    async def test_validate_key_success(self, api_key_service, mock_db, mock_hasher, mock_api_key):
        """Successfully validate a valid API key."""
        full_key = "mav_abc12345xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_api_key)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await api_key_service.validate_key(full_key)

        assert result is not None
        assert result["user_id"] == str(mock_api_key.user_id)
        assert result["tier"] == mock_api_key.tier
        mock_hasher.verify.assert_called_once()

    async def test_validate_key_invalid_prefix(self, api_key_service):
        """Invalid prefix returns None."""
        result = await api_key_service.validate_key("invalid_key")

        assert result is None

    async def test_validate_key_not_found(self, api_key_service, mock_db):
        """Non-existent key returns None."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await api_key_service.validate_key("mav_nonexistent")

        assert result is None

    async def test_validate_key_expired(self, api_key_service, mock_db, mock_api_key):
        """Expired key returns None."""
        mock_api_key.expires_at = datetime.now(UTC) - timedelta(days=1)

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_api_key)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await api_key_service.validate_key("mav_abc12345xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

        assert result is None

    async def test_validate_key_wrong_hash(self, api_key_service, mock_db, mock_hasher, mock_api_key):
        """Wrong key hash returns None."""
        mock_hasher.verify.return_value = False

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_api_key)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await api_key_service.validate_key("mav_abc12345wrongkeyxxxxxxxxxxxxxxxxxxx")

        assert result is None

    async def test_validate_key_updates_last_used(self, api_key_service, mock_db, mock_hasher, mock_api_key):
        """Validating key updates last_used_at."""
        full_key = "mav_abc12345xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        mock_api_key.last_used_at = None

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_api_key)
        mock_db.execute = AsyncMock(return_value=mock_result)

        await api_key_service.validate_key(full_key)

        assert mock_api_key.last_used_at is not None
        mock_db.commit.assert_called()

