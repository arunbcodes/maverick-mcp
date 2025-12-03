"""
Request logging middleware with correlation IDs.

Adds a unique request ID to every request for tracing.
"""

import logging
import time
import uuid
from contextvars import ContextVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

# Context variable for request ID (accessible throughout request lifecycle)
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

logger = logging.getLogger(__name__)


class CorrelationFilter(logging.Filter):
    """
    Logging filter that adds request_id to log records.

    Usage:
        handler.addFilter(CorrelationFilter())
        formatter = logging.Formatter("%(asctime)s [%(request_id)s] %(message)s")
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id to log record."""
        record.request_id = request_id_ctx.get() or "-"
        return True


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds request ID and logs requests.

    Features:
    - Generates unique request ID (or uses X-Request-ID header)
    - Stores request ID in context var for logging
    - Logs request method, path, and duration
    - Adds X-Request-ID to response headers
    """

    HEADER_NAME = "X-Request-ID"

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request with logging."""

        # Get or generate request ID
        request_id = request.headers.get(self.HEADER_NAME) or str(uuid.uuid4())

        # Store in context var for logging
        request_id_ctx.set(request_id)

        # Store on request for access in handlers
        request.state.request_id = request_id

        # Log request start
        start_time = time.perf_counter()
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={"request_id": request_id},
        )

        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"({duration_ms:.2f}ms) - {type(e).__name__}: {e}",
                extra={"request_id": request_id},
            )
            raise

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log request completion
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"-> {response.status_code} ({duration_ms:.2f}ms)",
            extra={"request_id": request_id},
        )

        # Add request ID to response headers
        response.headers[self.HEADER_NAME] = request_id

        return response


def get_request_id() -> str:
    """Get current request ID from context."""
    return request_id_ctx.get() or str(uuid.uuid4())


__all__ = [
    "RequestLoggingMiddleware",
    "CorrelationFilter",
    "request_id_ctx",
    "get_request_id",
]

