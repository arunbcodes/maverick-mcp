"""
Structured logging configuration settings.

Provides centralized configuration for all logging-related settings including
log levels, output formats, file logging, and performance monitoring.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LoggingSettings:
    """
    Comprehensive logging configuration settings.

    All settings can be configured via environment variables with the
    MAVERICK_ prefix. For example, MAVERICK_LOG_LEVEL sets log_level.
    """

    # Basic logging configuration
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    enable_async_logging: bool = True
    console_output: str = "stderr"  # stdout or stderr

    # File logging configuration
    enable_file_logging: bool = True
    log_file_path: str = "logs/maverick.log"
    enable_log_rotation: bool = True
    max_log_size_mb: int = 10
    backup_count: int = 5

    # Debug mode configuration
    debug_enabled: bool = False
    verbose_modules: list[str] = field(default_factory=list)
    log_request_response: bool = False
    max_payload_length: int = 1000

    # Performance monitoring
    enable_performance_logging: bool = True
    performance_log_threshold_ms: float = 1000.0
    enable_resource_tracking: bool = True
    enable_business_metrics: bool = True

    # Async logging configuration
    async_log_queue_size: int = 10000
    async_log_flush_interval: float = 1.0

    # Sensitive data handling
    mask_sensitive_data: bool = True
    sensitive_field_patterns: list[str] = field(default_factory=list)

    # Remote logging (for future log aggregation)
    enable_remote_logging: bool = False
    remote_endpoint: str | None = None
    remote_api_key: str | None = None

    # Correlation and tracing
    enable_correlation_tracking: bool = True
    correlation_id_header: str = "X-Correlation-ID"
    enable_request_tracing: bool = True

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if not self.verbose_modules:
            self.verbose_modules = []

        if not self.sensitive_field_patterns:
            self.sensitive_field_patterns = [
                "password",
                "token",
                "key",
                "secret",
                "auth",
                "credential",
                "bearer",
                "session",
                "cookie",
                "api_key",
                "access_token",
                "refresh_token",
                "private",
                "confidential",
            ]

    @classmethod
    def from_env(cls) -> "LoggingSettings":
        """
        Create logging settings from environment variables.

        Environment variables are prefixed with MAVERICK_.
        Boolean values are case-insensitive ("true"/"false").

        Returns:
            LoggingSettings instance configured from environment.
        """
        return cls(
            log_level=os.getenv("MAVERICK_LOG_LEVEL", "INFO").upper(),
            log_format=os.getenv("MAVERICK_LOG_FORMAT", "json").lower(),
            enable_async_logging=_env_bool("MAVERICK_ASYNC_LOGGING", True),
            console_output=os.getenv("MAVERICK_CONSOLE_OUTPUT", "stderr").lower(),
            # File logging
            enable_file_logging=_env_bool("MAVERICK_FILE_LOGGING", True),
            log_file_path=os.getenv("MAVERICK_LOG_FILE", "logs/maverick.log"),
            enable_log_rotation=_env_bool("MAVERICK_LOG_ROTATION", True),
            max_log_size_mb=int(os.getenv("MAVERICK_LOG_SIZE_MB", "10")),
            backup_count=int(os.getenv("MAVERICK_LOG_BACKUPS", "5")),
            # Debug configuration
            debug_enabled=_env_bool("MAVERICK_DEBUG", False),
            log_request_response=_env_bool("MAVERICK_LOG_REQUESTS", False),
            max_payload_length=int(os.getenv("MAVERICK_MAX_PAYLOAD", "1000")),
            # Performance monitoring
            enable_performance_logging=_env_bool("MAVERICK_PERF_LOGGING", True),
            performance_log_threshold_ms=float(
                os.getenv("MAVERICK_PERF_THRESHOLD", "1000.0")
            ),
            enable_resource_tracking=_env_bool("MAVERICK_RESOURCE_TRACKING", True),
            enable_business_metrics=_env_bool("MAVERICK_BUSINESS_METRICS", True),
            # Async logging
            async_log_queue_size=int(os.getenv("MAVERICK_LOG_QUEUE_SIZE", "10000")),
            async_log_flush_interval=float(
                os.getenv("MAVERICK_LOG_FLUSH_INTERVAL", "1.0")
            ),
            # Sensitive data
            mask_sensitive_data=_env_bool("MAVERICK_MASK_SENSITIVE", True),
            # Remote logging
            enable_remote_logging=_env_bool("MAVERICK_REMOTE_LOGGING", False),
            remote_endpoint=os.getenv("MAVERICK_REMOTE_LOG_ENDPOINT"),
            remote_api_key=os.getenv("MAVERICK_REMOTE_LOG_API_KEY"),
            # Correlation and tracing
            enable_correlation_tracking=_env_bool(
                "MAVERICK_CORRELATION_TRACKING", True
            ),
            correlation_id_header=os.getenv(
                "MAVERICK_CORRELATION_HEADER", "X-Correlation-ID"
            ),
            enable_request_tracing=_env_bool("MAVERICK_REQUEST_TRACING", True),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary for serialization."""
        return {
            "log_level": self.log_level,
            "log_format": self.log_format,
            "enable_async_logging": self.enable_async_logging,
            "console_output": self.console_output,
            "enable_file_logging": self.enable_file_logging,
            "log_file_path": self.log_file_path,
            "enable_log_rotation": self.enable_log_rotation,
            "max_log_size_mb": self.max_log_size_mb,
            "backup_count": self.backup_count,
            "debug_enabled": self.debug_enabled,
            "verbose_modules": self.verbose_modules,
            "log_request_response": self.log_request_response,
            "max_payload_length": self.max_payload_length,
            "enable_performance_logging": self.enable_performance_logging,
            "performance_log_threshold_ms": self.performance_log_threshold_ms,
            "enable_resource_tracking": self.enable_resource_tracking,
            "enable_business_metrics": self.enable_business_metrics,
            "async_log_queue_size": self.async_log_queue_size,
            "async_log_flush_interval": self.async_log_flush_interval,
            "mask_sensitive_data": self.mask_sensitive_data,
            "sensitive_field_patterns": self.sensitive_field_patterns,
            "enable_remote_logging": self.enable_remote_logging,
            "remote_endpoint": self.remote_endpoint,
            "enable_correlation_tracking": self.enable_correlation_tracking,
            "correlation_id_header": self.correlation_id_header,
            "enable_request_tracing": self.enable_request_tracing,
        }

    def ensure_log_directory(self) -> None:
        """Ensure the log directory exists."""
        if self.enable_file_logging and self.log_file_path:
            log_path = Path(self.log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

    def get_debug_modules(self) -> list[str]:
        """Get list of modules for debug logging."""
        if not self.debug_enabled:
            return []

        if not self.verbose_modules:
            # Default debug modules
            return [
                "maverick_core",
                "maverick_data",
                "maverick_backtest",
                "maverick_agents",
                "maverick_india",
                "maverick_server",
            ]

        return self.verbose_modules

    def should_log_performance(self, duration_ms: float) -> bool:
        """Check if operation should be logged based on performance threshold."""
        if not self.enable_performance_logging:
            return False
        return duration_ms >= self.performance_log_threshold_ms

    def get_log_file_config(self) -> dict[str, Any]:
        """Get file logging configuration."""
        if not self.enable_file_logging:
            return {}

        config: dict[str, Any] = {
            "filename": self.log_file_path,
            "mode": "a",
            "encoding": "utf-8",
        }

        if self.enable_log_rotation:
            config.update(
                {
                    "maxBytes": self.max_log_size_mb * 1024 * 1024,
                    "backupCount": self.backup_count,
                }
            )

        return config

    def get_performance_config(self) -> dict[str, Any]:
        """Get performance monitoring configuration."""
        return {
            "enabled": self.enable_performance_logging,
            "threshold_ms": self.performance_log_threshold_ms,
            "resource_tracking": self.enable_resource_tracking,
            "business_metrics": self.enable_business_metrics,
        }

    def get_debug_config(self) -> dict[str, Any]:
        """Get debug configuration."""
        return {
            "enabled": self.debug_enabled,
            "verbose_modules": self.get_debug_modules(),
            "log_request_response": self.log_request_response,
            "max_payload_length": self.max_payload_length,
        }


class EnvironmentLogSettings:
    """Environment-specific logging configurations."""

    @staticmethod
    def development() -> LoggingSettings:
        """Development environment logging configuration."""
        return LoggingSettings(
            log_level="DEBUG",
            log_format="text",
            debug_enabled=True,
            log_request_response=True,
            enable_performance_logging=True,
            performance_log_threshold_ms=100.0,  # Lower threshold for development
            console_output="stdout",
            enable_file_logging=True,
            log_file_path="logs/dev_maverick.log",
        )

    @staticmethod
    def testing() -> LoggingSettings:
        """Testing environment logging configuration."""
        return LoggingSettings(
            log_level="WARNING",
            log_format="text",
            debug_enabled=False,
            enable_performance_logging=False,
            enable_file_logging=False,
            console_output="stdout",
            enable_async_logging=False,  # Synchronous for tests
        )

    @staticmethod
    def production() -> LoggingSettings:
        """Production environment logging configuration."""
        return LoggingSettings(
            log_level="INFO",
            log_format="json",
            debug_enabled=False,
            log_request_response=False,
            enable_performance_logging=True,
            performance_log_threshold_ms=2000.0,  # Higher threshold for production
            console_output="stderr",
            enable_file_logging=True,
            log_file_path="/var/log/maverick/app.log",
            enable_log_rotation=True,
            max_log_size_mb=50,  # Larger files in production
            backup_count=10,
            enable_remote_logging=True,  # Enable for log aggregation
        )


# Global logging settings instance
_logging_settings: LoggingSettings | None = None


def get_logging_settings() -> LoggingSettings:
    """
    Get global logging settings instance.

    Creates settings based on MAVERICK_ENVIRONMENT variable:
    - development: Debug-friendly text logging
    - testing: Minimal logging for test isolation
    - production: JSON logging with file rotation

    Returns:
        Configured LoggingSettings instance.
    """
    global _logging_settings

    if _logging_settings is None:
        environment = os.getenv("MAVERICK_ENVIRONMENT", "development").lower()

        if environment == "development":
            _logging_settings = EnvironmentLogSettings.development()
        elif environment == "testing":
            _logging_settings = EnvironmentLogSettings.testing()
        elif environment == "production":
            _logging_settings = EnvironmentLogSettings.production()
        else:
            # Default to environment variables
            _logging_settings = LoggingSettings.from_env()

        # Override with any explicit environment variables
        env_overrides = LoggingSettings.from_env()
        default_settings = LoggingSettings()
        for key, value in env_overrides.to_dict().items():
            if value is not None and value != getattr(default_settings, key):
                setattr(_logging_settings, key, value)

        # Ensure log directory exists
        _logging_settings.ensure_log_directory()

    return _logging_settings


def configure_logging_for_environment(environment: str) -> LoggingSettings:
    """
    Configure logging for specific environment.

    Args:
        environment: Environment name ("development", "testing", "production")

    Returns:
        Configured LoggingSettings for the environment.

    Raises:
        ValueError: If environment is not recognized.
    """
    global _logging_settings

    if environment.lower() == "development":
        _logging_settings = EnvironmentLogSettings.development()
    elif environment.lower() == "testing":
        _logging_settings = EnvironmentLogSettings.testing()
    elif environment.lower() == "production":
        _logging_settings = EnvironmentLogSettings.production()
    else:
        raise ValueError(f"Unknown environment: {environment}")

    _logging_settings.ensure_log_directory()
    return _logging_settings


def reset_logging_settings() -> None:
    """Reset global logging settings (useful for testing)."""
    global _logging_settings
    _logging_settings = None


def validate_logging_settings(settings: LoggingSettings) -> list[str]:
    """
    Validate logging settings and return list of warnings/errors.

    Args:
        settings: LoggingSettings to validate

    Returns:
        List of warning/error messages (empty if valid).
    """
    warnings = []

    # Validate log level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if settings.log_level not in valid_levels:
        warnings.append(f"Invalid log level '{settings.log_level}', using INFO")

    # Validate log format
    valid_formats = ["json", "text"]
    if settings.log_format not in valid_formats:
        warnings.append(f"Invalid log format '{settings.log_format}', using json")

    # Validate console output
    valid_outputs = ["stdout", "stderr"]
    if settings.console_output not in valid_outputs:
        warnings.append(
            f"Invalid console output '{settings.console_output}', using stderr"
        )

    # Validate file logging
    if settings.enable_file_logging:
        try:
            log_path = Path(settings.log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            warnings.append(f"Cannot create log directory: {e}")

    # Validate performance settings
    if settings.performance_log_threshold_ms < 0:
        warnings.append("Performance threshold cannot be negative, using 1000ms")

    # Validate async settings
    if settings.async_log_queue_size < 100:
        warnings.append("Async log queue size too small, using 1000")

    return warnings


def _env_bool(key: str, default: bool) -> bool:
    """Get boolean from environment variable."""
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() == "true"

