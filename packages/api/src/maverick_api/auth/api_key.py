"""
API Key authentication.

Used for programmatic access. Provides:
- Simple header-based authentication
- Per-key rate limits
- Usage tracking
"""

from datetime import datetime, UTC

from fastapi import Request
from redis.asyncio import Redis

from maverick_api.auth.base import AuthStrategy
from maverick_schemas.auth import AuthenticatedUser
from maverick_schemas.base import AuthMethod, Tier


class APIKeyAuthStrategy(AuthStrategy):
    """
    API key authentication for programmatic access.

    API keys are passed in the X-API-Key header.
    Keys are stored in Redis with associated metadata.
    """

    HEADER_NAME = "X-API-Key"

    def __init__(
        self,
        redis: Redis | None = None,
        key_prefix: str = "mav_",
    ):
        """
        Initialize API key auth strategy.

        Args:
            redis: Redis client for key validation
            key_prefix: Expected prefix for API keys
        """
        self._redis = redis
        self._key_prefix = key_prefix

    def get_header_name(self) -> str:
        """Return X-API-Key header name."""
        return self.HEADER_NAME

    async def authenticate(self, request: Request) -> AuthenticatedUser | None:
        """
        Authenticate request using API key.

        Expects: X-API-Key: mav_live_xxxxx
        """
        api_key = request.headers.get(self.HEADER_NAME)
        if not api_key:
            return None

        # Validate key format
        if not api_key.startswith(self._key_prefix):
            return None

        # Validate key against store
        return await self._validate_key(api_key)

    async def _validate_key(self, api_key: str) -> AuthenticatedUser | None:
        """Validate API key and return user if valid."""
        if not self._redis:
            # For testing without Redis, accept any properly formatted key
            return AuthenticatedUser(
                user_id="api_key_user",
                auth_method=AuthMethod.API_KEY,
                tier=Tier.FREE,
                rate_limit=100,
            )

        # Get key metadata from Redis
        key_data = await self._redis.hgetall(f"api_key:{api_key}")
        if not key_data:
            return None

        # Decode bytes to strings
        data = {k.decode(): v.decode() for k, v in key_data.items()}

        # Check if key is expired
        expires_at = data.get("expires_at")
        if expires_at:
            expires = datetime.fromisoformat(expires_at)
            if datetime.now(UTC) > expires:
                return None

        # Check if key is revoked
        if data.get("revoked") == "true":
            return None

        # Update last used
        await self._redis.hset(
            f"api_key:{api_key}",
            "last_used",
            datetime.now(UTC).isoformat(),
        )

        # Increment usage counter
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        await self._redis.incr(f"api_key_usage:{api_key}:{today}")
        await self._redis.expire(f"api_key_usage:{api_key}:{today}", 86400 * 2)

        return AuthenticatedUser(
            user_id=data["user_id"],
            auth_method=AuthMethod.API_KEY,
            tier=Tier(data.get("tier", "free")),
            rate_limit=int(data.get("rate_limit", 100)),
        )

    async def create_key(
        self,
        user_id: str,
        name: str,
        tier: Tier = Tier.FREE,
        rate_limit: int = 100,
        expires_in_days: int | None = None,
    ) -> tuple[str, str]:
        """
        Create a new API key.

        Args:
            user_id: User identifier
            name: Key name for identification
            tier: Associated tier
            rate_limit: Requests per minute
            expires_in_days: Optional expiration

        Returns:
            Tuple of (full_key, key_id)
        """
        import secrets

        # Generate key
        key_secret = secrets.token_urlsafe(32)
        full_key = f"{self._key_prefix}live_{key_secret}"
        key_id = full_key[:16]  # First 16 chars as ID

        if self._redis:
            key_data = {
                "user_id": user_id,
                "name": name,
                "tier": tier.value,
                "rate_limit": str(rate_limit),
                "created_at": datetime.now(UTC).isoformat(),
                "revoked": "false",
            }

            if expires_in_days:
                expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)
                key_data["expires_at"] = expires_at.isoformat()

            await self._redis.hset(f"api_key:{full_key}", mapping=key_data)

            # Track key for user
            await self._redis.sadd(f"user_api_keys:{user_id}", full_key)

        return full_key, key_id

    async def revoke_key(self, api_key: str) -> bool:
        """
        Revoke an API key.

        Args:
            api_key: Key to revoke

        Returns:
            True if key was revoked, False if not found
        """
        if not self._redis:
            return False

        exists = await self._redis.exists(f"api_key:{api_key}")
        if not exists:
            return False

        await self._redis.hset(f"api_key:{api_key}", "revoked", "true")
        return True

    async def get_user_keys(self, user_id: str) -> list[dict]:
        """
        Get all API keys for a user.

        Args:
            user_id: User identifier

        Returns:
            List of key metadata (without secrets)
        """
        if not self._redis:
            return []

        key_ids = await self._redis.smembers(f"user_api_keys:{user_id}")
        keys = []

        for key_id in key_ids:
            key_id_str = key_id.decode() if isinstance(key_id, bytes) else key_id
            data = await self._redis.hgetall(f"api_key:{key_id_str}")
            if data:
                key_info = {k.decode(): v.decode() for k, v in data.items()}
                key_info["key_id"] = key_id_str[:16]  # Only show prefix
                keys.append(key_info)

        return keys


# Import timedelta for expires_in_days
from datetime import timedelta

__all__ = ["APIKeyAuthStrategy"]

