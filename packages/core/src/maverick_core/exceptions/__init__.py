"""
Maverick Core Exceptions.

This module defines the exception hierarchy for all Maverick packages.
All exceptions inherit from MaverickError for easy catching.

Features:
- Error codes for programmatic handling
- HTTP status codes for API responses
- Serialization to dict for API responses
- Context information for debugging
"""

from typing import Any


class MaverickError(Exception):
    """
    Base exception for all Maverick errors.
    
    Provides error codes, HTTP status codes, and context information.
    """

    error_code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        field: str | None = None,
        recoverable: bool = True,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.error_code
        self.status_code = status_code or self.__class__.status_code
        self.details = details or {}
        self.context = context or {}
        self.field = field
        self.recoverable = recoverable

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.message}', code='{self.error_code}')"

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        result: dict[str, Any] = {
            "code": self.error_code,
            "message": self.message,
        }
        if self.field:
            result["field"] = self.field
        if self.context:
            result["context"] = self.context
        if self.details:
            result["details"] = self.details
        return result


class ValidationError(MaverickError):
    """Error in input validation."""

    error_code = "VALIDATION_ERROR"
    status_code = 400


class ParameterValidationError(ValidationError):
    """Raised when function parameters are invalid."""

    error_code = "PARAMETER_VALIDATION_ERROR"
    status_code = 400

    def __init__(
        self,
        param_name: str,
        expected_type: str,
        actual_type: str,
        **kwargs,
    ):
        reason = f"Expected {expected_type}, got {actual_type}"
        message = f"Validation failed for '{param_name}': {reason}"
        super().__init__(message, field=param_name, **kwargs)
        self.context["expected_type"] = expected_type
        self.context["actual_type"] = actual_type


class StockDataError(MaverickError):
    """Error fetching or processing stock data."""

    error_code = "STOCK_DATA_ERROR"
    status_code = 500


class SymbolNotFoundError(StockDataError):
    """Stock symbol not found."""

    error_code = "SYMBOL_NOT_FOUND"
    status_code = 404


class DataProviderError(MaverickError):
    """Error from data provider (Yahoo Finance, Tiingo, etc.)."""

    error_code = "DATA_PROVIDER_ERROR"
    status_code = 503

    def __init__(self, provider: str, message: str, **kwargs):
        super().__init__(message, **kwargs)
        self.context["provider"] = provider


class DataNotFoundError(DataProviderError):
    """Raised when requested data is not found."""

    error_code = "DATA_NOT_FOUND"
    status_code = 404

    def __init__(
        self,
        symbol: str | None = None,
        date_range: tuple | None = None,
        message: str | None = None,
        **kwargs,
    ):
        if message is None:
            message = f"Data not found for symbol '{symbol}'" if symbol else "Data not found"
            if date_range:
                message += f" in range {date_range[0]} to {date_range[1]}"
        super().__init__("cache", message, **kwargs)
        if symbol:
            self.context["symbol"] = symbol
        if date_range:
            self.context["date_range"] = date_range


class DataValidationError(StockDataError):
    """Invalid data received from provider."""

    error_code = "DATA_VALIDATION_ERROR"
    status_code = 422


class TechnicalAnalysisError(MaverickError):
    """Error in technical analysis calculations."""

    error_code = "TECHNICAL_ANALYSIS_ERROR"
    status_code = 500


class CacheError(MaverickError):
    """Error in cache operations."""

    error_code = "CACHE_ERROR"
    status_code = 503

    def __init__(self, operation: str, message: str, **kwargs):
        super().__init__(message, **kwargs)
        self.context["operation"] = operation


class CacheConnectionError(CacheError):
    """Raised when cache connection fails."""

    error_code = "CACHE_CONNECTION_ERROR"
    status_code = 503

    def __init__(self, cache_type: str, reason: str, **kwargs):
        message = f"{cache_type} cache connection failed: {reason}"
        super().__init__("connect", message, recoverable=True, **kwargs)
        self.context["cache_type"] = cache_type


