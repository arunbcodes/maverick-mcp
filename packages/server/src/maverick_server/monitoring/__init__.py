"""
Maverick Server Monitoring Module.

This package provides comprehensive monitoring capabilities including:
- Prometheus metrics for backtesting and application performance
- Strategy execution monitoring
- API rate limiting and failure tracking
- Health checks and status dashboards
- Anomaly detection and alerting
- Sentry error tracking integration
"""

from maverick_server.monitoring.health_check import (
    ComponentHealth,
    HealthChecker,
    HealthStatus,
    SystemHealth,
    check_system_health,
    get_health_checker,
)
from maverick_server.monitoring.metrics import (
    BacktestingMetricsCollector,
    get_backtesting_metrics,
    get_metrics_for_prometheus,
    track_anomaly_detection,
    track_api_call_metrics,
    track_backtest_execution,
    track_strategy_performance,
)
from maverick_server.monitoring.prometheus_metrics import (
    PROMETHEUS_AVAILABLE,
    get_metrics,
    is_prometheus_available,
    track_authentication,
    track_authorization,
    track_cache_eviction,
    track_cache_operation,
    track_database_connection_event,
    track_database_query,
    track_error,
    track_external_api_call,
    track_rate_limit_hit,
    track_redis_operation,
    track_request,
    track_security_violation,
    track_tool_error,
    track_tool_usage,
    track_user_session,
    update_active_users,
    update_cache_metrics,
    update_database_metrics,
    update_performance_metrics,
    update_redis_metrics,
)
from maverick_server.monitoring.sentry import (
    SentryService,
    add_breadcrumb,
    capture_exception,
    capture_message,
    get_sentry_service,
)

__all__ = [
    # Health check
    "HealthChecker",
    "HealthStatus",
    "ComponentHealth",
    "SystemHealth",
    "check_system_health",
    "get_health_checker",
    # Backtesting Metrics
    "BacktestingMetricsCollector",
    "get_backtesting_metrics",
    "track_backtest_execution",
    "track_strategy_performance",
    "track_api_call_metrics",
    "track_anomaly_detection",
    "get_metrics_for_prometheus",
    # Prometheus Metrics
    "PROMETHEUS_AVAILABLE",
    "is_prometheus_available",
    "get_metrics",
    "track_request",
    "track_error",
    "track_tool_usage",
    "track_tool_error",
    "track_cache_operation",
    "track_cache_eviction",
    "update_cache_metrics",
    "track_database_query",
    "update_database_metrics",
    "track_database_connection_event",
    "track_redis_operation",
    "update_redis_metrics",
    "track_external_api_call",
    "track_user_session",
    "update_active_users",
    "track_authentication",
    "track_authorization",
    "track_security_violation",
    "track_rate_limit_hit",
    "update_performance_metrics",
    # Sentry
    "SentryService",
    "get_sentry_service",
    "capture_exception",
    "capture_message",
    "add_breadcrumb",
]

