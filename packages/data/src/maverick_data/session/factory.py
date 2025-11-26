"""
Database Session Factory.

Provides configurable session factories for sync and async database access.
This module uses environment variables for configuration and supports
both SQLite (default) and PostgreSQL.
"""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import AsyncGenerator, Generator
from typing import Any

from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from maverick_data.models.base import Base

logger = logging.getLogger("maverick_data.session")


def _get_database_url() -> str:
    """Get database URL from environment, defaulting to SQLite."""
    if os.getenv("GITHUB_ACTIONS") == "true" or os.getenv("CI") == "true":
        return "sqlite:///:memory:"
    return (
        os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or "sqlite:///maverick_mcp.db"
    )


def _get_db_config() -> dict[str, Any]:
    """Get database configuration from environment."""
    return {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
        "pool_timeout": float(os.getenv("DB_POOL_TIMEOUT", "30")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
        "pool_pre_ping": os.getenv("DB_POOL_PRE_PING", "true").lower() == "true",
        "echo": os.getenv("DB_ECHO", "false").lower() == "true",
        "use_pooling": os.getenv("DB_USE_POOLING", "true").lower() == "true",
        "statement_timeout": int(os.getenv("DB_STATEMENT_TIMEOUT", "30000")),
    }


DATABASE_URL = _get_database_url()
_db_config = _get_db_config()


def _get_connect_args(url: str) -> dict[str, Any]:
    """Get database-specific connection arguments."""
    if "postgresql" in url:
        return {
            "connect_timeout": 10,
            "application_name": "maverick_data",
            "options": f"-c statement_timeout={_db_config['statement_timeout']}",
        }
    elif "sqlite" in url:
        return {"check_same_thread": False}
    return {}


def _create_sync_engine():
    """Create the synchronous database engine."""
    connect_args = _get_connect_args(DATABASE_URL)

    if _db_config["use_pooling"] and "sqlite" not in DATABASE_URL:
        return create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=_db_config["pool_size"],
            max_overflow=_db_config["max_overflow"],
            pool_timeout=_db_config["pool_timeout"],
            pool_recycle=_db_config["pool_recycle"],
            pool_pre_ping=_db_config["pool_pre_ping"],
            echo=_db_config["echo"],
            connect_args=connect_args,
        )
    else:
        return create_engine(
            DATABASE_URL,
            poolclass=NullPool,
            echo=_db_config["echo"],
            connect_args=connect_args,
        )


engine = _create_sync_engine()
_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_schema_lock = threading.Lock()
_schema_initialized = False


def ensure_database_schema(force: bool = False) -> bool:
    """Ensure the database schema exists for the configured engine.

    Args:
        force: When True, the schema will be (re)created even if it appears
            to exist already.

    Returns:
        True if the schema creation routine executed, False otherwise.
    """
    global _schema_initialized

    if not force and _schema_initialized:
        return False

    with _schema_lock:
        if not force and _schema_initialized:
            return False

        try:
            inspector = inspect(engine)
            existing_tables = set(inspector.get_table_names())
        except SQLAlchemyError as exc:
            logger.warning(
                "Unable to inspect database schema; attempting to create tables anyway",
                exc_info=exc,
            )
            existing_tables = set()

        defined_tables = set(Base.metadata.tables.keys())
        missing_tables = defined_tables - existing_tables

        should_create = force or bool(missing_tables)
        if should_create:
            if missing_tables:
                logger.info(
                    "Creating missing database tables: %s",
                    ", ".join(sorted(missing_tables)),
                )
            else:
                logger.info("Ensuring database schema is up to date")

            Base.metadata.create_all(bind=engine)
            _schema_initialized = True
            return True

        _schema_initialized = True
        return False


class _SessionFactoryWrapper:
    """Session factory that ensures the schema exists before creating sessions."""

    def __init__(self, factory: sessionmaker):
        self._factory = factory

    def __call__(self, *args, **kwargs):
        ensure_database_schema()
        return self._factory(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._factory, name)


SessionLocal = _SessionFactoryWrapper(_session_factory)


# Async engine management
_async_engine = None
_async_session_factory = None


def _get_async_database_url() -> str:
    """Convert sync URL to async URL."""
    if DATABASE_URL.startswith("sqlite://"):
        return DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
    return DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")


def _get_async_connect_args(url: str) -> dict[str, Any]:
    """Get async database-specific connection arguments."""
    if "postgresql" in url:
        return {
            "server_settings": {
                "application_name": "maverick_data_async",
                "statement_timeout": str(_db_config["statement_timeout"]),
            }
        }
    elif "sqlite" in url:
        return {"check_same_thread": False}
    return {}


def _get_async_engine():
    """Get or create the async engine singleton."""
    global _async_engine
    if _async_engine is None:
        async_url = _get_async_database_url()
        connect_args = _get_async_connect_args(async_url)

        if _db_config["use_pooling"] and "sqlite" not in async_url:
            _async_engine = create_async_engine(
                async_url,
                pool_size=_db_config["pool_size"],
                max_overflow=_db_config["max_overflow"],
                pool_timeout=_db_config["pool_timeout"],
                pool_recycle=_db_config["pool_recycle"],
                pool_pre_ping=_db_config["pool_pre_ping"],
                echo=_db_config["echo"],
                connect_args=connect_args,
            )
        else:
            _async_engine = create_async_engine(
                async_url,
                poolclass=NullPool,
                echo=_db_config["echo"],
                connect_args=connect_args,
            )
        logger.info("Created async database engine")
    return _async_engine


def _get_async_session_factory():
    """Get or create the async session factory singleton."""
    global _async_session_factory
    if _async_session_factory is None:
        async_engine = _get_async_engine()
        _async_session_factory = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("Created async session factory")
    return _async_session_factory


def get_db() -> Generator[Session, None, None]:
    """Get database session (generator for FastAPI dependency injection)."""
    ensure_database_schema()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session() -> Session:
    """Get database session (direct session for manual management)."""
    ensure_database_schema()
    return SessionLocal()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session using the cached engine."""
    async_session_factory = _get_async_session_factory()

    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_async_db_connections():
    """Close the async database engine and cleanup connections."""
    global _async_engine, _async_session_factory
    if _async_engine:
        await _async_engine.dispose()
        _async_engine = None
        _async_session_factory = None
        logger.info("Closed async database engine")


def init_db():
    """Initialize database by creating all tables."""
    ensure_database_schema(force=True)
