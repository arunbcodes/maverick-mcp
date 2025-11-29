# maverick-server: Monitoring

Health checks, metrics, and observability.

## Health Checks

```python
from maverick_server.monitoring import HealthChecker

checker = HealthChecker()

# Run health check
status = checker.check_health()

print(f"Status: {status['status']}")  # healthy, degraded, unhealthy
print(f"Components: {status['components']}")
```

### Component Status

```python
{
    "status": "healthy",
    "components": {
        "database": {"status": "healthy", "latency_ms": 5},
        "redis": {"status": "healthy", "latency_ms": 2},
        "yfinance_api": {"status": "healthy", "latency_ms": 150}
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Prometheus Metrics

```python
from maverick_server.monitoring import PrometheusMetrics

metrics = PrometheusMetrics()

# Record metrics
metrics.record_request(endpoint="/api/stocks", duration=0.125)
metrics.record_error(endpoint="/api/stocks", error_type="timeout")
metrics.record_cache_hit("stock_data")
metrics.record_cache_miss("stock_data")
```

### Available Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | Request latency |
| `cache_hits_total` | Counter | Cache hits |
| `cache_misses_total` | Counter | Cache misses |
| `circuit_breaker_state` | Gauge | Circuit breaker states |
| `active_connections` | Gauge | Database connections |

### Prometheus Endpoint

```
GET /metrics
```

Returns Prometheus-formatted metrics:

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/api/stocks",method="GET"} 1234

# HELP http_request_duration_seconds Request latency
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 900
http_request_duration_seconds_bucket{le="0.5"} 1200
```

---

## Sentry Integration

Error tracking and performance monitoring:

```python
from maverick_server.monitoring import SentryIntegration

# Initialize (usually at startup)
sentry = SentryIntegration(
    dsn="https://xxx@sentry.io/project",
    environment="production",
    traces_sample_rate=0.1
)

# Capture exception
try:
    risky_operation()
except Exception as e:
    sentry.capture_exception(e, extra={"ticker": "AAPL"})

# Capture message
sentry.capture_message("Cache cleared", level="info")
```

### Configuration

Environment variables:

```bash
SENTRY_DSN=https://xxx@sentry.io/project
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

---

## Circuit Breaker Monitoring

```python
from maverick_server.monitoring import get_circuit_breaker_status

status = get_circuit_breaker_status()

for name, breaker_status in status.items():
    print(f"{name}: {breaker_status['state']}")
    print(f"  Failures: {breaker_status['failure_count']}")
    print(f"  Success Rate: {breaker_status['success_rate']:.2%}")
```

---

## Resource Usage

```python
from maverick_server.monitoring import get_resource_usage

usage = get_resource_usage()

print(f"CPU: {usage['cpu_percent']}%")
print(f"Memory: {usage['memory_mb']} MB")
print(f"DB Connections: {usage['db_connections']}")
```

---

## Health Endpoints

### Basic Health

```
GET /health
```

Returns:
```json
{"status": "healthy"}
```

### Detailed Health

```
GET /health/detailed
```

Returns:
```json
{
    "status": "healthy",
    "components": {
        "database": {"status": "healthy"},
        "redis": {"status": "healthy"},
        "external_apis": {"status": "degraded"}
    },
    "uptime_seconds": 86400,
    "version": "0.1.0"
}
```

---

## Dashboard

```python
from maverick_server.monitoring import get_status_dashboard

dashboard = get_status_dashboard()

# Returns aggregated status for monitoring UI
{
    "health": {...},
    "metrics": {...},
    "alerts": [...],
    "recent_errors": [...]
}
```

---

## Alerting

Configure alerts based on metrics:

```python
from maverick_server.monitoring import AlertManager

alerts = AlertManager()

# Check for alerts
active_alerts = alerts.check_alerts()

for alert in active_alerts:
    print(f"ALERT: {alert['name']} - {alert['message']}")
```

### Alert Types

| Alert | Condition |
|-------|-----------|
| High Error Rate | Error rate > 5% |
| Circuit Open | Any circuit breaker open |
| High Latency | P95 latency > 2s |
| Low Cache Hit Rate | Cache hit rate < 50% |
| Database Connection Pool | Pool utilization > 80% |

