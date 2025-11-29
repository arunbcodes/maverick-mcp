"""
Correlation ID management for distributed tracing.

Provides context-aware correlation IDs for tracking requests across services.
"""

import uuid
import asyncio
from contextvars import ContextVar
from functools import wraps
from typing import Callable, TypeVar

# Context variable for correlation ID
correlation_id_var: ContextVar[str | None] = ContextVar(
    "correlation_id", default=None
)

F = TypeVar("F", bound=Callable)


class CorrelationIDMiddleware:
    """Middleware to inject correlation IDs into requests."""

    @staticmethod
    def generate_correlation_id() -> str:
        """Generate a unique correlation ID."""
        return f"mcp-{uuid.uuid4().hex[:8]}"

    @staticmethod
    def set_correlation_id(correlation_id: str | None = None) -> str:
        """
        Set correlation ID in context.

        Args:
            correlation_id: Optional correlation ID to set. If None, generates a new one.

        Returns:
            The correlation ID that was set.
        """
        if not correlation_id:
            correlation_id = CorrelationIDMiddleware.generate_correlation_id()
        correlation_id_var.set(correlation_id)
        return correlation_id

    @staticmethod
    def get_correlation_id() -> str | None:
        """Get current correlation ID from context."""
        return correlation_id_var.get()

    @staticmethod
    def clear_correlation_id() -> None:
        """Clear the correlation ID from context."""
        correlation_id_var.set(None)


def get_correlation_id() -> str | None:
    """Get current correlation ID from context."""
    return CorrelationIDMiddleware.get_correlation_id()


def set_correlation_id(correlation_id: str | None = None) -> str:
    """Set correlation ID in context."""
    return CorrelationIDMiddleware.set_correlation_id(correlation_id)


def with_correlation_id(func: F) -> F:
    """
    Decorator to ensure correlation ID exists for function execution.

    If no correlation ID is present in context, generates a new one before
    executing the function.

    Works with both sync and async functions.

    Usage:
        @with_correlation_id
        def process_request(data):
            # Correlation ID is guaranteed to exist
            return handle(data)

        @with_correlation_id
        async def async_handler(request):
            # Works with async too
            return await process(request)
    """

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        if not correlation_id_var.get():
            CorrelationIDMiddleware.set_correlation_id()
        return func(*args, **kwargs)

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        if not correlation_id_var.get():
            CorrelationIDMiddleware.set_correlation_id()
        return await func(*args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return async_wrapper  # type: ignore
    return sync_wrapper  # type: ignore


class CorrelationContext:
    """
    Context manager for correlation ID scoping.

    Usage:
        with CorrelationContext("request-123"):
            # All logs in this block will have the correlation ID
            logger.info("Processing")
    """

    def __init__(self, correlation_id: str | None = None):
        """
        Initialize correlation context.

        Args:
            correlation_id: Optional correlation ID. If None, generates a new one.
        """
        self.correlation_id = (
            correlation_id or CorrelationIDMiddleware.generate_correlation_id()
        )
        self._token = None

    def __enter__(self) -> str:
        """Enter context and set correlation ID."""
        self._token = correlation_id_var.set(self.correlation_id)
        return self.correlation_id

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and reset correlation ID."""
        if self._token is not None:
            correlation_id_var.reset(self._token)

    async def __aenter__(self) -> str:
        """Async enter context."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async exit context."""
        self.__exit__(exc_type, exc_val, exc_tb)

