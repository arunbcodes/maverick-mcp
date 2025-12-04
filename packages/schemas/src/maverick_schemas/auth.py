"""
Authentication and authorization models.

Models for users, tokens, and authentication.
"""

from datetime import datetime

from pydantic import Field, EmailStr

from maverick_schemas.base import AuthMethod, MaverickBaseModel, Tier


class AuthenticatedUser(MaverickBaseModel):
    """Authenticated user context."""
    
    user_id: str = Field(description="Unique user identifier")
    auth_method: AuthMethod | str = Field(description="Authentication method used")
    tier: Tier | str = Field(default=Tier.FREE, description="Subscription tier")
    
    # Rate limiting
    rate_limit: int = Field(default=100, description="Requests per minute allowed")
    
    # Optional user info
    email: str | None = Field(default=None, description="User email")
    username: str | None = Field(default=None, description="Username")
    
    # Session info
    session_id: str | None = Field(default=None, description="Session ID (for cookie auth)")
    token_id: str | None = Field(default=None, description="Token ID (for JWT auth)")


class RegisterRequest(MaverickBaseModel):
    """User registration request."""
    
    email: EmailStr = Field(description="User email")
    password: str = Field(min_length=8, max_length=128, description="User password")
    
    # Optional
    name: str | None = Field(default=None, max_length=100, description="Display name")


class LoginRequest(MaverickBaseModel):
    """Login request model."""
    
    email: EmailStr = Field(description="User email")
    password: str = Field(min_length=8, description="User password")
    
    # MFA (optional)
    mfa_code: str | None = Field(default=None, description="MFA code if enabled")


class TokenResponse(MaverickBaseModel):
    """JWT token response."""
    
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Access token expiry in seconds")
    
    # User info
    user_id: str = Field(description="User ID")
    tier: Tier = Field(description="Subscription tier")


class RefreshTokenRequest(MaverickBaseModel):
    """Refresh token request."""
    
    refresh_token: str = Field(description="Refresh token")


class APIKeyInfo(MaverickBaseModel):
    """API key information."""
    
    key_id: str = Field(description="API key ID (prefix)")
    name: str = Field(description="API key name")
    tier: Tier = Field(description="Tier associated with key")
    
    # Usage
    rate_limit: int = Field(description="Rate limit per minute")
    requests_today: int = Field(default=0, description="Requests made today")
    last_used: datetime | None = Field(default=None, description="Last used timestamp")
    
    # Metadata
    created_at: datetime = Field(description="Creation timestamp")
    expires_at: datetime | None = Field(default=None, description="Expiration date")


class APIKeyCreate(MaverickBaseModel):
    """Request to create an API key."""
    
    name: str = Field(min_length=1, max_length=100, description="API key name")
    expires_in_days: int | None = Field(
        default=None,
        ge=1,
        le=365,
        description="Days until expiration"
    )


class APIKeyResponse(MaverickBaseModel):
    """Response after creating an API key."""
    
    key: str = Field(description="Full API key (only shown once)")
    key_id: str = Field(description="Key ID for reference")
    name: str = Field(description="Key name")
    created_at: datetime = Field(description="Creation timestamp")
    
    # Warning
    message: str = Field(
        default="Store this key securely. It will not be shown again.",
        description="Important message"
    )


class TokenBudget(MaverickBaseModel):
    """LLM token budget status."""
    
    tier: Tier = Field(description="User tier")
    
    # Daily budget
    daily_limit: int = Field(description="Daily token limit")
    daily_used: int = Field(description="Tokens used today")
    daily_remaining: int = Field(description="Tokens remaining today")
    
    # Monthly budget
    monthly_limit: int = Field(description="Monthly token limit")
    monthly_used: int = Field(description="Tokens used this month")
    monthly_remaining: int = Field(description="Tokens remaining this month")
    
    # Reset times
    daily_reset_at: datetime = Field(description="Daily reset timestamp")
    monthly_reset_at: datetime = Field(description="Monthly reset timestamp")


class UserProfile(MaverickBaseModel):
    """User profile response."""
    
    user_id: str = Field(description="User ID")
    email: str = Field(description="User email")
    tier: Tier | str = Field(description="Subscription tier")
    email_verified: bool = Field(default=False, description="Email verification status")
    created_at: str = Field(description="Account creation timestamp")
    last_login_at: str | None = Field(default=None, description="Last login timestamp")


__all__ = [
    "AuthenticatedUser",
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "UserProfile",
    "APIKeyInfo",
    "APIKeyCreate",
    "APIKeyResponse",
    "TokenBudget",
]