class PersistenceError(MaverickError):
    """Error in database operations."""

    error_code = "PERSISTENCE_ERROR"
    status_code = 500


class DatabaseError(PersistenceError):
    """Database connection or query error."""

    error_code = "DATABASE_ERROR"
    status_code = 500

    def __init__(self, operation: str, message: str, **kwargs):
        super().__init__(message, **kwargs)
        self.context["operation"] = operation


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    error_code = "DATABASE_CONNECTION_ERROR"
    status_code = 503

    def __init__(self, reason: str, **kwargs):
        message = f"Database connection failed: {reason}"
        super().__init__("connect", message, recoverable=True, **kwargs)


class DataIntegrityError(DatabaseError):
    """Raised when data integrity check fails."""

    error_code = "DATA_INTEGRITY_ERROR"
    status_code = 422

    def __init__(
        self,
        message: str,
        table: str | None = None,
        constraint: str | None = None,
        **kwargs,
    ):
        super().__init__("integrity_check", message, recoverable=False, **kwargs)
        if table:
            self.context["table"] = table
        if constraint:
            self.context["constraint"] = constraint


class StrategyError(MaverickError):
    """Error in trading strategy."""

    error_code = "STRATEGY_ERROR"
    status_code = 500


class LLMError(MaverickError):
    """Error in LLM operations."""

    error_code = "LLM_ERROR"
    status_code = 500


class AgentError(MaverickError):
    """Error in agent operations."""

    error_code = "AGENT_ERROR"
    status_code = 500


class AgentInitializationError(AgentError):
    """Raised when agent initialization fails."""

    error_code = "AGENT_INIT_ERROR"
    status_code = 500

    def __init__(self, agent_type: str, reason: str, **kwargs):
        message = f"Failed to initialize {agent_type}: {reason}"
        super().__init__(message, **kwargs)
        self.context["agent_type"] = agent_type
        self.context["reason"] = reason


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""

    error_code = "AGENT_EXECUTION_ERROR"
    status_code = 500


class BacktestError(MaverickError):
    """Error in backtesting operations."""

    error_code = "BACKTEST_ERROR"
    status_code = 500


class ConfigurationError(MaverickError):
    """Error in configuration."""

    error_code = "CONFIGURATION_ERROR"
    status_code = 500

    def __init__(self, message: str, config_key: str | None = None, **kwargs):
        super().__init__(message, **kwargs)
        if config_key:
            self.context["config_key"] = config_key


class RateLimitError(MaverickError):
    """Rate limit exceeded."""

    error_code = "RATE_LIMIT_EXCEEDED"
    status_code = 429

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        if retry_after:
            self.context["retry_after"] = retry_after


class APIRateLimitError(DataProviderError, RateLimitError):
    """Raised when API rate limit is exceeded."""

    error_code = "API_RATE_LIMIT_EXCEEDED"
    status_code = 429

    def __init__(self, provider: str, retry_after: int | None = None, **kwargs):
        message = f"Rate limit exceeded for {provider}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super(DataProviderError, self).__init__(message, recoverable=True, **kwargs)
        self.context["provider"] = provider
        if retry_after:
            self.context["retry_after"] = retry_after


class CircuitBreakerError(MaverickError):
    """Circuit breaker is open."""

    error_code = "CIRCUIT_BREAKER_OPEN"
    status_code = 503

    def __init__(
        self,
        service: str,
        failure_count: int | None = None,
        threshold: int | None = None,
        **kwargs,
    ):
        message = f"Circuit breaker open for {service}"
        if failure_count and threshold:
            message = f"Circuit breaker open for {service}: {failure_count}/{threshold} failures"
        super().__init__(message, recoverable=True, **kwargs)
        self.context["service"] = service
        if failure_count:
            self.context["failure_count"] = failure_count
        if threshold:
            self.context["threshold"] = threshold


