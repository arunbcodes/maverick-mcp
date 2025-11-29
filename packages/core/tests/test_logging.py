"""
Tests for the logging module.
"""

import json
import logging
from unittest.mock import patch

import pytest

from maverick_core.logging import (
    CorrelationIDMiddleware,
    EnvironmentLogSettings,
    ErrorLogger,
    LoggingSettings,
    StructuredFormatter,
    TextFormatter,
    configure_logging_for_environment,
    get_correlation_id,
    get_logger,
    get_logging_settings,
    set_correlation_id,
    setup_logging,
    validate_logging_settings,
    with_correlation_id,
)
from maverick_core.logging.correlation import CorrelationContext
from maverick_core.logging.settings import reset_logging_settings


class TestCorrelationID:
    """Test correlation ID management."""

    def setup_method(self):
        CorrelationIDMiddleware.clear_correlation_id()

    def test_generate_correlation_id(self):
        corr_id = CorrelationIDMiddleware.generate_correlation_id()
        assert corr_id.startswith("mcp-")
        assert len(corr_id) == 12  # "mcp-" + 8 hex chars

    def test_set_and_get_correlation_id(self):
        # Set custom ID
        set_correlation_id("test-123")
        assert get_correlation_id() == "test-123"

        # Set None generates new ID
        new_id = set_correlation_id(None)
        assert new_id.startswith("mcp-")
        assert get_correlation_id() == new_id

    def test_clear_correlation_id(self):
        set_correlation_id("test-456")
        CorrelationIDMiddleware.clear_correlation_id()
        assert get_correlation_id() is None

    def test_with_correlation_id_decorator_sync(self):
        CorrelationIDMiddleware.clear_correlation_id()

        @with_correlation_id
        def my_func():
            return get_correlation_id()

        result = my_func()
        assert result is not None
        assert result.startswith("mcp-")

    @pytest.mark.asyncio
    async def test_with_correlation_id_decorator_async(self):
        CorrelationIDMiddleware.clear_correlation_id()

        @with_correlation_id
        async def async_func():
            return get_correlation_id()

        result = await async_func()
        assert result is not None
        assert result.startswith("mcp-")

    def test_correlation_context(self):
        CorrelationIDMiddleware.clear_correlation_id()

        with CorrelationContext("custom-id") as corr_id:
            assert corr_id == "custom-id"
            assert get_correlation_id() == "custom-id"

        # Context should be cleared after exiting
        # (or reset to previous value if there was one)


class TestStructuredFormatter:
    """Test structured JSON logging formatter."""

    def test_format_basic_message(self):
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert data["module"] == "test"
        assert data["line"] == 10
        assert "timestamp" in data

    def test_format_with_extra_fields(self):
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.user_id = "123"
        record.request_id = "abc"

        output = formatter.format(record)
        data = json.loads(output)

        assert data["user_id"] == "123"
        assert data["request_id"] == "abc"

    def test_format_with_exception(self):
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert data["exception"]["message"] == "Test error"
        assert isinstance(data["exception"]["traceback"], list)


class TestTextFormatter:
    """Test human-readable text formatter."""

    def test_format_basic_message(self):
        formatter = TextFormatter(use_colors=False)
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        assert "INFO" in output
        assert "test.logger" in output
        assert "Test message" in output


class TestLoggingSettings:
    """Test logging configuration settings."""

    def setup_method(self):
        reset_logging_settings()

    def test_default_settings(self):
        settings = LoggingSettings()

        assert settings.log_level == "INFO"
        assert settings.log_format == "json"
        assert settings.enable_file_logging is True

    def test_from_env(self):
        with patch.dict("os.environ", {
            "MAVERICK_LOG_LEVEL": "DEBUG",
            "MAVERICK_LOG_FORMAT": "text",
            "MAVERICK_FILE_LOGGING": "false",
        }):
            settings = LoggingSettings.from_env()

            assert settings.log_level == "DEBUG"
            assert settings.log_format == "text"
            assert settings.enable_file_logging is False

    def test_to_dict(self):
        settings = LoggingSettings(log_level="WARNING")
        data = settings.to_dict()

        assert data["log_level"] == "WARNING"
        assert isinstance(data, dict)

    def test_should_log_performance(self):
        settings = LoggingSettings(
            enable_performance_logging=True,
            performance_log_threshold_ms=1000.0,
        )

        assert settings.should_log_performance(1500.0) is True
        assert settings.should_log_performance(500.0) is False

    def test_should_log_performance_disabled(self):
        settings = LoggingSettings(enable_performance_logging=False)

        assert settings.should_log_performance(5000.0) is False


