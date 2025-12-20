"""
Audit logger factory.

Provides factory functions for creating and accessing audit loggers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from maverick_capabilities.audit.protocols import AuditLogger
from maverick_capabilities.audit.memory_logger import MemoryAuditLogger

if TYPE_CHECKING:
    from collections.abc import Callable, AsyncGenerator
    from sqlalchemy.ext.asyncio import AsyncSession


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """
    Get the global audit logger instance.

    Creates a default MemoryAuditLogger if none exists.

    Returns:
        The global audit logger instance
    """
    global _audit_logger

    if _audit_logger is None:
        _audit_logger = MemoryAuditLogger()

    return _audit_logger


def set_audit_logger(logger: AuditLogger) -> None:
    """
    Set the global audit logger instance.

    Args:
        logger: The audit logger to use
    """
    global _audit_logger
    _audit_logger = logger


def create_database_audit_logger(
    session_factory: Callable[[], "AsyncGenerator[AsyncSession, None]"],
) -> AuditLogger:
    """
    Create a database-backed audit logger.

    Args:
        session_factory: Async context manager that yields database sessions

    Returns:
        DatabaseAuditLogger instance
    """
    from maverick_capabilities.audit.db_logger import DatabaseAuditLogger

    return DatabaseAuditLogger(session_factory)


def reset_audit_logger() -> None:
    """Reset the global audit logger (for testing)."""
    global _audit_logger
    _audit_logger = None
