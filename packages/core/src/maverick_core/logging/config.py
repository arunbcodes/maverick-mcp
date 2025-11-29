"""
Logging configuration and setup.

Provides structured JSON logging and text formatting with correlation ID support.
"""

import json
import logging
import sys
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any

from maverick_core.logging.correlation import correlation_id_var


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs log records as JSON with additional metadata including:
    - Timestamp in ISO format
    - Correlation ID from context
    - Exception details if present
    - Custom extra fields
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with additional metadata."""
        # Get correlation ID from context
        correlation_id = correlation_id_var.get()

        # Build structured log entry
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            if exc_type is not None:
                log_entry["exception"] = {
                    "type": exc_type.__name__,
                    "message": str(exc_value),
                    "traceback": traceback.format_exception(
                        exc_type, exc_value, exc_tb
                    ),
                }

        # Add extra fields (excluding standard LogRecord attributes)
        standard_attrs = {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "thread",
            "threadName",
            "exc_info",
            "exc_text",
            "stack_info",
            "taskName",
        }

        for key, value in record.__dict__.items():
            if key not in standard_attrs:
                try:
                    # Ensure value is JSON serializable
                    json.dumps(value)
                    log_entry[key] = value
                except (TypeError, ValueError):
                    log_entry[key] = str(value)

        return json.dumps(log_entry, default=str)


class TextFormatter(logging.Formatter):
    """
    Human-readable text formatter for development.

    Includes correlation ID and colored level names for terminal output.
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True):
        """
        Initialize text formatter.

        Args:
            use_colors: Whether to use ANSI colors in output.
        """
        super().__init__()
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as human-readable text."""
        correlation_id = correlation_id_var.get()
        correlation_str = f"[{correlation_id}] " if correlation_id else ""

        level = record.levelname
        if self.use_colors:
            color = self.COLORS.get(level, "")
            level = f"{color}{level}{self.RESET}"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        message = f"{timestamp} | {level:8} | {record.name} | {correlation_str}{record.getMessage()}"

        if record.exc_info:
            message += "\n" + "".join(
                traceback.format_exception(*record.exc_info)
            )

        return message


def setup_logging(
    level: int | str = logging.INFO,
    use_json: bool = True,
    log_file: str | None = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    use_colors: bool = True,
) -> logging.Logger:
    """
    Configure application logging with structured output.

    Args:
        level: Logging level (default: INFO)
        use_json: Use JSON formatting (default: True)
        log_file: Optional file path for file logging
        max_bytes: Maximum log file size before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
        use_colors: Use colors in text format (default: True)

    Returns:
        The root logger configured with the specified settings.

    Example:
        # Basic setup with JSON logging
        setup_logging()

        # Development setup with text logging
        setup_logging(level="DEBUG", use_json=False)

        # Production setup with file logging
        setup_logging(
            level="INFO",
            use_json=True,
            log_file="/var/log/maverick/app.log"
        )
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = TextFormatter(use_colors=use_colors)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        # Always use JSON for file logging
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)

    # Configure third-party loggers to reduce noise
    noisy_loggers = [
        "urllib3",
        "requests",
        "httpx",
        "httpcore",
        "asyncio",
        "yfinance",
        "filelock",
        "charset_normalizer",
    ]
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    This is a convenience wrapper around logging.getLogger that ensures
    the logging system is properly configured.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        Configured logger instance.

    Example:
        logger = get_logger(__name__)
        logger.info("Processing started", extra={"item_count": 100})
    """
    return logging.getLogger(name)


def add_file_handler(
    logger: logging.Logger,
    log_file: str,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    level: int = logging.DEBUG,
) -> RotatingFileHandler:
    """
    Add a rotating file handler to an existing logger.

    Args:
        logger: Logger to add handler to
        log_file: Path to log file
        max_bytes: Maximum file size before rotation
        backup_count: Number of backup files to keep
        level: Minimum log level for file handler

    Returns:
        The created file handler.
    """
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    return handler