class ExternalServiceError(MaverickError):
    """Raised when an external service fails."""

    error_code = "EXTERNAL_SERVICE_ERROR"
    status_code = 503

    def __init__(
        self,
        service: str,
        message: str,
        original_error: str | None = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.context["service"] = service
        if original_error:
            self.context["original_error"] = original_error


class APIConnectionError(ExternalServiceError):
    """Raised when API connection fails."""

    error_code = "API_CONNECTION_ERROR"
    status_code = 503

    def __init__(self, provider: str, endpoint: str, reason: str, **kwargs):
        message = f"Failed to connect to {provider} at {endpoint}: {reason}"
        super().__init__(provider, message, recoverable=True, **kwargs)
        self.context["endpoint"] = endpoint
        self.context["connection_reason"] = reason


class AuthenticationError(MaverickError):
    """Raised when authentication fails."""

    error_code = "AUTHENTICATION_ERROR"
    status_code = 401

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, **kwargs)


class AuthorizationError(MaverickError):
    """Raised when authorization fails."""

    error_code = "AUTHORIZATION_ERROR"
    status_code = 403

    def __init__(
        self,
        message: str = "Insufficient permissions",
        resource: str | None = None,
        action: str | None = None,
        **kwargs,
    ):
        if resource and action:
            message = f"Unauthorized access to {resource} for action '{action}'"
        super().__init__(message, **kwargs)
        if resource:
            self.context["resource"] = resource
        if action:
            self.context["action"] = action


class NotFoundError(MaverickError):
    """Raised when a requested resource is not found."""

    error_code = "NOT_FOUND"
    status_code = 404

    def __init__(self, resource: str, identifier: str | None = None, **kwargs):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, **kwargs)
        self.context["resource"] = resource
        if identifier:
            self.context["identifier"] = identifier


class ConflictError(MaverickError):
    """Raised when there's a conflict with existing data."""

    error_code = "CONFLICT"
    status_code = 409

    def __init__(self, message: str, field: str | None = None, **kwargs):
        super().__init__(message, field=field, **kwargs)


