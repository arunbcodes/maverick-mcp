"""
JWT authentication with refresh token rotation.

Used for mobile applications. Provides:
- Short-lived access tokens (15 min)
- Long-lived refresh tokens (30 days)
- Refresh token rotation (single-use)
- Token reuse detection
"""

import uuid
from datetime import datetime, timedelta, UTC

from fastapi import HTTPException, Request
from jose import jwt, JWTError
from redis.asyncio import Redis

from maverick_api.auth.base import AuthStrategy
from maverick_schemas.auth import AuthenticatedUser, TokenResponse
from maverick_schemas.base import AuthMethod, Tier


class JWTAuthStrategy(AuthStrategy):
    """
    JWT authentication with refresh token rotation.

    Security features:
    - Short-lived access tokens (15 minutes)
    - Refresh token rotation (each refresh issues new tokens)
    - Token reuse detection (invalidates all tokens on reuse)
    - User blocking on security incidents
    """

    HEADER_NAME = "Authorization"
    BEARER_PREFIX = "Bearer "

    def __init__(
        self,
        secret_key: str,
        redis: Redis | None = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 30,
    ):
        """
        Initialize JWT auth strategy.

        Args:
            secret_key: Secret key for signing tokens
            redis: Redis client for token tracking
            algorithm: JWT algorithm
            access_token_expire_minutes: Access token lifetime
            refresh_token_expire_days: Refresh token lifetime
        """
        self._secret_key = secret_key
        self._redis = redis
        self._algorithm = algorithm
        self._access_expire = timedelta(minutes=access_token_expire_minutes)
        self._refresh_expire = timedelta(days=refresh_token_expire_days)

    def get_header_name(self) -> str:
        """Return Authorization header name."""
        return self.HEADER_NAME

    async def authenticate(self, request: Request) -> AuthenticatedUser | None:
        """
        Authenticate request using JWT access token.

        Expects: Authorization: Bearer <token>
        """
        auth_header = request.headers.get(self.HEADER_NAME)
        if not auth_header or not auth_header.startswith(self.BEARER_PREFIX):
            return None

        token = auth_header[len(self.BEARER_PREFIX):]

        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
        except JWTError:
            return None

        # Must be access token
        if payload.get("type") != "access":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        # Check if user is blocked (security incident)
        if self._redis:
            blocked = await self._redis.get(f"user_blocked:{user_id}")
            if blocked:
                raise HTTPException(
                    status_code=401,
                    detail="Session invalidated - please login again",
                )

        return AuthenticatedUser(
            user_id=user_id,
            auth_method=AuthMethod.JWT,
            tier=Tier(payload.get("tier", "free")),
            token_id=payload.get("jti"),
        )

    def create_tokens(
        self,
        user_id: str,
        tier: Tier = Tier.FREE,
        email: str | None = None,
    ) -> TokenResponse:
        """
        Create access and refresh token pair.

        Args:
            user_id: User identifier
            tier: User subscription tier
            email: Optional user email

        Returns:
            TokenResponse with both tokens
        """
        now = datetime.now(UTC)

        # Access token (short-lived)
        access_payload = {
            "sub": user_id,
            "tier": tier.value,
            "type": "access",
            "exp": now + self._access_expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
        }
        access_token = jwt.encode(
            access_payload,
            self._secret_key,
            algorithm=self._algorithm,
        )

        # Refresh token (long-lived, with unique ID for rotation)
        refresh_jti = str(uuid.uuid4())
        refresh_payload = {
            "sub": user_id,
            "tier": tier.value,
            "type": "refresh",
            "exp": now + self._refresh_expire,
            "iat": now,
            "jti": refresh_jti,
        }
        refresh_token = jwt.encode(
            refresh_payload,
            self._secret_key,
            algorithm=self._algorithm,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(self._access_expire.total_seconds()),
            user_id=user_id,
            tier=tier,
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """
        Rotate refresh token and issue new token pair.

        Security: Each refresh token can only be used once.
        If reuse is detected, all user tokens are invalidated.

        Args:
            refresh_token: Current refresh token

        Returns:
            New TokenResponse

        Raises:
            HTTPException: If token is invalid or reused
        """
        try:
            payload = jwt.decode(
                refresh_token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        token_id = payload.get("jti")
        user_id = payload["sub"]

        # Check if this refresh token was already used
        if self._redis:
            used_key = f"used_refresh:{token_id}"
            was_used = await self._redis.get(used_key)

            if was_used:
                # TOKEN REUSE DETECTED - Possible theft!
                # Invalidate ALL tokens for this user
                await self._revoke_all_user_tokens(user_id)
                raise HTTPException(
                    status_code=401,
                    detail="Token reuse detected - all sessions invalidated",
                )

            # Mark this refresh token as used
            await self._redis.setex(
                used_key,
                int(self._refresh_expire.total_seconds()),
                "1",
            )

        # Issue new tokens
        return self.create_tokens(
            user_id=user_id,
            tier=Tier(payload.get("tier", "free")),
        )

    async def revoke_token(self, token: str) -> None:
        """
        Revoke a specific token.

        Args:
            token: Token to revoke
        """
        if not self._redis:
            return

        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
            token_id = payload.get("jti")
            if token_id:
                await self._redis.setex(f"revoked:{token_id}", 86400 * 30, "1")
        except JWTError:
            pass

    async def _revoke_all_user_tokens(self, user_id: str) -> None:
        """
        Revoke all tokens for a user.

        Called on security incidents (token reuse detection).
        """
        if not self._redis:
            return

        # Block user until all existing tokens expire
        await self._redis.setex(
            f"user_blocked:{user_id}",
            int(self._refresh_expire.total_seconds()),
            datetime.now(UTC).isoformat(),
        )


__all__ = ["JWTAuthStrategy"]

