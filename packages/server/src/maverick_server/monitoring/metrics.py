"""
Prometheus metrics for MaverickMCP backtesting system.

This module provides specialized metrics for monitoring:
- Backtesting execution performance and reliability
- Strategy performance over time
- API rate limiting and failure tracking
- Resource usage and optimization
- Anomaly detection and alerting
"""

import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any

try:
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Summary,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    CollectorRegistry = None  # type: ignore
    Counter = None  # type: ignore
    Gauge = None  # type: ignore
    Histogram = None  # type: ignore
    Summary = None  # type: ignore
    generate_latest = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class PerformanceThreshold:
    """Configuration for performance thresholds."""

    metric_name: str
    warning_value: float
    critical_value: float
    comparison_type: str = "greater_than"  # greater_than, less_than, equal_to


class BacktestingMetricsCollector:
    """
    Comprehensive metrics collector for backtesting operations.

    Provides high-level interfaces for tracking backtesting performance,
    strategy metrics, API usage, and anomaly detection.
    """

    def __init__(self):
        self._anomaly_thresholds = self._initialize_default_thresholds()
        self._lock = threading.Lock()
        self._metrics_data: dict[str, Any] = {}

        # Initialize Prometheus registry if available
        if PROMETHEUS_AVAILABLE:
            self._registry = CollectorRegistry()
            self._setup_prometheus_metrics()
        else:
            self._registry = None
            logger.warning("Prometheus client not available, using in-memory metrics")

        logger.info("Backtesting metrics collector initialized")

    def _initialize_default_thresholds(self) -> dict[str, PerformanceThreshold]:
        """Initialize default performance thresholds for anomaly detection."""
        return {
            "sharpe_ratio_low": PerformanceThreshold(
                "sharpe_ratio", 0.5, 0.0, "less_than"
            ),
            "max_drawdown_high": PerformanceThreshold(
                "max_drawdown", 20.0, 30.0, "greater_than"
            ),
            "win_rate_low": PerformanceThreshold("win_rate", 40.0, 30.0, "less_than"),
            "execution_time_high": PerformanceThreshold(
                "execution_time", 60.0, 120.0, "greater_than"
            ),
            "api_failure_rate_high": PerformanceThreshold(
                "api_failure_rate", 5.0, 10.0, "greater_than"
            ),
            "memory_usage_high": PerformanceThreshold(
                "memory_usage", 1000, 2000, "greater_than"
            ),
        }

    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics collectors."""
        if not PROMETHEUS_AVAILABLE:
            return

        # Backtest execution counters
        self._backtest_executions_total = Counter(
            "maverick_backtest_executions_total",
            "Total number of backtesting executions",
            ["strategy_name", "status", "symbol", "timeframe"],
            registry=self._registry,
        )

        self._backtest_execution_duration = Histogram(
            "maverick_backtest_execution_duration_seconds",
            "Duration of backtesting executions in seconds",
            ["strategy_name", "symbol", "timeframe", "data_size"],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
            registry=self._registry,
        )

        # Strategy performance metrics
        self._strategy_returns = Histogram(
            "maverick_strategy_returns_percent",
            "Strategy returns in percentage",
            ["strategy_name", "symbol", "period"],
            buckets=(-50, -25, -10, -5, -1, 0, 1, 5, 10, 25, 50, 100),
            registry=self._registry,
        )

        self._strategy_sharpe_ratio = Histogram(
            "maverick_strategy_sharpe_ratio",
            "Strategy Sharpe ratio",
            ["strategy_name", "symbol", "period"],
            buckets=(-2, -1, -0.5, 0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0),
            registry=self._registry,
        )

        # API call tracking
        self._api_calls_total = Counter(
            "maverick_api_calls_total",
            "Total API calls made to external providers",
            ["provider", "endpoint", "method", "status_code"],
            registry=self._registry,
        )

        self._api_call_duration = Histogram(
            "maverick_api_call_duration_seconds",
            "API call duration in seconds",
            ["provider", "endpoint"],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
            registry=self._registry,
        )

        # Anomaly detection
        self._strategy_performance_anomalies = Counter(
            "maverick_strategy_performance_anomalies_total",
            "Detected strategy performance anomalies",
            ["strategy_name", "anomaly_type", "severity"],
            registry=self._registry,
        )

    @contextmanager
    def track_backtest_execution(
        self, strategy_name: str, symbol: str, timeframe: str, data_points: int = 0
    ):
        """
        Context manager for tracking backtest execution metrics.

        Args:
            strategy_name: Name of the trading strategy
            symbol: Trading symbol (e.g., 'AAPL')
            timeframe: Data timeframe (e.g., '1D', '1H')
            data_points: Number of data points being processed
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()

        # Determine data size category
        data_size = self._categorize_data_size(data_points)

        try:
            yield

            # Success metrics
            duration = time.time() - start_time

            if PROMETHEUS_AVAILABLE and self._registry:
                self._backtest_executions_total.labels(
                    strategy_name=strategy_name,
                    status="success",
                    symbol=symbol,
                    timeframe=timeframe,
                ).inc()

                self._backtest_execution_duration.labels(
                    strategy_name=strategy_name,
                    symbol=symbol,
                    timeframe=timeframe,
                    data_size=data_size,
                ).observe(duration)

            # In-memory tracking
            with self._lock:
                key = f"backtest_{strategy_name}_{symbol}"
                if key not in self._metrics_data:
                    self._metrics_data[key] = {"success": 0, "failure": 0, "total_duration": 0}
                self._metrics_data[key]["success"] += 1
                self._metrics_data[key]["total_duration"] += duration

            # Check for performance anomalies
            memory_used = self._get_memory_usage() - start_memory
            self._check_execution_anomalies(strategy_name, duration, memory_used)

        except Exception:
            # Error metrics
            if PROMETHEUS_AVAILABLE and self._registry:
                self._backtest_executions_total.labels(
                    strategy_name=strategy_name,
                    status="failure",
                    symbol=symbol,
                    timeframe=timeframe,
                ).inc()

            with self._lock:
                key = f"backtest_{strategy_name}_{symbol}"
                if key not in self._metrics_data:
                    self._metrics_data[key] = {"success": 0, "failure": 0, "total_duration": 0}
                self._metrics_data[key]["failure"] += 1

            raise

    def track_strategy_performance(
        self,
        strategy_name: str,
        symbol: str,
        period: str,
        returns: float,
        sharpe_ratio: float,
        max_drawdown: float,
        win_rate: float,
        total_trades: int,
        winning_trades: int,
    ):
        """
        Track comprehensive strategy performance metrics.

        Args:
            strategy_name: Name of the trading strategy
            symbol: Trading symbol
            period: Performance period (e.g., '1Y', '6M', '3M')
            returns: Total returns in percentage
            sharpe_ratio: Sharpe ratio
            max_drawdown: Maximum drawdown percentage
            win_rate: Win rate percentage
            total_trades: Total number of trades
            winning_trades: Number of winning trades
        """
        if PROMETHEUS_AVAILABLE and self._registry:
            self._strategy_returns.labels(
                strategy_name=strategy_name, symbol=symbol, period=period
            ).observe(returns)

            self._strategy_sharpe_ratio.labels(
                strategy_name=strategy_name, symbol=symbol, period=period
            ).observe(sharpe_ratio)

        # In-memory tracking
        with self._lock:
            key = f"strategy_perf_{strategy_name}_{symbol}_{period}"
            self._metrics_data[key] = {
                "returns": returns,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "timestamp": datetime.now().isoformat(),
            }

        # Check for performance anomalies
        self._check_strategy_anomalies(
            strategy_name, sharpe_ratio, max_drawdown, win_rate
        )

    def track_api_call(
        self,
        provider: str,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float,
        error_type: str | None = None,
        remaining_calls: int | None = None,
        reset_time: datetime | None = None,
    ):
        """
        Track API call metrics including rate limiting and failures.

        Args:
            provider: API provider name (e.g., 'tiingo', 'yahoo')
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            duration: Request duration in seconds
            error_type: Type of error if request failed
            remaining_calls: Remaining API calls before rate limit
            reset_time: When rate limit resets
        """
        if PROMETHEUS_AVAILABLE and self._registry:
            self._api_calls_total.labels(
                provider=provider,
                endpoint=endpoint,
                method=method,
                status_code=str(status_code),
            ).inc()

            self._api_call_duration.labels(provider=provider, endpoint=endpoint).observe(duration)

        # In-memory tracking
        with self._lock:
            key = f"api_{provider}_{endpoint}"
            if key not in self._metrics_data:
                self._metrics_data[key] = {"calls": 0, "failures": 0, "total_duration": 0}
            self._metrics_data[key]["calls"] += 1
            self._metrics_data[key]["total_duration"] += duration
            if status_code >= 400:
                self._metrics_data[key]["failures"] += 1

        # Check for API anomalies
        self._check_api_anomalies(provider, endpoint, status_code, duration)

    def detect_anomaly(self, anomaly_type: str, severity: str, context: dict[str, Any]):
        """Record detected anomaly."""
        strategy_name = context.get("strategy_name", "unknown")

        if PROMETHEUS_AVAILABLE and self._registry:
            self._strategy_performance_anomalies.labels(
                strategy_name=strategy_name, anomaly_type=anomaly_type, severity=severity
            ).inc()

        logger.warning(
            f"Anomaly detected: {anomaly_type} (severity: {severity})",
            extra={"context": context},
        )

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

    def _categorize_data_size(self, data_points: int) -> str:
        """Categorize data size for metrics labeling."""
        if data_points < 100:
            return "small"
        elif data_points < 1000:
            return "medium"
        elif data_points < 10000:
            return "large"
        else:
            return "xlarge"

    def _check_execution_anomalies(
        self, strategy_name: str, duration: float, memory_mb: float
    ):
        """Check for execution performance anomalies."""
        threshold = self._anomaly_thresholds["execution_time_high"]
        if duration > threshold.critical_value:
            self.detect_anomaly(
                "execution_time_high",
                "critical",
                {
                    "strategy_name": strategy_name,
                    "duration": duration,
                    "threshold": threshold.critical_value,
                },
            )
        elif duration > threshold.warning_value:
            self.detect_anomaly(
                "execution_time_high",
                "warning",
                {
                    "strategy_name": strategy_name,
                    "duration": duration,
                    "threshold": threshold.warning_value,
                },
            )

    def _check_strategy_anomalies(
        self,
        strategy_name: str,
        sharpe_ratio: float,
        max_drawdown: float,
        win_rate: float,
    ):
        """Check for strategy performance anomalies."""
        # Check Sharpe ratio
        threshold = self._anomaly_thresholds["sharpe_ratio_low"]
        if sharpe_ratio < threshold.critical_value:
            self.detect_anomaly(
                "sharpe_ratio_low",
                "critical",
                {"strategy_name": strategy_name, "sharpe_ratio": sharpe_ratio},
            )
        elif sharpe_ratio < threshold.warning_value:
            self.detect_anomaly(
                "sharpe_ratio_low",
                "warning",
                {"strategy_name": strategy_name, "sharpe_ratio": sharpe_ratio},
            )

        # Check max drawdown
        threshold = self._anomaly_thresholds["max_drawdown_high"]
        if max_drawdown > threshold.critical_value:
            self.detect_anomaly(
                "max_drawdown_high",
                "critical",
                {"strategy_name": strategy_name, "max_drawdown": max_drawdown},
            )
        elif max_drawdown > threshold.warning_value:
            self.detect_anomaly(
                "max_drawdown_high",
                "warning",
                {"strategy_name": strategy_name, "max_drawdown": max_drawdown},
            )

    def _check_api_anomalies(
        self, provider: str, endpoint: str, status_code: int, duration: float
    ):
        """Check for API call anomalies."""
        # Check API response time
        if duration > 30.0:  # 30 second threshold
            self.detect_anomaly(
                "api_response_slow",
                "warning" if duration < 60.0 else "critical",
                {"provider": provider, "endpoint": endpoint, "duration": duration},
            )

        # Check for repeated failures
        if status_code >= 500:
            self.detect_anomaly(
                "api_server_error",
                "critical",
                {
                    "provider": provider,
                    "endpoint": endpoint,
                    "status_code": status_code,
                },
            )

    def get_metrics_text(self) -> str:
        """Get all backtesting metrics in Prometheus text format."""
        if PROMETHEUS_AVAILABLE and self._registry:
            return generate_latest(self._registry).decode("utf-8")
        else:
            # Return JSON representation for non-Prometheus environments
            import json
            return json.dumps(self._metrics_data, indent=2)

    def get_metrics_data(self) -> dict[str, Any]:
        """Get in-memory metrics data."""
        with self._lock:
            return self._metrics_data.copy()


