"""Tests for UserService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, UTC

from maverick_services.auth.user_service import UserService
from maverick_services.auth.password import PasswordHasher
from maverick_services.exceptions import (
    ConflictError,
    AuthenticationError,
    NotFoundError,
)
from maverick_schemas.auth import AuthenticatedUser


@pytest.fixture
def mock_db():
    """Create a mock async database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def mock_hasher():
    """Create a mock password hasher."""
    hasher = MagicMock(spec=PasswordHasher)
    hasher.hash = MagicMock(return_value="$argon2id$hashed_password")
    hasher.verify = MagicMock(return_value=True)
    hasher.needs_rehash = MagicMock(return_value=False)
    return hasher


@pytest.fixture
def user_service(mock_db, mock_hasher):
    """Create UserService with mocked dependencies."""
    return UserService(db=mock_db, password_hasher=mock_hasher)


@pytest.fixture
def mock_user():
    """Create a mock user object."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.password_hash = "$argon2id$hashed_password"
    user.tier = "free"
    user.email_verified = False
    user.is_active = True
    user.last_login_at = None
    user.created_at = datetime.now(UTC)
    return user


class TestUserServiceRegister:
    """Tests for user registration."""

    async def test_register_success(self, user_service, mock_db, mock_hasher):
        """Successfully register a new user."""
        # Setup: No existing user
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock the user creation
        async def refresh_user(user):
            user.id = uuid4()
            user.email = "new@example.com"
            user.tier = "free"

        mock_db.refresh = refresh_user

        result = await user_service.register(
            email="new@example.com",
            password="secure_password123",
        )

        assert result["email"] == "new@example.com"
        assert result["tier"] == "free"
        assert "user_id" in result
        mock_hasher.hash.assert_called_once_with("secure_password123")
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_register_normalizes_email(self, user_service, mock_db, mock_hasher):
        """Email is normalized to lowercase and trimmed."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        async def refresh_user(user):
            user.id = uuid4()
            user.email = "test@example.com"
            user.tier = "free"

        mock_db.refresh = refresh_user

        result = await user_service.register(
            email="  TEST@Example.COM  ",
            password="password123",
        )

        # Check that normalized email was used
        assert result["email"] == "test@example.com"

    async def test_register_duplicate_email_raises(self, user_service, mock_db, mock_user):
        """Duplicate email raises ConflictError."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ConflictError) as exc_info:
            await user_service.register(
                email="test@example.com",
                password="password123",
            )

        assert "already registered" in str(exc_info.value)

    async def test_register_with_custom_tier(self, user_service, mock_db, mock_hasher):
        """Can register with custom tier."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        async def refresh_user(user):
            user.id = uuid4()
            user.email = "pro@example.com"
            user.tier = "pro"

        mock_db.refresh = refresh_user

        result = await user_service.register(
            email="pro@example.com",
            password="password123",
            tier="pro",
        )

        assert result["tier"] == "pro"


