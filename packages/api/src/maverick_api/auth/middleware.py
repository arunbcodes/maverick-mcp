"""
Multi-strategy authentication middleware.

Tries each authentication strategy in order until one succeeds.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from maverick_api.auth.base import AuthStrategy


# Paths that don't require authentication
PUBLIC_PATHS = {
    "/",
    "/health",
    "/ready",
    "/startup",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
}

# Path prefixes that don't require authentication
PUBLIC_PATH_PREFIXES = (
    "/docs",
    "/redoc",
)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Multi-strategy authentication middleware.

    Tries each strategy in order:
    1. Cookie (web apps)
    2. JWT (mobile apps)
    3. API Key (programmatic)

    First successful authentication wins.
    """

    def __init__(
        self,
        app,
        strategies: list[AuthStrategy] | None = None,
        public_paths: set[str] | None = None,
    ):
        """
        Initialize auth middleware.

        Args:
            app: FastAPI application
            strategies: List of auth strategies (in priority order)
            public_paths: Additional public paths (no auth required)
        """
        super().__init__(app)
        self.strategies = strategies or []
        self.public_paths = (public_paths or set()) | PUBLIC_PATHS

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request through auth strategies."""

        # Skip auth for public endpoints
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Try each auth strategy
        for strategy in self.strategies:
            try:
                user = await strategy.authenticate(request)
                if user:
                    # Store authenticated user in request state
                    request.state.user = user
                    return await call_next(request)
            except HTTPException:
                # Re-raise HTTP exceptions (e.g., CSRF errors)
                raise
            except Exception:
                # Log and continue to next strategy
                continue

        # No strategy succeeded
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer, ApiKey"},
        )

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required)."""
        # Exact match
        if path in self.public_paths:
            return True

        # Prefix match
        if path.startswith(PUBLIC_PATH_PREFIXES):
            return True

        return False


__all__ = ["AuthMiddleware", "PUBLIC_PATHS"]