# Global metrics collector instance
_metrics_collector: BacktestingMetricsCollector | None = None
_collector_lock = threading.Lock()


def get_backtesting_metrics() -> BacktestingMetricsCollector:
    """Get or create the global backtesting metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        with _collector_lock:
            if _metrics_collector is None:
                _metrics_collector = BacktestingMetricsCollector()
    return _metrics_collector


# Convenience functions for common operations
def track_backtest_execution(
    strategy_name: str, symbol: str, timeframe: str, data_points: int = 0
):
    """Convenience function to track backtest execution."""
    return get_backtesting_metrics().track_backtest_execution(
        strategy_name, symbol, timeframe, data_points
    )


def track_strategy_performance(
    strategy_name: str,
    symbol: str,
    period: str,
    returns: float,
    sharpe_ratio: float,
    max_drawdown: float,
    win_rate: float,
    total_trades: int,
    winning_trades: int,
):
    """Convenience function to track strategy performance."""
    get_backtesting_metrics().track_strategy_performance(
        strategy_name,
        symbol,
        period,
        returns,
        sharpe_ratio,
        max_drawdown,
        win_rate,
        total_trades,
        winning_trades,
    )


def track_api_call_metrics(
    provider: str,
    endpoint: str,
    method: str,
    status_code: int,
    duration: float,
    error_type: str | None = None,
    remaining_calls: int | None = None,
    reset_time: datetime | None = None,
):
    """Convenience function to track API call metrics."""
    get_backtesting_metrics().track_api_call(
        provider,
        endpoint,
        method,
        status_code,
        duration,
        error_type,
        remaining_calls,
        reset_time,
    )


def track_anomaly_detection(anomaly_type: str, severity: str, context: dict[str, Any]):
    """Convenience function to track detected anomalies."""
    get_backtesting_metrics().detect_anomaly(anomaly_type, severity, context)


def get_metrics_for_prometheus() -> str:
    """Get backtesting metrics in Prometheus format."""
    return get_backtesting_metrics().get_metrics_text()

