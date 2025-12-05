"""
User model for authentication and authorization.

Supports multi-tier access (free, pro, enterprise) and tracks
login activity for security auditing.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Index, String, Uuid
from sqlalchemy.orm import Mapped, relationship

from maverick_data.models.base import Base, TimestampMixin


class UserTier(str, Enum):
    """User subscription tiers with different rate limits and features."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(TimestampMixin, Base):
    """
    User account for authentication.

    Supports email/password authentication with secure password hashing.
    Tracks login activity for security auditing.

    Attributes:
        id: Unique user identifier (UUID)
        email: User email address (unique, indexed)
        password_hash: Argon2 hash of user password
        name: Optional display name
        tier: Subscription tier (free, pro, enterprise)
        email_verified: Whether email has been verified
        is_active: Whether account is active (soft delete)
        is_demo_user: Whether this is the demo account
        is_admin: Whether user has admin privileges
        onboarding_completed: Whether user completed onboarding
        last_login_at: Timestamp of last successful login
    """

    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)

    # Account status
    tier = Column(String(20), nullable=False, default=UserTier.FREE.value)
    email_verified = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_demo_user = Column(Boolean, nullable=False, default=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    onboarding_completed = Column(Boolean, nullable=False, default=False)

    # Security audit
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    portfolios: Mapped[list["UserPortfolio"]] = relationship(
        "UserPortfolio",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys="UserPortfolio.owner_id",
    )

    # Indexes
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_active", "is_active"),
        Index("idx_user_tier", "tier"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', tier='{self.tier}')>"

    @property
    def is_verified(self) -> bool:
        """Check if user email is verified."""
        return self.email_verified

    @property
    def tier_enum(self) -> UserTier:
        """Get tier as enum."""
        return UserTier(self.tier)


# Import here to avoid circular imports
from maverick_data.models.api_key import APIKey  # noqa: E402
from maverick_data.models.portfolio import UserPortfolio  # noqa: E402

