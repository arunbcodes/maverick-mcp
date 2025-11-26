"""
Maverick Core Exceptions.

This module defines the exception hierarchy for all Maverick packages.
All exceptions inherit from MaverickError for easy catching.
"""


class MaverickError(Exception):
    """Base exception for all Maverick errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class ValidationError(MaverickError):
    """Error in input validation."""

    pass


class StockDataError(MaverickError):
    """Error fetching or processing stock data."""

    pass


class SymbolNotFoundError(StockDataError):
    """Stock symbol not found."""

    pass


class DataProviderError(StockDataError):
    """Error from data provider (Yahoo Finance, Tiingo, etc.)."""

    pass


class DataValidationError(StockDataError):
    """Invalid data received from provider."""

    pass


class TechnicalAnalysisError(MaverickError):
    """Error in technical analysis calculations."""

    pass


class CacheError(MaverickError):
    """Error in cache operations."""

    pass


class PersistenceError(MaverickError):
    """Error in database operations."""

    pass


class DatabaseError(PersistenceError):
    """Database connection or query error."""

    pass


class StrategyError(MaverickError):
    """Error in trading strategy."""

    pass


class LLMError(MaverickError):
    """Error in LLM operations."""

    pass


class AgentError(MaverickError):
    """Error in agent operations."""

    pass


class BacktestError(MaverickError):
    """Error in backtesting operations."""

    pass


class ConfigurationError(MaverickError):
    """Error in configuration."""

    pass


class RateLimitError(MaverickError):
    """Rate limit exceeded."""

    pass


class CircuitBreakerError(MaverickError):
    """Circuit breaker is open."""

    pass


__all__ = [
    "MaverickError",
    "ValidationError",
    "StockDataError",
    "SymbolNotFoundError",
    "DataProviderError",
    "DataValidationError",
    "TechnicalAnalysisError",
    "CacheError",
    "PersistenceError",
    "DatabaseError",
    "StrategyError",
    "LLMError",
    "AgentError",
    "BacktestError",
    "ConfigurationError",
    "RateLimitError",
    "CircuitBreakerError",
]
