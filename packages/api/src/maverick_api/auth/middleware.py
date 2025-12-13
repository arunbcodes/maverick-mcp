"""
Multi-strategy authentication middleware.

Tries each authentication strategy in order until one succeeds.
"""

from datetime import datetime, UTC

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, JSONResponse

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
    "/api/v1/auth/demo-login",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
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
            except HTTPException as e:
                # Return HTTP exceptions as JSON response (e.g., CSRF errors)
                return JSONResponse(
                    status_code=e.status_code,
                    content={
                        "success": False,
                        "error": {
                            "code": "UNAUTHORIZED" if e.status_code == 401 else "AUTH_ERROR",
                            "message": str(e.detail) if isinstance(e.detail, str) else "Authentication error",
                            "details": e.detail if isinstance(e.detail, dict) else None,
                            "field": None,
                        },
                        "meta": {
                            "request_id": getattr(request.state, "request_id", "unknown"),
                            "timestamp": datetime.now(UTC).isoformat(),
                            "version": "1.0.0",
                        },
                    },
                    headers=e.headers,
                )
            except Exception:
                # Log and continue to next strategy
                continue

        # No strategy succeeded - return JSON response directly
        # (BaseHTTPMiddleware doesn't properly propagate HTTPExceptions)
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Authentication required",
                    "details": None,
                    "field": None,
                },
                "meta": {
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "timestamp": datetime.now(UTC).isoformat(),
                    "version": "1.0.0",
                },
            },
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

