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
from maverick_services.screening_service import (
    ScreeningService,
    InvestorPersona as ScreeningPersona,
    PERSONA_CONFIG,
)
from maverick_services.auth import UserService, PasswordHasher
from maverick_services.ai_screening_service import (
    AIScreeningService,
    ExplanationRequest,
    StockExplanation,
    InvestorPersona,
    ConfidenceLevel,
    get_ai_screening_service,
)
from maverick_services.nl_screening_service import (
    NLScreeningService,
    ParsedQuery,
    QueryIntent,
    QuerySuggestion,
    EXAMPLE_QUERIES,
    get_nl_screening_service,
)
from maverick_services.thesis_service import (
    ThesisGeneratorService,
    InvestmentThesis,
    ThesisSection,
    ThesisRating,
    RiskLevel,
    get_thesis_service,
)
from maverick_services.alert_service import (
    AlertService,
    Alert,
    AlertRule,
    AlertType,
    AlertPriority,
    AlertStatus,
    get_alert_service,
    PRESET_RULES,
)
from maverick_services.watchlist_service import (
    WatchlistService,
    Watchlist,
    WatchlistItem,
    get_watchlist_service,
)
from maverick_services.custom_screener_service import (
    CustomScreenerService,
    CustomScreener,
    FilterCondition,
    FilterField,
    FilterOperator,
    ScreenerResult,
    get_custom_screener_service,
    PRESET_SCREENERS,
    FILTER_FIELD_METADATA,
)
from maverick_services.exceptions import (
    ServiceError,
    ServiceException,
    NotFoundError,
    ConflictError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
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
    "UserService",
    "PasswordHasher",
    # AI Services
    "AIScreeningService",
    "ExplanationRequest",
    "StockExplanation",
    "InvestorPersona",
    "ConfidenceLevel",
    "get_ai_screening_service",
    # Natural Language Services
    "NLScreeningService",
    "ParsedQuery",
    "QueryIntent",
    "QuerySuggestion",
    "EXAMPLE_QUERIES",
    "get_nl_screening_service",
    # Thesis Services
    "ThesisGeneratorService",
    "InvestmentThesis",
    "ThesisSection",
    "ThesisRating",
    "RiskLevel",
    "get_thesis_service",
    # Alert Services
    "AlertService",
    "Alert",
    "AlertRule",
    "AlertType",
    "AlertPriority",
    "AlertStatus",
    "get_alert_service",
    "PRESET_RULES",
    # Watchlist Services
    "WatchlistService",
    "Watchlist",
    "WatchlistItem",
    "get_watchlist_service",
    # Custom Screener Services
    "CustomScreenerService",
    "CustomScreener",
    "FilterCondition",
    "FilterField",
    "FilterOperator",
    "ScreenerResult",
    "get_custom_screener_service",
    "PRESET_SCREENERS",
    "FILTER_FIELD_METADATA",
    # Base exceptions
    "ServiceError",
    "ServiceException",
    # Generic exceptions
    "NotFoundError",
    "ConflictError",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    # Domain-specific exceptions
    "StockNotFoundError",
    "InsufficientDataError",
    "PortfolioNotFoundError",
    "PositionNotFoundError",
]

