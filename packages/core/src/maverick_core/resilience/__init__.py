"""
Maverick Core Resilience Module.

This module provides resilience patterns for handling failures gracefully:
- Circuit breaker: Prevents cascade failures by failing fast
- Fallback strategies: Provides graceful degradation when services fail
- Retry mechanisms: Automatic retry with exponential backoff
"""

from maverick_core.resilience.circuit_breaker import (
    CIRCUIT_BREAKER_CONFIGS,
    CircuitBreakerConfig,
    CircuitBreakerManager,
    CircuitBreakerMetrics,
    CircuitState,
    EnhancedCircuitBreaker,
    FailureDetectionStrategy,
    circuit_breaker,
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
)
from maverick_core.resilience.decorators import (
    circuit_breaker_method,
    with_http_circuit_breaker,
)
from maverick_core.resilience.fallback import (
    FallbackChain,
    FallbackStrategy,
)

__all__ = [
    # Enums
    "CircuitState",
    "FailureDetectionStrategy",
    # Configuration
    "CircuitBreakerConfig",
    "CIRCUIT_BREAKER_CONFIGS",
    # Core classes
    "EnhancedCircuitBreaker",
    "CircuitBreakerMetrics",
    "CircuitBreakerManager",
    # Registry functions
    "register_circuit_breaker",
    "get_circuit_breaker",
    "get_all_circuit_breakers",
    "reset_all_circuit_breakers",
    "get_circuit_breaker_status",
    # Initialization
    "initialize_circuit_breakers",
    "initialize_all_circuit_breakers",
    "get_circuit_breaker_manager",
    "get_all_circuit_breaker_status",
    # Decorators
    "circuit_breaker",
    "with_circuit_breaker",
    "with_async_circuit_breaker",
    "with_http_circuit_breaker",
    "circuit_breaker_method",
    # Fallback
    "FallbackStrategy",
    "FallbackChain",
]

