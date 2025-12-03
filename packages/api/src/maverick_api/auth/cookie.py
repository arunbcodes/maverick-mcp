"""
Cookie-based authentication with CSRF protection.

Used for web applications. Provides:
- HttpOnly session cookie (secure, not accessible to JS)
- CSRF token cookie (readable by JS for header)
- Double-submit cookie pattern for CSRF protection
"""

import secrets
from datetime import datetime, timedelta, UTC

from fastapi import HTTPException, Request, Response
from redis.asyncio import Redis

from maverick_api.auth.base import AuthStrategy
from maverick_schemas.auth import AuthenticatedUser
from maverick_schemas.base import AuthMethod, Tier


class CookieAuthStrategy(AuthStrategy):
    """
    HttpOnly cookie authentication with CSRF protection.

    Security features:
    - HttpOnly session cookie (prevents XSS access)
    - Secure flag (HTTPS only in production)
    - SameSite=Lax (prevents CSRF for GET, requires token for mutations)
    - CSRF double-submit cookie pattern
    """

    SESSION_COOKIE_NAME = "maverick_session"
    CSRF_COOKIE_NAME = "maverick_csrf"
    CSRF_HEADER_NAME = "X-CSRF-Token"

    def __init__(
        self,
        redis: Redis | None = None,
        session_ttl: int = 60 * 60 * 24 * 7,  # 7 days
        secure: bool = True,
    ):
        """
        Initialize cookie auth strategy.

        Args:
            redis: Redis client for session storage
            session_ttl: Session TTL in seconds
            secure: Whether to use Secure flag (set False for local dev)
        """
        self._redis = redis
        self._session_ttl = session_ttl
        self._secure = secure

    def get_header_name(self) -> str | None:
        """Cookie auth doesn't use headers."""
        return None

    async def authenticate(self, request: Request) -> AuthenticatedUser | None:
        """
        Authenticate request using session cookie.

        For state-changing operations (POST, PUT, DELETE, PATCH),
        also validates CSRF token.
        """
        session_id = request.cookies.get(self.SESSION_COOKIE_NAME)
        if not session_id:
            return None

        # Validate CSRF for mutations
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            csrf_cookie = request.cookies.get(self.CSRF_COOKIE_NAME)
            csrf_header = request.headers.get(self.CSRF_HEADER_NAME)

            if not csrf_cookie or csrf_cookie != csrf_header:
                raise HTTPException(
                    status_code=403,
                    detail="CSRF token mismatch",
                )

        # Validate session
        return await self._validate_session(session_id)

    async def create_session(
        self,
        response: Response,
        user_id: str,
        tier: Tier = Tier.FREE,
        email: str | None = None,
    ) -> tuple[str, str]:
        """
        Create a new session and set cookies.

        Args:
            response: FastAPI response to set cookies on
            user_id: User identifier
            tier: User subscription tier
            email: Optional user email

        Returns:
            Tuple of (session_id, csrf_token)
        """
        session_id = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)

        # Store session in Redis
        if self._redis:
            session_data = {
                "user_id": user_id,
                "tier": tier.value,
                "email": email,
                "created_at": datetime.now(UTC).isoformat(),
            }
            await self._redis.hset(f"session:{session_id}", mapping=session_data)
            await self._redis.expire(f"session:{session_id}", self._session_ttl)

        # Set session cookie (HttpOnly - JS cannot access)
        response.set_cookie(
            key=self.SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            secure=self._secure,
            samesite="lax",
            max_age=self._session_ttl,
            path="/",
        )

        # Set CSRF cookie (NOT HttpOnly - JS must read and send in header)
        response.set_cookie(
            key=self.CSRF_COOKIE_NAME,
            value=csrf_token,
            httponly=False,  # JS needs to read this
            secure=self._secure,
            samesite="strict",
            max_age=self._session_ttl,
            path="/",
        )

        return session_id, csrf_token

    async def destroy_session(self, request: Request, response: Response) -> None:
        """
        Destroy session and clear cookies.

        Args:
            request: Request containing session cookie
            response: Response to clear cookies on
        """
        session_id = request.cookies.get(self.SESSION_COOKIE_NAME)

        # Delete from Redis
        if session_id and self._redis:
            await self._redis.delete(f"session:{session_id}")

        # Clear cookies
        response.delete_cookie(self.SESSION_COOKIE_NAME, path="/")
        response.delete_cookie(self.CSRF_COOKIE_NAME, path="/")

    async def _validate_session(self, session_id: str) -> AuthenticatedUser | None:
        """Validate session and return user if valid."""
        if not self._redis:
            return None

        session_data = await self._redis.hgetall(f"session:{session_id}")
        if not session_data:
            return None

        # Decode bytes to strings
        data = {k.decode(): v.decode() for k, v in session_data.items()}

        return AuthenticatedUser(
            user_id=data["user_id"],
            auth_method=AuthMethod.COOKIE,
            tier=Tier(data.get("tier", "free")),
            email=data.get("email"),
            session_id=session_id,
        )


__all__ = ["CookieAuthStrategy"]

