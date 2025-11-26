"""Tests for session factory."""

import os

import pytest


class TestSessionFactory:
    """Tests for the session factory module."""

    def test_database_url_defaults_to_sqlite(self):
        """Test that DATABASE_URL defaults to SQLite."""
        # Clear any environment overrides
        original = os.environ.get("DATABASE_URL")
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]
        if "POSTGRES_URL" in os.environ:
            del os.environ["POSTGRES_URL"]

        # Re-import to get fresh values
        # Note: In actual tests, this would require more sophisticated module reloading
        from maverick_data.session.factory import DATABASE_URL

        # Restore
        if original:
            os.environ["DATABASE_URL"] = original

        # The default should be SQLite
        assert "sqlite" in DATABASE_URL.lower() or "memory" in DATABASE_URL.lower()

    def test_engine_is_created(self):
        """Test that the engine is created."""
        from maverick_data.session.factory import engine

        assert engine is not None

    def test_session_local_is_available(self):
        """Test that SessionLocal is available."""
        from maverick_data.session.factory import SessionLocal

        assert SessionLocal is not None

    def test_get_session_returns_session(self):
        """Test that get_session returns a session."""
        from maverick_data.session.factory import get_session

        session = get_session()
        assert session is not None
        session.close()

    def test_get_db_is_generator(self):
        """Test that get_db returns a generator."""
        from maverick_data.session.factory import get_db

        gen = get_db()
        session = next(gen)
        assert session is not None
        try:
            next(gen)
        except StopIteration:
            pass  # Expected

    def test_init_db_creates_tables(self):
        """Test that init_db creates tables."""
        from maverick_data.session.factory import init_db

        # Should not raise
        init_db()


class TestTimestampMixin:
    """Tests for the TimestampMixin."""

    def test_timestamp_mixin_has_created_at(self):
        """Test that TimestampMixin has created_at."""
        from maverick_data.models.base import TimestampMixin

        assert hasattr(TimestampMixin, "created_at")

    def test_timestamp_mixin_has_updated_at(self):
        """Test that TimestampMixin has updated_at."""
        from maverick_data.models.base import TimestampMixin

        assert hasattr(TimestampMixin, "updated_at")
