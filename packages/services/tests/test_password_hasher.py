"""Tests for PasswordHasher."""

import pytest

from maverick_services.auth.password import PasswordHasher, password_hasher


class TestPasswordHasher:
    """Tests for PasswordHasher class."""

    @pytest.fixture
    def hasher(self):
        """Create a PasswordHasher instance with default settings."""
        return PasswordHasher()

    def test_hash_returns_argon2_hash(self, hasher):
        """Hash returns an Argon2 formatted string."""
        password = "my_secure_password123"
        hashed = hasher.hash(password)

        assert hashed.startswith("$argon2id$")
        assert len(hashed) > 50

    def test_hash_is_unique_per_call(self, hasher):
        """Same password produces different hashes (due to salt)."""
        password = "my_secure_password123"

        hash1 = hasher.hash(password)
        hash2 = hasher.hash(password)

        assert hash1 != hash2  # Different salts

    def test_verify_correct_password(self, hasher):
        """Verify returns True for correct password."""
        password = "my_secure_password123"
        hashed = hasher.hash(password)

        assert hasher.verify(password, hashed) is True

    def test_verify_wrong_password(self, hasher):
        """Verify returns False for wrong password."""
        password = "my_secure_password123"
        wrong_password = "wrong_password456"
        hashed = hasher.hash(password)

        assert hasher.verify(wrong_password, hashed) is False

    def test_verify_empty_password(self, hasher):
        """Verify handles empty password gracefully."""
        hashed = hasher.hash("original_password")

        assert hasher.verify("", hashed) is False

    def test_verify_invalid_hash(self, hasher):
        """Verify returns False for invalid hash format."""
        result = hasher.verify("any_password", "invalid_hash_format")

        assert result is False

    def test_verify_corrupted_hash(self, hasher):
        """Verify returns False for corrupted hash."""
        password = "my_password"
        hashed = hasher.hash(password)
        corrupted = hashed[:-10] + "xxxxxxxxxx"  # Corrupt the hash

        assert hasher.verify(password, corrupted) is False

    def test_needs_rehash_fresh_hash(self, hasher):
        """Fresh hash doesn't need rehashing."""
        hashed = hasher.hash("password123")

        assert hasher.needs_rehash(hashed) is False

    def test_needs_rehash_with_different_params(self):
        """Hash with different params may need rehashing."""
        # Create hasher with minimal params
        weak_hasher = PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)
        hashed = weak_hasher.hash("password123")

        # Strong hasher should indicate rehash needed
        strong_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)

        # The hash was created with different params
        assert strong_hasher.needs_rehash(hashed) is True

    def test_hash_with_unicode_password(self, hasher):
        """Hash handles unicode passwords correctly."""
        password = "密码🔐émoji"
        hashed = hasher.hash(password)

        assert hasher.verify(password, hashed) is True
        assert hasher.verify("different_password", hashed) is False

    def test_hash_with_very_long_password(self, hasher):
        """Hash handles very long passwords."""
        password = "x" * 1000  # 1000 character password
        hashed = hasher.hash(password)

        assert hasher.verify(password, hashed) is True
        assert hasher.verify(password + "y", hashed) is False

    def test_hash_with_special_characters(self, hasher):
        """Hash handles special characters correctly."""
        password = "p@$$w0rd!#$%^&*()_+-=[]{}|;':\",./<>?"
        hashed = hasher.hash(password)

        assert hasher.verify(password, hashed) is True


class TestPasswordHasherSingleton:
    """Tests for the singleton password_hasher instance."""

    def test_singleton_exists(self):
        """Module-level singleton is available."""
        assert password_hasher is not None
        assert isinstance(password_hasher, PasswordHasher)

    def test_singleton_works(self):
        """Singleton can hash and verify passwords."""
        password = "test_singleton_password"
        hashed = password_hasher.hash(password)

        assert password_hasher.verify(password, hashed) is True


class TestPasswordHasherConfiguration:
    """Tests for PasswordHasher configuration."""

    def test_custom_time_cost(self):
        """Can create hasher with custom time cost."""
        hasher = PasswordHasher(time_cost=2)
        hashed = hasher.hash("password")

        assert hasher.verify("password", hashed) is True

    def test_custom_memory_cost(self):
        """Can create hasher with custom memory cost."""
        hasher = PasswordHasher(memory_cost=32768)  # 32 MB
        hashed = hasher.hash("password")

        assert hasher.verify("password", hashed) is True

    def test_custom_parallelism(self):
        """Can create hasher with custom parallelism."""
        hasher = PasswordHasher(parallelism=2)
        hashed = hasher.hash("password")

        assert hasher.verify("password", hashed) is True

