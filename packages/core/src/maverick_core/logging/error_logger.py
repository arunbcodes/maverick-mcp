"""
Enhanced error logging with context and metrics.

Provides structured error logging with sensitive data masking,
error statistics tracking, and rich context information.
"""

import logging
import sys
import traceback
from typing import Any


class ErrorLogger:
    """
    Enhanced error logging with context and metrics.

    Features:
    - Structured error logs with full context
    - Automatic sensitive data masking
    - Error count statistics by type
    - Stack trace capture

    Usage:
        logger = logging.getLogger(__name__)
        error_logger = ErrorLogger(logger)

        try:
            process_request(data)
        except Exception as e:
            error_logger.log_error(e, {"request_id": "123", "user": "alice"})
    """

    # Default sensitive field patterns to mask
    DEFAULT_SENSITIVE_FIELDS = frozenset({
        "password",
        "token",
        "api_key",
        "secret",
        "card_number",
        "ssn",
        "email",
        "phone",
        "address",
        "bearer",
        "authorization",
        "x-api-key",
        "credential",
        "private_key",
        "access_token",
        "refresh_token",
        "session",
        "cookie",
    })

    def __init__(
        self,
        logger: logging.Logger,
        sensitive_fields: frozenset[str] | None = None,
    ):
        """
        Initialize error logger.

        Args:
            logger: Base logger to use for output
            sensitive_fields: Set of field name patterns to mask (case-insensitive)
        """
        self.logger = logger
        self.sensitive_fields = sensitive_fields or self.DEFAULT_SENSITIVE_FIELDS
        self._error_counts: dict[str, int] = {}

    def log_error(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
        level: int = logging.ERROR,
        mask_sensitive: bool = True,
        include_traceback: bool = True,
    ) -> None:
        """
        Log error with full context and tracking.

        Args:
            error: Exception to log
            context: Additional context dictionary
            level: Log level (default: ERROR)
            mask_sensitive: Whether to mask sensitive data (default: True)
            include_traceback: Whether to include stack trace (default: True)
        """
        context = context or {}
        error_type = type(error).__name__

        # Track error count
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1

        # Mask sensitive data if requested
        if mask_sensitive:
            context = self._mask_sensitive_data(context)

        # Build extra data for structured logging
        extra: dict[str, Any] = {
            "error_type": error_type,
            "error_message": str(error),
            "error_count": self._error_counts[error_type],
            "error_context": context,
        }

        # Add stack trace if requested
        if include_traceback:
            exc_info = sys.exc_info()
            if exc_info[0] is not None:
                extra["stack_trace"] = traceback.format_exc()

        # Add error attributes if it's a custom exception
        if hasattr(error, "error_code"):
            extra["error_code"] = error.error_code
        if hasattr(error, "status_code"):
            extra["status_code"] = error.status_code
        if hasattr(error, "to_dict"):
            extra["error_details"] = error.to_dict()

        # Log the error
        self.logger.log(
            level,
            f"{error_type}: {str(error)}",
            extra=extra,
        )

    def log_warning(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        mask_sensitive: bool = True,
    ) -> None:
        """
        Log warning with context.

        Args:
            message: Warning message
            context: Additional context dictionary
            mask_sensitive: Whether to mask sensitive data
        """
        context = context or {}
        if mask_sensitive:
            context = self._mask_sensitive_data(context)

        self.logger.warning(message, extra={"warning_context": context})

    def _mask_sensitive_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Mask sensitive fields in logging data.

        Args:
            data: Dictionary to mask

        Returns:
            New dictionary with sensitive values masked.
        """
        masked_data = {}
        for key, value in data.items():
            if self._is_sensitive_field(key):
                masked_data[key] = "***MASKED***"
            elif isinstance(value, dict):
                masked_data[key] = self._mask_sensitive_data(value)
            elif isinstance(value, list):
                masked_data[key] = [
                    self._mask_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked_data[key] = value

        return masked_data

    def _is_sensitive_field(self, field_name: str) -> bool:
        """
        Check if a field name matches any sensitive patterns.

        Args:
            field_name: Field name to check

        Returns:
            True if field should be masked.
        """
        lower_name = field_name.lower()
        return any(
            sensitive in lower_name for sensitive in self.sensitive_fields
        )

    def get_error_stats(self) -> dict[str, int]:
        """
        Get error count statistics.

        Returns:
            Dictionary mapping error type names to their occurrence counts.
        """
        return self._error_counts.copy()

    def reset_error_stats(self) -> None:
        """Reset error count statistics."""
        self._error_counts.clear()

    def get_top_errors(self, n: int = 5) -> list[tuple[str, int]]:
        """
        Get the most frequent error types.

        Args:
            n: Number of top errors to return

        Returns:
            List of (error_type, count) tuples sorted by count descending.
        """
        sorted_errors = sorted(
            self._error_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return sorted_errors[:n]


def create_error_logger(
    name: str,
    sensitive_fields: frozenset[str] | None = None,
) -> ErrorLogger:
    """
    Create an error logger for the given module name.

    Args:
        name: Logger name, typically __name__
        sensitive_fields: Optional custom set of sensitive field patterns

    Returns:
        Configured ErrorLogger instance.

    Example:
        error_logger = create_error_logger(__name__)
        error_logger.log_error(exception, {"user_id": user_id})
    """
    logger = logging.getLogger(name)
    return ErrorLogger(logger, sensitive_fields)

