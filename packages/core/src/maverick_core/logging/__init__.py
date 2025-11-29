"""
Maverick Core Logging.

Centralized logging configuration with structured output, correlation IDs,
and environment-specific settings.

Usage:
    from maverick_core.logging import (
        setup_logging,
        get_logger,
        with_correlation_id,
        LoggingSettings,
    )

    # Setup logging for the application
    setup_logging()

    # Get a logger for your module
    logger = get_logger(__name__)
    logger.info("Processing request", extra={"user_id": "123"})
"""

from maverick_core.logging.config import (
    StructuredFormatter,
    TextFormatter,
    setup_logging,
    get_logger,
)
from maverick_core.logging.correlation import (
    correlation_id_var,
    CorrelationIDMiddleware,
    with_correlation_id,
    get_correlation_id,
    set_correlation_id,
)
from maverick_core.logging.error_logger import ErrorLogger
from maverick_core.logging.settings import (
    LoggingSettings,
    EnvironmentLogSettings,
    get_logging_settings,
    configure_logging_for_environment,
    validate_logging_settings,
)

__all__ = [
    # Config
    "StructuredFormatter",
    "TextFormatter",
    "setup_logging",
    "get_logger",
    # Correlation
    "correlation_id_var",
    "CorrelationIDMiddleware",
    "with_correlation_id",
    "get_correlation_id",
    "set_correlation_id",
    # Error logging
    "ErrorLogger",
    # Settings
    "LoggingSettings",
    "EnvironmentLogSettings",
    "get_logging_settings",
    "configure_logging_for_environment",
    "validate_logging_settings",
]

