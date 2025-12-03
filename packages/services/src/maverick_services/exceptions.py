"""
Service-specific exceptions.

These exceptions are raised by services and can be caught by both MCP and REST handlers.
"""

from maverick_core.exceptions import MaverickError


class ServiceError(MaverickError):
    """Base exception for service layer errors."""

    error_code = "SERVICE_ERROR"
    status_code = 500


class StockNotFoundError(ServiceError):
    """Raised when a stock ticker is not found."""

    error_code = "STOCK_NOT_FOUND"
    status_code = 404

    def __init__(self, ticker: str, **kwargs):
        message = f"Stock not found: {ticker}"
        super().__init__(message, **kwargs)
        self.context["ticker"] = ticker


class InsufficientDataError(ServiceError):
    """Raised when there's not enough data for analysis."""

    error_code = "INSUFFICIENT_DATA"
    status_code = 422

    def __init__(self, ticker: str, required: int, actual: int, **kwargs):
        message = f"Insufficient data for {ticker}: need {required} data points, got {actual}"
        super().__init__(message, **kwargs)
        self.context["ticker"] = ticker
        self.context["required"] = required
        self.context["actual"] = actual


class PortfolioNotFoundError(ServiceError):
    """Raised when a portfolio is not found."""

    error_code = "PORTFOLIO_NOT_FOUND"
    status_code = 404

    def __init__(self, user_id: str, portfolio_name: str = "My Portfolio", **kwargs):
        message = f"Portfolio '{portfolio_name}' not found for user {user_id}"
        super().__init__(message, **kwargs)
        self.context["user_id"] = user_id
        self.context["portfolio_name"] = portfolio_name


class PositionNotFoundError(ServiceError):
    """Raised when a position is not found."""

    error_code = "POSITION_NOT_FOUND"
    status_code = 404

    def __init__(self, ticker: str, user_id: str, **kwargs):
        message = f"Position not found for {ticker}"
        super().__init__(message, **kwargs)
        self.context["ticker"] = ticker
        self.context["user_id"] = user_id


class ScreeningError(ServiceError):
    """Raised when screening fails."""

    error_code = "SCREENING_ERROR"
    status_code = 500


class BacktestError(ServiceError):
    """Raised when backtesting fails."""

    error_code = "BACKTEST_ERROR"
    status_code = 500


class ResearchError(ServiceError):
    """Raised when research fails."""

    error_code = "RESEARCH_ERROR"
    status_code = 500


__all__ = [
    "ServiceError",
    "StockNotFoundError",
    "InsufficientDataError",
    "PortfolioNotFoundError",
    "PositionNotFoundError",
    "ScreeningError",
    "BacktestError",
    "ResearchError",
]