class TestEnvironmentLogSettings:
    """Test environment-specific logging configurations."""

    def test_development_settings(self):
        settings = EnvironmentLogSettings.development()

        assert settings.log_level == "DEBUG"
        assert settings.log_format == "text"
        assert settings.debug_enabled is True

    def test_testing_settings(self):
        settings = EnvironmentLogSettings.testing()

        assert settings.log_level == "WARNING"
        assert settings.enable_performance_logging is False
        assert settings.enable_file_logging is False

    def test_production_settings(self):
        settings = EnvironmentLogSettings.production()

        assert settings.log_level == "INFO"
        assert settings.log_format == "json"
        assert settings.debug_enabled is False


class TestValidateLoggingSettings:
    """Test logging settings validation."""

    def test_valid_settings(self):
        settings = LoggingSettings()
        warnings = validate_logging_settings(settings)

        assert len(warnings) == 0

    def test_invalid_log_level(self):
        settings = LoggingSettings(log_level="INVALID")
        warnings = validate_logging_settings(settings)

        assert any("Invalid log level" in w for w in warnings)

    def test_invalid_log_format(self):
        settings = LoggingSettings(log_format="xml")
        warnings = validate_logging_settings(settings)

        assert any("Invalid log format" in w for w in warnings)


class TestConfigureLogging:
    """Test logging configuration functions."""

    def setup_method(self):
        reset_logging_settings()

    def test_configure_for_development(self):
        settings = configure_logging_for_environment("development")

        assert settings.log_level == "DEBUG"
        assert settings.debug_enabled is True

    def test_configure_for_testing(self):
        settings = configure_logging_for_environment("testing")

        assert settings.log_level == "WARNING"

    def test_configure_for_production(self):
        settings = configure_logging_for_environment("production")

        assert settings.log_level == "INFO"
        assert settings.log_format == "json"

    def test_configure_for_unknown_environment(self):
        with pytest.raises(ValueError) as exc_info:
            configure_logging_for_environment("unknown")

        assert "Unknown environment" in str(exc_info.value)


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_with_defaults(self):
        logger = setup_logging()

        assert logger is not None
        assert logger.level == logging.INFO

    def test_setup_with_custom_level(self):
        logger = setup_logging(level="DEBUG")

        assert logger.level == logging.DEBUG

    def test_setup_with_text_format(self):
        logger = setup_logging(use_json=False)

        # Check handler formatter type
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, TextFormatter)


class TestErrorLogger:
    """Test error logger functionality."""

    def test_log_error(self):
        base_logger = logging.getLogger("test.error_logger")
        error_logger = ErrorLogger(base_logger)

        with patch.object(base_logger, "log") as mock_log:
            try:
                raise ValueError("Test error")
            except ValueError as e:
                error_logger.log_error(e, {"request_id": "123"})

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == logging.ERROR
            assert "ValueError: Test error" in call_args[0][1]

    def test_error_stats(self):
        base_logger = logging.getLogger("test.error_stats")
        error_logger = ErrorLogger(base_logger)

        with patch.object(base_logger, "log"):
            error_logger.log_error(ValueError("Error 1"), {})
            error_logger.log_error(ValueError("Error 2"), {})
            error_logger.log_error(TypeError("Error 3"), {})

        stats = error_logger.get_error_stats()
        assert stats["ValueError"] == 2
        assert stats["TypeError"] == 1

    def test_sensitive_data_masking(self):
        base_logger = logging.getLogger("test.masking")
        error_logger = ErrorLogger(base_logger)

        context = {
            "user_id": "123",
            "password": "secret123",
            "api_key": "key-abc-123",
            "normal_field": "visible",
        }

        masked = error_logger._mask_sensitive_data(context)

        assert masked["user_id"] == "123"
        assert masked["password"] == "***MASKED***"
        assert masked["api_key"] == "***MASKED***"
        assert masked["normal_field"] == "visible"

    def test_get_logger_helper(self):
        logger = get_logger("test.helper")

        assert logger is not None
        assert logger.name == "test.helper"