class ResearchError(MaverickError):
    """Raised when research operations fail."""

    error_code = "RESEARCH_ERROR"
    status_code = 500

    def __init__(
        self,
        message: str,
        research_type: str | None = None,
        provider: str | None = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.research_type = research_type
        self.provider = provider
        if research_type:
            self.context["research_type"] = research_type
        if provider:
            self.context["provider"] = provider


class WebSearchError(ResearchError):
    """Raised when web search operations fail."""

    error_code = "WEB_SEARCH_ERROR"


class ContentAnalysisError(ResearchError):
    """Raised when content analysis fails."""

    error_code = "CONTENT_ANALYSIS_ERROR"


class WebhookError(MaverickError):
    """Raised when webhook processing fails."""

    error_code = "WEBHOOK_ERROR"
    status_code = 400

    def __init__(
        self,
        message: str,
        event_type: str | None = None,
        event_id: str | None = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        if event_type:
            self.context["event_type"] = event_type
        if event_id:
            self.context["event_id"] = event_id


class PersonaConfigurationError(MaverickError):
    """Raised when persona configuration is invalid."""

    error_code = "PERSONA_CONFIG_ERROR"
    status_code = 400

    def __init__(self, persona: str, valid_personas: list, **kwargs):
        message = (
            f"Invalid persona '{persona}'. Valid options: {', '.join(valid_personas)}"
        )
        super().__init__(message, **kwargs)
        self.context["invalid_persona"] = persona
        self.context["valid_personas"] = valid_personas


class ToolRegistrationError(MaverickError):
    """Raised when tool registration fails."""

    error_code = "TOOL_REGISTRATION_ERROR"
    status_code = 500

    def __init__(self, tool_name: str, reason: str, **kwargs):
        message = f"Failed to register tool '{tool_name}': {reason}"
        super().__init__(message, **kwargs)
        self.context["tool_name"] = tool_name
        self.context["reason"] = reason


# Error code constants for documentation
ERROR_CODES = {
    "VALIDATION_ERROR": "Request validation failed",
    "PARAMETER_VALIDATION_ERROR": "Invalid parameter",
    "AUTHENTICATION_ERROR": "Authentication failed",
    "AUTHORIZATION_ERROR": "Insufficient permissions",
    "NOT_FOUND": "Resource not found",
    "CONFLICT": "Resource conflict",
    "RATE_LIMIT_EXCEEDED": "Too many requests",
    "API_RATE_LIMIT_EXCEEDED": "API rate limit exceeded",
    "EXTERNAL_SERVICE_ERROR": "External service unavailable",
    "DATA_PROVIDER_ERROR": "Data provider error",
    "DATA_NOT_FOUND": "Data not found",
    "API_CONNECTION_ERROR": "API connection failed",
    "DATABASE_ERROR": "Database error",
    "DATABASE_CONNECTION_ERROR": "Database connection failed",
    "DATA_INTEGRITY_ERROR": "Data integrity violation",
    "CACHE_ERROR": "Cache error",
    "CACHE_CONNECTION_ERROR": "Cache connection failed",
    "CONFIGURATION_ERROR": "Configuration error",
    "WEBHOOK_ERROR": "Webhook processing failed",
    "AGENT_INIT_ERROR": "Agent initialization failed",
    "AGENT_EXECUTION_ERROR": "Agent execution failed",
    "PERSONA_CONFIG_ERROR": "Invalid persona configuration",
    "TOOL_REGISTRATION_ERROR": "Tool registration failed",
    "CIRCUIT_BREAKER_OPEN": "Service unavailable - circuit breaker open",
    "INTERNAL_ERROR": "Internal server error",
    "RESEARCH_ERROR": "Research operation failed",
    "WEB_SEARCH_ERROR": "Web search failed",
    "CONTENT_ANALYSIS_ERROR": "Content analysis failed",
    "STRATEGY_ERROR": "Strategy error",
    "BACKTEST_ERROR": "Backtest error",
    "LLM_ERROR": "LLM error",
}


def get_error_message(code: str) -> str:
    """Get human-readable message for error code."""
    return ERROR_CODES.get(code, "Unknown error")


# Backward compatibility aliases
MaverickException = MaverickError
MaverickMCPError = MaverickError


__all__ = [
    # Base
    "MaverickError",
    "MaverickException",
    "MaverickMCPError",
    # Validation
    "ValidationError",
    "ParameterValidationError",
    # Stock Data
    "StockDataError",
    "SymbolNotFoundError",
    "DataProviderError",
    "DataNotFoundError",
    "DataValidationError",
    # Technical Analysis
    "TechnicalAnalysisError",
    # Cache
    "CacheError",
    "CacheConnectionError",
    # Database
    "PersistenceError",
    "DatabaseError",
    "DatabaseConnectionError",
    "DataIntegrityError",
    # Strategy/Backtest
    "StrategyError",
    "BacktestError",
    # LLM/Agent
    "LLMError",
    "AgentError",
    "AgentInitializationError",
    "AgentExecutionError",
    # Configuration
    "ConfigurationError",
    # Rate Limiting
    "RateLimitError",
    "APIRateLimitError",
    # Circuit Breaker
    "CircuitBreakerError",
    # External Services
    "ExternalServiceError",
    "APIConnectionError",
    # Auth
    "AuthenticationError",
    "AuthorizationError",
    # Resource
    "NotFoundError",
    "ConflictError",
    # Research
    "ResearchError",
    "WebSearchError",
    "ContentAnalysisError",
    # Miscellaneous
    "WebhookError",
    "PersonaConfigurationError",
    "ToolRegistrationError",
    # Utilities
    "ERROR_CODES",
    "get_error_message",
]
