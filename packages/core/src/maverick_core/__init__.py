"""
Maverick Core - Pure domain logic and interfaces for stock analysis.

This package contains:
- Domain entities and value objects (DDD patterns)
- Interface definitions (protocols) for all services
- Pure technical analysis functions
- Domain exceptions

Zero external dependencies on frameworks like SQLAlchemy, Redis, or LangChain.
"""

from maverick_core.exceptions import (
    MaverickError,
    StockDataError,
    ValidationError,
    TechnicalAnalysisError,
)

__version__ = "0.1.0"

__all__ = [
    # Exceptions
    "MaverickError",
    "StockDataError",
    "ValidationError",
    "TechnicalAnalysisError",
    # Version
    "__version__",
]
