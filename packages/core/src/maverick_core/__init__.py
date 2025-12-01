"""
Maverick Core - Pure domain logic and interfaces for stock analysis.

This package contains:
- Domain entities and value objects (DDD patterns)
- Interface definitions (protocols) for all services
- Pure technical analysis functions
- Domain exceptions

Zero external dependencies on frameworks like SQLAlchemy, Redis, or LangChain.
"""

# Domain entities
from maverick_core.domain import Portfolio, Position

# Technical analysis functions
from maverick_core.technical import (
    calculate_atr,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_momentum,
    calculate_obv,
    calculate_rate_of_change,
    calculate_rsi,
    calculate_sma,
    calculate_stochastic,
    calculate_support_resistance,
    calculate_trend_strength,
    calculate_williams_r,
)

# Exceptions
from maverick_core.exceptions import (
    ERROR_CODES,
    AgentError,
    AgentExecutionError,
    AgentInitializationError,
    APIConnectionError,
    APIRateLimitError,
    AuthenticationError,
    AuthorizationError,
    BacktestError,
    CacheConnectionError,
    CacheError,
    CircuitBreakerError,
    ConfigurationError,
    ConflictError,
    ContentAnalysisError,
    DatabaseConnectionError,
    DatabaseError,
    DataIntegrityError,
    DataNotFoundError,
    DataProviderError,
    DataValidationError,
    ExternalServiceError,
    get_error_message,
    LLMError,
    MaverickError,
    MaverickException,
    NotFoundError,
    ParameterValidationError,
    PersistenceError,
    PersonaConfigurationError,
    RateLimitError,
    ResearchError,
    StockDataError,
    StrategyError,
    SymbolNotFoundError,
    TechnicalAnalysisError,
    ToolRegistrationError,
    ValidationError,
    WebhookError,
    WebSearchError,
)

# Interfaces
from maverick_core.interfaces import (
    IBacktestEngine,
    ICacheKeyGenerator,
    ICacheProvider,
    IConfigProvider,
    ILLMProvider,
    IMarketCalendar,
    IPortfolioRepository,
    IRepository,
    IResearchAgent,
    IScreeningRepository,
    IStockDataFetcher,
    IStockRepository,
    IStockScreener,
    IStrategy,
    ITechnicalAnalyzer,
    TaskType,
)

# Configuration (lazy import to avoid circular dependencies)
from maverick_core.config import (
    CACHE_TTL,
    CONFIG,
    Settings,
    get_settings,
)

# Validation
from maverick_core.validation import (
    BaseRequest,
    BaseResponse,
    DateRangeMixin,
    DateString,
    DateValidator,
    PaginationMixin,
    Percentage,
    PositiveFloat,
    PositiveInt,
    StrictBaseModel,
    TickerSymbol,
    TickerValidator,
    validate_currency_code,
    validate_date_range,
    validate_email,
    validate_in_range,
    validate_max_length,
    validate_min_length,
    validate_not_empty,
    validate_one_of,
    validate_percentage,
    validate_positive_number,
    validate_symbol,
    validate_url,
)

# Resilience
from maverick_core.resilience import (
    CIRCUIT_BREAKER_CONFIGS,
    CircuitBreakerConfig,
    CircuitBreakerManager,
    CircuitBreakerMetrics,
    CircuitState,
    EnhancedCircuitBreaker,
    FailureDetectionStrategy,
    FallbackChain,
    FallbackStrategy,
    circuit_breaker,
    circuit_breaker_method,
    get_all_circuit_breaker_status,
    get_all_circuit_breakers,
    get_circuit_breaker,
    get_circuit_breaker_manager,
    get_circuit_breaker_status,
    initialize_all_circuit_breakers,
    initialize_circuit_breakers,
    register_circuit_breaker,
    reset_all_circuit_breakers,
    with_async_circuit_breaker,
    with_circuit_breaker,
    with_http_circuit_breaker,
)

# Logging
from maverick_core.logging import (
    CorrelationIDMiddleware,
    EnvironmentLogSettings,
    ErrorLogger,
    LoggingSettings,
    StructuredFormatter,
    TextFormatter,
    configure_logging_for_environment,
    correlation_id_var,
    get_correlation_id,
    get_logger,
    get_logging_settings,
    set_correlation_id,
    setup_logging,
    validate_logging_settings,
    with_correlation_id,
)

# Decorators
from maverick_core.decorators import (
    handle_async_errors,
    handle_errors,
    handle_provider_errors,
    handle_repository_errors,
    handle_service_errors,
    safe_execute,
    safe_execute_async,
)

# HTTP Client
from maverick_core.http import (
    AsyncHTTPClient,
    close_http_client,
    get_http_client,
    http_client_context,
)

__version__ = "0.1.0"

