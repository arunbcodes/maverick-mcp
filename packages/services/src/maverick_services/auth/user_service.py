"""
User service for authentication operations.

Handles user registration, authentication, and profile management.
"""

from datetime import datetime, UTC
from uuid import UUID
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from maverick_schemas.auth import AuthenticatedUser
from maverick_services.auth.password import PasswordHasher, password_hasher
from maverick_services.exceptions import (
    ServiceException,
    NotFoundError,
    ConflictError,
    AuthenticationError,
)

logger = logging.getLogger(__name__)


class UserService:
    """
    Service for user management operations.
    
    Handles:
    - User registration with password hashing
    - User authentication (login)
    - Profile retrieval and updates
    - Last login tracking
    """
    
    def __init__(
        self,
        db: AsyncSession,
        password_hasher: PasswordHasher | None = None,
    ):
        """
        Initialize the user service.
        
        Args:
            db: Async database session
            password_hasher: Optional custom password hasher
        """
        self._db = db
        self._hasher = password_hasher or globals()["password_hasher"]
    
    async def register(
        self,
        email: str,
        password: str,
        tier: str = "free",
        name: str | None = None,
    ) -> dict:
        """
        Register a new user.
        
        Args:
            email: User email address
            password: Plain text password
            tier: Subscription tier (default: free)
            name: Optional display name
            
        Returns:
            Dict with user_id, email, and name
            
        Raises:
            ConflictError: If email already exists
            ServiceException: On database error
        """
        from maverick_data.models import User
        
        # Normalize email
        email = email.lower().strip()
        
        # Check if email already exists
        existing = await self._db.execute(
            select(User).where(User.email == email)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Email {email} is already registered")
        
        # Hash password
        password_hash = self._hasher.hash(password)
        
        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            tier=tier,
            name=name,
        )
        
        self._db.add(user)
        
        try:
            await self._db.commit()
            await self._db.refresh(user)
            
            logger.info(f"User registered: {email}")
            
            return {
                "user_id": str(user.id),
                "email": user.email,
                "name": user.name,
                "tier": user.tier,
            }
        except Exception as e:
            await self._db.rollback()
            logger.error(f"Failed to register user {email}: {e}")
            raise ServiceException(f"Registration failed: {e}")
    
    async def authenticate(
        self,
        email: str,
        password: str,
    ) -> AuthenticatedUser:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User email address
            password: Plain text password
            
        Returns:
            AuthenticatedUser on success
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        from maverick_data.models import User
        
        # Normalize email
        email = email.lower().strip()
        
        # Find user
        result = await self._db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Use same error message to prevent user enumeration
            raise AuthenticationError("Invalid email or password")
        
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")
        
        # Verify password
        if not self._hasher.verify(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        
        # Check if password needs rehash (security upgrade)
        if self._hasher.needs_rehash(user.password_hash):
            user.password_hash = self._hasher.hash(password)
            await self._db.commit()
            logger.info(f"Rehashed password for user {email}")
        
        # Update last login
        user.last_login_at = datetime.now(UTC)
        await self._db.commit()
        
        logger.info(f"User authenticated: {email}")
        
        return AuthenticatedUser(
            user_id=str(user.id),
            email=user.email,
            tier=user.tier,
            auth_method="password",
        )
    
    async def get_by_id(self, user_id: UUID | str) -> dict:
        """
        Get user by ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            Dict with user details
            
        Raises:
            NotFoundError: If user not found
        """
        from maverick_data.models import User
        
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        result = await self._db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        return {
            "user_id": str(user.id),
            "email": user.email,
            "name": user.name,
            "tier": user.tier,
            "email_verified": user.email_verified,
            "is_demo_user": user.is_demo_user,
            "onboarding_completed": user.onboarding_completed,
            "created_at": user.created_at.isoformat(),
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        }
    
    async def get_by_email(self, email: str) -> dict | None:
        """
        Get user by email.
        
        Args:
            email: User email address
            
        Returns:
            Dict with user details or None if not found
        """
        from maverick_data.models import User
        
        email = email.lower().strip()
        
        result = await self._db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        return {
            "user_id": str(user.id),
            "email": user.email,
            "tier": user.tier,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
        }
    
    async def update_password(
        self,
        user_id: UUID | str,
        current_password: str,
        new_password: str,
    ) -> bool:
        """
        Update user password.
        
        Args:
            user_id: User UUID
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True on success
            
        Raises:
            NotFoundError: If user not found
            AuthenticationError: If current password is wrong
        """
        from maverick_data.models import User
        
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        result = await self._db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        # Verify current password
        if not self._hasher.verify(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")
        
        # Hash and set new password
        user.password_hash = self._hasher.hash(new_password)
        user.updated_at = datetime.now(UTC)
        
        await self._db.commit()
        
        logger.info(f"Password updated for user {user.email}")
        
        return True
    
    async def deactivate(self, user_id: UUID | str) -> bool:
        """
        Deactivate a user account (soft delete).
        
        Args:
            user_id: User UUID
            
        Returns:
            True on success
            
        Raises:
            NotFoundError: If user not found
        """
        from maverick_data.models import User
        
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        result = await self._db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        user.is_active = False
        user.updated_at = datetime.now(UTC)
        
        await self._db.commit()
        
        logger.info(f"User deactivated: {user.email}")
        
        return True

