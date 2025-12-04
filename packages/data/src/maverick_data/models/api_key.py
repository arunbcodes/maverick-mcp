"""
API Key model for programmatic access.

Stores only the key hash for security. The full key is only shown once
at creation time and cannot be retrieved later.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, relationship

from maverick_data.models.base import Base, TimestampMixin


def generate_key_prefix() -> str:
    """Generate a random key prefix for identification."""
    return f"mav_{secrets.token_urlsafe(8)}"


class APIKey(TimestampMixin, Base):
    """
    API key for programmatic access.

    Security: Only the hash of the key is stored. The full key is returned
    once at creation and cannot be retrieved again.

    Attributes:
        id: Unique key identifier (UUID)
        user_id: Owner of this API key
        key_prefix: First 12 characters of key (for identification)
        key_hash: Argon2 hash of the full key
        name: User-friendly name for this key
        tier: Rate limit tier for this key
        rate_limit: Custom rate limit (requests per minute), null = use tier default
        last_used_at: Timestamp of last use
        expires_at: Expiration timestamp (null = never expires)
        is_active: Whether key is active (can be revoked)
    """

    __tablename__ = "api_keys"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Key identification and security
    key_prefix = Column(String(20), nullable=False, unique=True, index=True)
    key_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)

    # Rate limiting
    tier = Column(String(20), nullable=False, default="free")
    rate_limit = Column(Integer, nullable=True)  # Custom rate limit override

    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    request_count = Column(Integer, nullable=False, default=0)

    # Lifecycle
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")

    # Indexes
    __table_args__ = (
        Index("idx_api_key_user", "user_id"),
        Index("idx_api_key_prefix", "key_prefix"),
        Index("idx_api_key_active", "is_active"),
        Index("idx_api_key_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}')>"

    @property
    def is_expired(self) -> bool:
        """Check if key has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(self.expires_at.tzinfo) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if key is valid (active and not expired)."""
        return self.is_active and not self.is_expired

    def record_usage(self) -> None:
        """Update last_used_at and increment request count."""
        from datetime import UTC

        self.last_used_at = datetime.now(UTC)
        self.request_count += 1


# Import here to avoid circular imports
from maverick_data.models.user import User  # noqa: E402