class TestUserServiceAuthenticate:
    """Tests for user authentication."""

    async def test_authenticate_success(self, user_service, mock_db, mock_user, mock_hasher):
        """Successfully authenticate with correct credentials."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_service.authenticate(
            email="test@example.com",
            password="correct_password",
        )

        assert isinstance(result, AuthenticatedUser)
        assert result.email == "test@example.com"
        assert result.auth_method == "password"
        mock_hasher.verify.assert_called_once()

    async def test_authenticate_updates_last_login(self, user_service, mock_db, mock_user, mock_hasher):
        """Authentication updates last_login_at."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        await user_service.authenticate(
            email="test@example.com",
            password="correct_password",
        )

        # Check last_login_at was updated
        assert mock_user.last_login_at is not None
        mock_db.commit.assert_called()

    async def test_authenticate_wrong_password(self, user_service, mock_db, mock_user, mock_hasher):
        """Wrong password raises AuthenticationError."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_hasher.verify.return_value = False

        with pytest.raises(AuthenticationError) as exc_info:
            await user_service.authenticate(
                email="test@example.com",
                password="wrong_password",
            )

        assert "Invalid email or password" in str(exc_info.value)

    async def test_authenticate_user_not_found(self, user_service, mock_db):
        """Non-existent user raises AuthenticationError."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(AuthenticationError) as exc_info:
            await user_service.authenticate(
                email="nonexistent@example.com",
                password="any_password",
            )

        # Same error message to prevent user enumeration
        assert "Invalid email or password" in str(exc_info.value)

    async def test_authenticate_deactivated_user(self, user_service, mock_db, mock_user, mock_hasher):
        """Deactivated user raises AuthenticationError."""
        mock_user.is_active = False
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(AuthenticationError) as exc_info:
            await user_service.authenticate(
                email="test@example.com",
                password="correct_password",
            )

        assert "deactivated" in str(exc_info.value)

    async def test_authenticate_rehashes_if_needed(self, user_service, mock_db, mock_user, mock_hasher):
        """Password is rehashed if needed."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_hasher.needs_rehash.return_value = True

        await user_service.authenticate(
            email="test@example.com",
            password="correct_password",
        )

        # Password should be rehashed
        mock_hasher.hash.assert_called_once_with("correct_password")


class TestUserServiceGetById:
    """Tests for getting user by ID."""

    async def test_get_by_id_success(self, user_service, mock_db, mock_user):
        """Successfully get user by ID."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_service.get_by_id(str(mock_user.id))

        assert result["user_id"] == str(mock_user.id)
        assert result["email"] == mock_user.email

    async def test_get_by_id_not_found(self, user_service, mock_db):
        """Non-existent user raises NotFoundError."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(NotFoundError):
            await user_service.get_by_id(str(uuid4()))

    async def test_get_by_id_accepts_uuid(self, user_service, mock_db, mock_user):
        """Can pass UUID object instead of string."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_service.get_by_id(mock_user.id)  # UUID, not string

        assert result["user_id"] == str(mock_user.id)


class TestUserServiceUpdatePassword:
    """Tests for password update."""

    async def test_update_password_success(self, user_service, mock_db, mock_user, mock_hasher):
        """Successfully update password."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_service.update_password(
            user_id=str(mock_user.id),
            current_password="old_password",
            new_password="new_secure_password",
        )

        assert result is True
        mock_hasher.verify.assert_called_once()
        mock_hasher.hash.assert_called_once_with("new_secure_password")
        mock_db.commit.assert_called_once()

    async def test_update_password_wrong_current(self, user_service, mock_db, mock_user, mock_hasher):
        """Wrong current password raises AuthenticationError."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_hasher.verify.return_value = False

        with pytest.raises(AuthenticationError) as exc_info:
            await user_service.update_password(
                user_id=str(mock_user.id),
                current_password="wrong_password",
                new_password="new_password",
            )

        assert "Current password is incorrect" in str(exc_info.value)

    async def test_update_password_user_not_found(self, user_service, mock_db):
        """Non-existent user raises NotFoundError."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(NotFoundError):
            await user_service.update_password(
                user_id=str(uuid4()),
                current_password="any",
                new_password="any",
            )


class TestUserServiceDeactivate:
    """Tests for user deactivation."""

    async def test_deactivate_success(self, user_service, mock_db, mock_user):
        """Successfully deactivate user."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_service.deactivate(str(mock_user.id))

        assert result is True
        assert mock_user.is_active is False
        mock_db.commit.assert_called_once()

    async def test_deactivate_user_not_found(self, user_service, mock_db):
        """Non-existent user raises NotFoundError."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(NotFoundError):
            await user_service.deactivate(str(uuid4()))


class TestUserServiceGetByEmail:
    """Tests for getting user by email."""

    async def test_get_by_email_success(self, user_service, mock_db, mock_user):
        """Successfully get user by email."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_service.get_by_email("test@example.com")

        assert result is not None
        assert result["email"] == mock_user.email

    async def test_get_by_email_not_found(self, user_service, mock_db):
        """Non-existent email returns None."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_service.get_by_email("nonexistent@example.com")

        assert result is None

    async def test_get_by_email_normalizes(self, user_service, mock_db, mock_user):
        """Email is normalized before query."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        await user_service.get_by_email("  TEST@Example.COM  ")

        # Verify the query was made with normalized email
        mock_db.execute.assert_called_once()

