"""
Sentry error tracking integration for MaverickMCP.

This module provides Sentry integration for production monitoring and alerting,
including:
- Automatic error capture with context
- Performance tracing
- User context management
- Breadcrumb tracking
"""

import logging
import os
from contextlib import contextmanager
from typing import Any, Generator

logger = logging.getLogger(__name__)


class SentryService:
    """
    Service for Sentry error tracking and performance monitoring.

    Usage:
        sentry = SentryService()
        sentry.capture_exception(error, user_id="123", endpoint="/api/stock")
    """

    def __init__(self, dsn: str | None = None, environment: str = "development"):
        """
        Initialize Sentry service.

        Args:
            dsn: Sentry DSN. If None, reads from SENTRY_DSN environment variable.
            environment: Deployment environment (development, staging, production).
        """
        self.enabled = False
        self.environment = environment
        self._sentry = None

        dsn = dsn or os.getenv("SENTRY_DSN")
        if dsn:
            self._initialize(dsn)

    def _initialize(self, dsn: str) -> None:
        """Initialize Sentry with the provided DSN."""
        try:
            import sentry_sdk
            from sentry_sdk.integrations.asyncio import AsyncioIntegration
            from sentry_sdk.integrations.logging import LoggingIntegration

            # Determine sample rates based on environment
            is_production = self.environment == "production"
            traces_sample_rate = 0.1 if is_production else 1.0
            profiles_sample_rate = 0.1 if is_production else 1.0

            # Configure Sentry
            sentry_sdk.init(
                dsn=dsn,
                environment=self.environment,
                traces_sample_rate=traces_sample_rate,
                profiles_sample_rate=profiles_sample_rate,
                integrations=[
                    AsyncioIntegration(),
                    LoggingIntegration(
                        level=None,  # Capture all levels
                        event_level=None,  # Don't create events from logs
                    ),
                ],
                before_send=self._before_send,
                attach_stacktrace=True,
                send_default_pii=False,  # Don't send PII
                release=os.getenv("RELEASE_VERSION", "unknown"),
            )

            # Set application context
            sentry_sdk.set_context(
                "app",
                {
                    "name": "MaverickMCP",
                    "environment": self.environment,
                },
            )

            self._sentry = sentry_sdk
            self.enabled = True
            logger.info("Sentry error tracking initialized")

        except ImportError:
            logger.warning("Sentry SDK not installed. Run: pip install sentry-sdk")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")

    def _before_send(
        self, event: dict[str, Any], hint: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Filter events before sending to Sentry.

        Removes sensitive data and skips certain error types.
        """
        # Don't send certain errors
        if "exc_info" in hint:
            _, exc_value, _ = hint["exc_info"]

            # Skip client errors
            error_message = str(exc_value).lower()
            skip_patterns = [
                "client disconnected",
                "connection reset",
                "broken pipe",
                "cancelled",
            ]
            if any(skip in error_message for skip in skip_patterns):
                return None

        # Remove sensitive data from request
        if "request" in event:
            request = event["request"]
            # Remove auth headers
            if "headers" in request:
                sensitive_headers = {"authorization", "cookie", "x-api-key", "token"}
                request["headers"] = {
                    k: "***REDACTED***" if k.lower() in sensitive_headers else v
                    for k, v in request["headers"].items()
                }

        return event

    def capture_exception(self, error: Exception, **context: Any) -> str | None:
        """
        Capture exception with Sentry.

        Args:
            error: Exception to capture
            **context: Additional context to attach to the event

        Returns:
            Event ID if captured, None otherwise.
        """
        if not self.enabled or not self._sentry:
            return None

        try:
            # Add context
            for key, value in context.items():
                self._sentry.set_context(key, {"value": value})

            # Capture the exception
            return self._sentry.capture_exception(error)

        except Exception as e:
            logger.error(f"Failed to capture exception with Sentry: {e}")
            return None

    def capture_message(
        self, message: str, level: str = "info", **context: Any
    ) -> str | None:
        """
        Capture message with Sentry.

        Args:
            message: Message to capture
            level: Log level (debug, info, warning, error, fatal)
            **context: Additional context to attach

        Returns:
            Event ID if captured, None otherwise.
        """
        if not self.enabled or not self._sentry:
            return None

        try:
            # Add context
            for key, value in context.items():
                self._sentry.set_context(key, {"value": value})

            # Capture the message
            return self._sentry.capture_message(message, level=level)

        except Exception as e:
            logger.error(f"Failed to capture message with Sentry: {e}")
            return None

    def set_user_context(
        self,
        user_id: str | None,
        email: str | None = None,
        username: str | None = None,
    ) -> None:
        """
        Set user context for Sentry events.

        Args:
            user_id: User ID
            email: User email (optional)
            username: Username (optional)
        """
        if not self.enabled or not self._sentry:
            return

        try:
            if user_id:
                user_data: dict[str, Any] = {"id": user_id}
                if email:
                    user_data["email"] = email
                if username:
                    user_data["username"] = username
                self._sentry.set_user(user_data)
            else:
                self._sentry.set_user(None)

        except Exception as e:
            logger.error(f"Failed to set user context: {e}")

    def clear_user_context(self) -> None:
        """Clear user context."""
        self.set_user_context(None)

    @contextmanager
    def transaction(
        self, name: str, op: str = "task"
    ) -> Generator[Any, None, None]:
        """
        Create a Sentry transaction for performance monitoring.

        Args:
            name: Transaction name
            op: Operation type (task, http.server, etc.)

        Usage:
            with sentry.transaction("process_order", "task"):
                process_order()
        """
        if not self.enabled or not self._sentry:
            yield None
            return

        try:
            with self._sentry.start_transaction(name=name, op=op) as transaction:
                yield transaction

        except Exception as e:
            logger.error(f"Failed to create transaction: {e}")
            yield None

    @contextmanager
    def span(self, description: str, op: str = "task") -> Generator[Any, None, None]:
        """
        Create a Sentry span within a transaction.

        Args:
            description: Span description
            op: Operation type

        Usage:
            with sentry.span("database_query", "db"):
                result = query_database()
        """
        if not self.enabled or not self._sentry:
            yield None
            return

        try:
            with self._sentry.start_span(description=description, op=op) as span:
                yield span

        except Exception as e:
            logger.error(f"Failed to create span: {e}")
            yield None

    def add_breadcrumb(
        self,
        message: str,
        category: str = "app",
        level: str = "info",
        **data: Any,
    ) -> None:
        """
        Add breadcrumb for Sentry.

        Breadcrumbs are a trail of events that happened prior to an issue.

        Args:
            message: Breadcrumb message
            category: Category (app, http, ui, navigation, etc.)
            level: Level (debug, info, warning, error, critical)
            **data: Additional data to attach
        """
        if not self.enabled or not self._sentry:
            return

        try:
            self._sentry.add_breadcrumb(
                message=message,
                category=category,
                level=level,
                data=data if data else None,
            )

        except Exception as e:
            logger.error(f"Failed to add breadcrumb: {e}")

    def set_tag(self, key: str, value: str) -> None:
        """
        Set a tag on future events.

        Tags are indexed and searchable in Sentry.

        Args:
            key: Tag key
            value: Tag value
        """
        if not self.enabled or not self._sentry:
            return

        try:
            self._sentry.set_tag(key, value)
        except Exception as e:
            logger.error(f"Failed to set tag: {e}")

    def set_context(self, name: str, context: dict[str, Any]) -> None:
        """
        Set additional context on future events.

        Args:
            name: Context name
            context: Context data
        """
        if not self.enabled or not self._sentry:
            return

        try:
            self._sentry.set_context(name, context)
        except Exception as e:
            logger.error(f"Failed to set context: {e}")


# Global Sentry service instance
_sentry_service: SentryService | None = None


def get_sentry_service(
    dsn: str | None = None, environment: str | None = None
) -> SentryService:
    """
    Get or create the global Sentry service.

    Args:
        dsn: Optional DSN to use (reads from SENTRY_DSN if not provided)
        environment: Optional environment (reads from MAVERICK_ENVIRONMENT if not provided)

    Returns:
        SentryService instance
    """
    global _sentry_service

    if _sentry_service is None:
        env = environment or os.getenv("MAVERICK_ENVIRONMENT", "development")
        _sentry_service = SentryService(dsn=dsn, environment=env)

    return _sentry_service


def capture_exception(error: Exception, **context: Any) -> str | None:
    """Convenience function to capture an exception."""
    return get_sentry_service().capture_exception(error, **context)


def capture_message(message: str, level: str = "info", **context: Any) -> str | None:
    """Convenience function to capture a message."""
    return get_sentry_service().capture_message(message, level=level, **context)


def add_breadcrumb(
    message: str, category: str = "app", level: str = "info", **data: Any
) -> None:
    """Convenience function to add a breadcrumb."""
    get_sentry_service().add_breadcrumb(message, category, level, **data)

