"""
Maverick Services Package.

Shared domain services for MaverickMCP. This package provides the business logic
layer used by both the MCP server and REST API.

Features:
- Protocol-agnostic services (MCP and REST use the same logic)
- Dependency injection support
- Schema-first design (uses maverick-schemas models)
"""

from maverick_services.stock_service import StockService
from maverick_services.technical_service import TechnicalService
from maverick_services.portfolio_service import PortfolioService
from maverick_services.screening_service import ScreeningService
from maverick_services.exceptions import (
    ServiceError,
    StockNotFoundError,
    InsufficientDataError,
    PortfolioNotFoundError,
    PositionNotFoundError,
)

__all__ = [
    # Services
    "StockService",
    "TechnicalService",
    "PortfolioService",
    "ScreeningService",
    # Exceptions
    "ServiceError",
    "StockNotFoundError",
    "InsufficientDataError",
    "PortfolioNotFoundError",
    "PositionNotFoundError",
]

