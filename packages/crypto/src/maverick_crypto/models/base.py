"""
Base model classes for maverick_crypto.

Provides standalone base classes that can work independently
or integrate with maverick_data if available.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase


class CryptoBase(DeclarativeBase):
    """
    Base class for all crypto models.
    
    Uses a separate metadata namespace to allow independent
    table creation without conflicting with maverick_data models.
    """
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

