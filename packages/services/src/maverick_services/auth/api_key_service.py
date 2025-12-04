"""
API Key service for managing programmatic access.

Handles API key creation, validation, and revocation.
"""

from datetime import datetime, timedelta, UTC
from uuid import UUID
import secrets
import logging

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from maverick_services.auth.password import PasswordHasher
from maverick_services.exceptions import (
    NotFoundError,
    AuthorizationError,
)

logger = logging.getLogger(__name__)


class APIKeyService:
    """
    Service for API key management.
    
    Handles:
    - API key creation with secure random generation
    - API key validation (hash comparison)
    - API key listing for a user
    - API key revocation
    """
    
    KEY_PREFIX = "mav_"
    KEY_LENGTH = 32  # 256 bits of entropy
    
    def __init__(
        self,
        db: AsyncSession,
        hasher: PasswordHasher | None = None,
    ):
        """
        Initialize the API key service.
        
        Args:
            db: Async database session
            hasher: Optional custom password hasher
        """
        self._db = db
        self._hasher = hasher or PasswordHasher()
    
    def _generate_key(self) -> tuple[str, str]:
        """
        Generate a new API key.
        
        Returns:
            Tuple of (full_key, key_prefix) where:
            - full_key: The complete API key (shown once to user)
            - key_prefix: First 12 chars for identification
        """
        # Generate random bytes and convert to hex
        random_part = secrets.token_hex(self.KEY_LENGTH)
        full_key = f"{self.KEY_PREFIX}{random_part}"
        
        # Use first 12 chars after prefix as the visible ID
        key_prefix = full_key[:len(self.KEY_PREFIX) + 8]
        
        return full_key, key_prefix
    
    async def create_key(
        self,
        user_id: UUID | str,
        name: str,
        tier: str = "free",
        expires_in_days: int | None = None,
    ) -> dict:
        """
        Create a new API key for a user.
        
        Args:
            user_id: User UUID who owns the key
            name: Human-readable name for the key
            tier: Subscription tier for rate limiting
            expires_in_days: Optional expiration in days
            
        Returns:
            Dict with key details (full key only shown once)
        """
        from maverick_data.models import APIKey
        
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        # Generate the key
        full_key, key_prefix = self._generate_key()
        
        # Hash the key for storage
        key_hash = self._hasher.hash(full_key)
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)
        
        # Create the API key record
        api_key = APIKey(
            user_id=user_id,
            key_prefix=key_prefix,
            key_hash=key_hash,
            name=name,
            tier=tier,
            expires_at=expires_at,
        )
        
        self._db.add(api_key)
        await self._db.commit()
        await self._db.refresh(api_key)
        
        logger.info(f"Created API key {key_prefix} for user {user_id}")
        
        return {
            "key_id": str(api_key.id),
            "key": full_key,  # Only shown once!
            "key_prefix": key_prefix,
            "name": name,
            "tier": tier,
            "created_at": api_key.created_at.isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
        }
    
    async def list_keys(self, user_id: UUID | str) -> list[dict]:
        """
        List all API keys for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            List of API key details (without full key)
        """
        from maverick_data.models import APIKey
        
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        result = await self._db.execute(
            select(APIKey)
            .where(
                and_(
                    APIKey.user_id == user_id,
                    APIKey.is_active == True,
                )
            )
            .order_by(APIKey.created_at.desc())
        )
        keys = result.scalars().all()
        
        return [
            {
                "key_id": str(key.id),
                "key_prefix": key.key_prefix,
                "name": key.name,
                "tier": key.tier,
                "rate_limit": key.rate_limit,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "created_at": key.created_at.isoformat(),
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            }
            for key in keys
        ]
    
    async def revoke_key(
        self,
        key_id: UUID | str,
        user_id: UUID | str,
    ) -> bool:
        """
        Revoke an API key.
        
        Args:
            key_id: API key UUID
            user_id: User UUID (for authorization check)
            
        Returns:
            True on success
            
        Raises:
            NotFoundError: If key not found
            AuthorizationError: If key doesn't belong to user
        """
        from maverick_data.models import APIKey
        
        if isinstance(key_id, str):
            key_id = UUID(key_id)
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        result = await self._db.execute(
            select(APIKey).where(APIKey.id == key_id)
        )
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            raise NotFoundError(f"API key {key_id} not found")
        
        if api_key.user_id != user_id:
            raise AuthorizationError("Cannot revoke another user's API key")
        
        api_key.is_active = False
        api_key.updated_at = datetime.now(UTC)
        
        await self._db.commit()
        
        logger.info(f"Revoked API key {api_key.key_prefix} for user {user_id}")
        
        return True
    
    async def validate_key(self, full_key: str) -> dict | None:
        """
        Validate an API key and return associated user info.
        
        Args:
            full_key: The full API key
            
        Returns:
            Dict with user info if valid, None otherwise
        """
        from maverick_data.models import APIKey
        
        # Extract prefix from key
        if not full_key.startswith(self.KEY_PREFIX):
            return None
        
        key_prefix = full_key[:len(self.KEY_PREFIX) + 8]
        
        # Find key by prefix
        result = await self._db.execute(
            select(APIKey).where(
                and_(
                    APIKey.key_prefix == key_prefix,
                    APIKey.is_active == True,
                )
            )
        )
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            return None
        
        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
            return None
        
        # Verify hash
        if not self._hasher.verify(full_key, api_key.key_hash):
            return None
        
        # Update last used
        api_key.last_used_at = datetime.now(UTC)
        await self._db.commit()
        
        return {
            "user_id": str(api_key.user_id),
            "tier": api_key.tier,
            "rate_limit": api_key.rate_limit,
            "key_prefix": api_key.key_prefix,
        }

