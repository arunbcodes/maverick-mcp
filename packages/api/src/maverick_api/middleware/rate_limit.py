"""
Tiered rate limiting middleware.

Provides per-tier and per-endpoint rate limits.
"""

import logging
from datetime import datetime, UTC

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from redis.asyncio import Redis

from maverick_api.config import Settings

logger = logging.getLogger(__name__)


# Endpoint-specific limits (override tier limits)
ENDPOINT_LIMITS = {
    # Expensive operations have stricter limits
    "/api/v1/backtest/run": {"requests": 10, "window": 3600},  # 10/hour
    "/api/v1/research/analyze": {"requests": 20, "window": 3600},  # 20/hour
    "/api/v1/backtest/optimize": {"requests": 5, "window": 3600},  # 5/hour
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Tiered rate limiting middleware.

    Rate limits are based on:
    1. User tier (free, pro, enterprise)
    2. Endpoint (some endpoints have stricter limits)

    Uses Redis for distributed rate limiting.
    """

    def __init__(
        self,
        app,
        settings: Settings,
        redis: Redis | None = None,
    ):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            settings: Application settings
            redis: Redis client for rate limiting
        """
        super().__init__(app)
        self.settings = settings
        self._redis = redis

        # Tier limits (requests per minute)
        self.tier_limits = {
            "free": {"requests": settings.rate_limit_free_rpm, "window": 60},
            "pro": {"requests": settings.rate_limit_pro_rpm, "window": 60},
            "enterprise": {"requests": settings.rate_limit_enterprise_rpm, "window": 60},
        }

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Check rate limits before processing request."""

        # Skip rate limiting for health endpoints
        if request.url.path in ("/health", "/ready", "/startup"):
            return await call_next(request)

        # Get user info (may not be authenticated yet)
        user = getattr(request.state, "user", None)
        tier = user.tier.value if user else "free"
        user_id = user.user_id if user else self._get_client_id(request)

        # Get applicable limits
        endpoint = request.url.path
        if endpoint in ENDPOINT_LIMITS:
            limits = ENDPOINT_LIMITS[endpoint]
        else:
            limits = self.tier_limits.get(tier, self.tier_limits["free"])

        # Check rate limit
        try:
            remaining, reset_time = await self._check_limit(
                user_id=user_id,
                endpoint=endpoint,
                limits=limits,
            )
        except HTTPException:
            raise
        except Exception as e:
            # On Redis error, allow request (fail open)
            logger.warning(f"Rate limit check failed: {e}")
            remaining = -1
            reset_time = 0

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        if remaining >= 0:
            response.headers["X-RateLimit-Limit"] = str(limits["requests"])
            response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
            response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response

    async def _check_limit(
        self,
        user_id: str,
        endpoint: str,
        limits: dict,
    ) -> tuple[int, int]:
        """
        Check if request is within rate limits.

        Returns:
            Tuple of (remaining_requests, reset_timestamp)

        Raises:
            HTTPException: If rate limit exceeded
        """
        if not self._redis:
            # No Redis, no rate limiting
            return limits["requests"], 0

        # Use sliding window counter
        key = f"rate_limit:{user_id}:{endpoint}"
        now = datetime.now(UTC).timestamp()
        window = limits["window"]

        # Remove old entries
        await self._redis.zremrangebyscore(key, 0, now - window)

        # Count current requests
        current = await self._redis.zcard(key)

        if current >= limits["requests"]:
            # Get reset time (oldest entry + window)
            oldest = await self._redis.zrange(key, 0, 0, withscores=True)
            reset_time = int(oldest[0][1] + window) if oldest else int(now + window)

            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": limits["requests"],
                    "window": limits["window"],
                    "retry_after": reset_time - int(now),
                },
                headers={
                    "Retry-After": str(reset_time - int(now)),
                    "X-RateLimit-Limit": str(limits["requests"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                },
            )

        # Add current request
        await self._redis.zadd(key, {str(now): now})
        await self._redis.expire(key, window)

        remaining = limits["requests"] - current - 1
        reset_time = int(now + window)

        return remaining, reset_time

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for unauthenticated requests."""
        # Use forwarded IP if behind proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Use direct client IP
        return request.client.host if request.client else "unknown"


__all__ = ["RateLimitMiddleware", "ENDPOINT_LIMITS"]