__all__ = [
    # Domain entities
    "Portfolio",
    "Position",
    # Technical Analysis Functions
    "calculate_sma",
    "calculate_ema",
    "calculate_rsi",
    "calculate_stochastic",
    "calculate_williams_r",
    "calculate_macd",
    "calculate_trend_strength",
    "calculate_bollinger_bands",
    "calculate_atr",
    "calculate_momentum",
    "calculate_rate_of_change",
    "calculate_obv",
    "calculate_support_resistance",
    # Interfaces - Stock Data
    "IStockDataFetcher",
    "IStockScreener",
    # Interfaces - Cache
    "ICacheProvider",
    "ICacheKeyGenerator",
    # Interfaces - Persistence
    "IRepository",
    "IStockRepository",
    "IPortfolioRepository",
    "IScreeningRepository",
    # Interfaces - Technical Analysis
    "ITechnicalAnalyzer",
    # Interfaces - Market Calendar
    "IMarketCalendar",
    # Interfaces - LLM
    "ILLMProvider",
    "IResearchAgent",
    "TaskType",
    # Interfaces - Backtest
    "IBacktestEngine",
    "IStrategy",
    # Interfaces - Config
    "IConfigProvider",
    # Exceptions - Base
    "MaverickError",
    "MaverickException",
    # Exceptions - Validation
    "ValidationError",
    "ParameterValidationError",
    # Exceptions - Stock Data
    "StockDataError",
    "SymbolNotFoundError",
    "DataProviderError",
    "DataNotFoundError",
    "DataValidationError",
    # Exceptions - Technical Analysis
    "TechnicalAnalysisError",
    # Exceptions - Cache
    "CacheError",
    "CacheConnectionError",
    # Exceptions - Database
    "PersistenceError",
    "DatabaseError",
    "DatabaseConnectionError",
    "DataIntegrityError",
    # Exceptions - Strategy/Backtest
    "StrategyError",
    "BacktestError",
    # Exceptions - LLM/Agent
    "LLMError",
    "AgentError",
    "AgentInitializationError",
    "AgentExecutionError",
    # Exceptions - Configuration
    "ConfigurationError",
    # Exceptions - Rate Limiting
    "RateLimitError",
    "APIRateLimitError",
    # Exceptions - Circuit Breaker
    "CircuitBreakerError",
    # Exceptions - External Services
    "ExternalServiceError",
    "APIConnectionError",
    # Exceptions - Auth
    "AuthenticationError",
    "AuthorizationError",
    # Exceptions - Resource
    "NotFoundError",
    "ConflictError",
    # Exceptions - Research
    "ResearchError",
    "WebSearchError",
    "ContentAnalysisError",
    # Exceptions - Miscellaneous
    "WebhookError",
    "PersonaConfigurationError",
    "ToolRegistrationError",
    # Exceptions - Utilities
    "ERROR_CODES",
    "get_error_message",
    # Configuration
    "Settings",
    "get_settings",
    "CONFIG",
    "CACHE_TTL",
    # Validation - Type annotations
    "TickerSymbol",
    "DateString",
    "PositiveInt",
    "PositiveFloat",
    "Percentage",
    # Validation - Base models
    "StrictBaseModel",
    "BaseRequest",
    "BaseResponse",
    # Validation - Mixins
    "PaginationMixin",
    "DateRangeMixin",
    # Validation - Validator classes
    "TickerValidator",
    "DateValidator",
    # Validation - Utility functions
    "validate_symbol",
    "validate_date_range",
    "validate_positive_number",
    "validate_in_range",
    "validate_email",
    "validate_url",
    "validate_not_empty",
    "validate_min_length",
    "validate_max_length",
    "validate_one_of",
    "validate_percentage",
    "validate_currency_code",
    # Resilience - Enums
    "CircuitState",
    "FailureDetectionStrategy",
    # Resilience - Configuration
    "CircuitBreakerConfig",
    "CIRCUIT_BREAKER_CONFIGS",
    # Resilience - Core classes
    "EnhancedCircuitBreaker",
    "CircuitBreakerMetrics",
    "CircuitBreakerManager",
    # Resilience - Registry functions
    "register_circuit_breaker",
    "get_circuit_breaker",
    "get_all_circuit_breakers",
    "reset_all_circuit_breakers",
    "get_circuit_breaker_status",
    # Resilience - Initialization
    "initialize_circuit_breakers",
    "initialize_all_circuit_breakers",
    "get_circuit_breaker_manager",
    "get_all_circuit_breaker_status",
    # Resilience - Decorators
    "circuit_breaker",
    "with_circuit_breaker",
    "with_async_circuit_breaker",
    "with_http_circuit_breaker",
    "circuit_breaker_method",
    # Resilience - Fallback
    "FallbackStrategy",
    "FallbackChain",
    # Logging - Formatters
    "StructuredFormatter",
    "TextFormatter",
    # Logging - Configuration
    "setup_logging",
    "get_logger",
    "LoggingSettings",
    "EnvironmentLogSettings",
    "get_logging_settings",
    "configure_logging_for_environment",
    "validate_logging_settings",
    # Logging - Correlation
    "correlation_id_var",
    "CorrelationIDMiddleware",
    "with_correlation_id",
    "get_correlation_id",
    "set_correlation_id",
    # Logging - Error handling
    "ErrorLogger",
    # Decorators - Error handling
    "handle_errors",
    "handle_async_errors",
    "handle_provider_errors",
    "handle_repository_errors",
    "handle_service_errors",
    "safe_execute",
    "safe_execute_async",
    # HTTP Client
    "AsyncHTTPClient",
    "get_http_client",
    "close_http_client",
    "http_client_context",
    # Version
    "__version__",
]
