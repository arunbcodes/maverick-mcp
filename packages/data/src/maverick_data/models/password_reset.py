"""
Password reset token model.

Stores time-limited tokens for password reset flow.
Tokens are hashed for security - only the hash is stored.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, relationship

from maverick_data.models.base import Base


class PasswordResetToken(Base):
    """
    Password reset token for secure password recovery.

    Tokens are single-use and expire after a configurable period.
    Only the hash of the token is stored - the actual token is sent
    to the user and never stored in plain text.

    Attributes:
        id: Unique token identifier (UUID)
        user_id: Reference to the user requesting reset
        token_hash: SHA-256 hash of the reset token
        expires_at: When the token expires (typically 1 hour)
        used_at: When the token was used (null if unused)
        created_at: When the token was created
    """

    __tablename__ = "password_reset_tokens"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")

    # Indexes
    __table_args__ = (
        Index("idx_password_reset_token_user", "user_id"),
        Index("idx_password_reset_token_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_used(self) -> bool:
        """Check if token has been used."""
        return self.used_at is not None

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        return not self.is_expired and not self.is_used


# Import here to avoid circular imports
from maverick_data.models.user import User  # noqa: E402, F401

