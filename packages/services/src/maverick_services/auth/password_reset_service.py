"""
Password reset service.

Handles password reset token generation, validation, and password updates.
"""

import secrets
import hashlib
import logging
from datetime import datetime, timedelta, UTC
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from maverick_services.auth.password import password_hasher
from maverick_services.exceptions import (
    NotFoundError,
    ValidationError,
    ServiceException,
)

logger = logging.getLogger(__name__)

# Token settings
TOKEN_LENGTH = 32  # 256 bits
TOKEN_EXPIRY_HOURS = 1


def generate_reset_token() -> str:
    """Generate a cryptographically secure reset token."""
    return secrets.token_urlsafe(TOKEN_LENGTH)


def hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


class PasswordResetService:
    """
    Service for password reset operations.
    
    Handles:
    - Token generation and storage
    - Token validation
    - Password reset execution
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the password reset service.
        
        Args:
            db: Async database session
        """
        self._db = db
    
    async def request_reset(self, email: str) -> dict:
        """
        Request a password reset for a user.
        
        Creates a reset token and returns it. In production, this would
        be sent via email. For now, we return it (or log it) for dev.
        
        Args:
            email: User email address
            
        Returns:
            Dict with reset_token (in dev) and message
            
        Note:
            Always returns success message to prevent user enumeration.
        """
        from maverick_data.models import User, PasswordResetToken
        
        email = email.lower().strip()
        
        # Find user
        result = await self._db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        # Always return success to prevent user enumeration
        if not user or not user.is_active:
            logger.info(f"Password reset requested for non-existent/inactive email: {email}")
            return {
                "message": "If an account exists with this email, a reset link has been sent.",
            }
        
        # Generate token
        token = generate_reset_token()
        token_hash = hash_token(token)
        expires_at = datetime.now(UTC) + timedelta(hours=TOKEN_EXPIRY_HOURS)
        
        # Invalidate any existing tokens for this user
        await self._db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == user.id)
            .where(PasswordResetToken.used_at.is_(None))
        )
        
        # Create new token
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        
        self._db.add(reset_token)
        
        try:
            await self._db.commit()
            
            logger.info(f"Password reset token created for user {email}")
            
            # In production, send email here
            # For dev, we return the token
            return {
                "message": "If an account exists with this email, a reset link has been sent.",
                # Dev only - remove in production
                "_dev_token": token,
                "_dev_expires_at": expires_at.isoformat(),
            }
        except Exception as e:
            await self._db.rollback()
            logger.error(f"Failed to create reset token for {email}: {e}")
            raise ServiceException(f"Failed to request password reset: {e}")
    
    async def validate_token(self, token: str) -> dict:
        """
        Validate a password reset token.
        
        Args:
            token: The reset token to validate
            
        Returns:
            Dict with is_valid and user_email
            
        Raises:
            ValidationError: If token is invalid or expired
        """
        from maverick_data.models import PasswordResetToken
        
        token_hash = hash_token(token)
        
        result = await self._db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hash)
        )
        reset_token = result.scalar_one_or_none()
        
        if not reset_token:
            raise ValidationError("Invalid reset token")
        
        if reset_token.is_used:
            raise ValidationError("Reset token has already been used")
        
        if reset_token.is_expired:
            raise ValidationError("Reset token has expired")
        
        return {
            "is_valid": True,
            "user_email": reset_token.user.email,
        }
    
    async def reset_password(self, token: str, new_password: str) -> dict:
        """
        Reset password using a valid token.
        
        Args:
            token: The reset token
            new_password: The new password to set
            
        Returns:
            Dict with success message
            
        Raises:
            ValidationError: If token is invalid or expired
            ServiceException: On database error
        """
        from maverick_data.models import User, PasswordResetToken
        
        token_hash = hash_token(token)
        
        result = await self._db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hash)
        )
        reset_token = result.scalar_one_or_none()
        
        if not reset_token:
            raise ValidationError("Invalid reset token")
        
        if reset_token.is_used:
            raise ValidationError("Reset token has already been used")
        
        if reset_token.is_expired:
            raise ValidationError("Reset token has expired")
        
        # Get user
        user_result = await self._db.execute(
            select(User).where(User.id == reset_token.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User not found")
        
        # Update password
        user.password_hash = password_hasher.hash(new_password)
        user.updated_at = datetime.now(UTC)
        
        # Mark token as used
        reset_token.used_at = datetime.now(UTC)
        
        try:
            await self._db.commit()
            
            logger.info(f"Password reset completed for user {user.email}")
            
            return {
                "message": "Password has been reset successfully. You can now log in with your new password.",
            }
        except Exception as e:
            await self._db.rollback()
            logger.error(f"Failed to reset password: {e}")
            raise ServiceException(f"Failed to reset password: {e}")
    
    async def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired tokens from the database.
        
        Returns:
            Number of tokens deleted
        """
        from maverick_data.models import PasswordResetToken
        
        # Delete tokens that are expired or used (older than 24 hours)
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        
        result = await self._db.execute(
            select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.created_at < cutoff,
                    PasswordResetToken.used_at.isnot(None),
                )
            )
        )
        tokens = result.scalars().all()
        
        count = 0
        for token in tokens:
            await self._db.delete(token)
            count += 1
        
        if count > 0:
            await self._db.commit()
            logger.info(f"Cleaned up {count} expired password reset tokens")
        
        return count

