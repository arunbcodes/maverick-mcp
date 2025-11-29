# maverick-core: Resilience

Circuit breakers and fallback strategies for robust external service calls.

## Circuit Breaker

Prevents cascading failures when external services are unavailable.

### Basic Usage

```python
from maverick_core import EnhancedCircuitBreaker, CircuitState

# Create circuit breaker
breaker = EnhancedCircuitBreaker(
    name="tiingo-api",
    failure_threshold=5,
    recovery_timeout=30,
    half_open_requests=3
)

# Use with external calls
try:
    if breaker.can_execute():
        result = call_external_api()
        breaker.record_success()
    else:
        result = get_fallback_data()
except Exception as e:
    breaker.record_failure()
    raise
```

### Decorator Usage

```python
from maverick_core import with_circuit_breaker

@with_circuit_breaker(
    name="stock-api",
    failure_threshold=3,
    recovery_timeout=60
)
async def fetch_stock_data(ticker: str):
    return await external_api.get_stock(ticker)
```

---

## Circuit States

```python
from maverick_core import CircuitState

# Circuit states
CircuitState.CLOSED      # Normal operation
CircuitState.OPEN        # Failures exceeded threshold, blocking calls
CircuitState.HALF_OPEN   # Testing if service recovered
```

### State Transitions

```
CLOSED → (failures >= threshold) → OPEN
OPEN → (timeout elapsed) → HALF_OPEN
HALF_OPEN → (test succeeds) → CLOSED
HALF_OPEN → (test fails) → OPEN
```

---

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | Required | Circuit breaker identifier |
| `failure_threshold` | int | 5 | Failures before opening |
| `recovery_timeout` | int | 30 | Seconds before half-open |
| `half_open_requests` | int | 3 | Test requests in half-open |
| `success_threshold` | int | 2 | Successes to close |

---

## Fallback Strategies

Define fallback behavior when circuit is open.

### FallbackChain

Chain multiple fallback options:

```python
from maverick_core import FallbackChain, FallbackStrategy

chain = FallbackChain([
    FallbackStrategy.CACHE,      # Try cache first
    FallbackStrategy.STALE_DATA, # Then stale data
    FallbackStrategy.DEFAULT,    # Finally, default value
])

result = chain.execute(
    primary_fn=lambda: api.fetch_data(),
    cache_fn=lambda: cache.get("data"),
    default_value={"status": "unavailable"}
)
```

### Built-in Strategies

| Strategy | Description |
|----------|-------------|
| `CACHE` | Return cached value |
| `STALE_DATA` | Return expired cache data |
| `DEFAULT` | Return default value |
| `RAISE` | Re-raise exception |
| `RETRY` | Retry with backoff |

---

## Monitoring

### Get Circuit Status

```python
breaker = EnhancedCircuitBreaker("my-service")

status = breaker.get_status()
print(f"State: {status['state']}")
print(f"Failures: {status['failure_count']}")
print(f"Success Rate: {status['success_rate']:.2%}")
```

### Health Check Integration

```python
from maverick_core import CircuitBreakerRegistry

# Get all circuit breakers
registry = CircuitBreakerRegistry()
all_breakers = registry.get_all()

for name, breaker in all_breakers.items():
    status = breaker.get_status()
    if status['state'] == CircuitState.OPEN:
        logger.warning(f"Circuit {name} is OPEN")
```

---

## Best Practices

### 1. Name Circuit Breakers Descriptively

```python
# Good
EnhancedCircuitBreaker("tiingo-stock-api")
EnhancedCircuitBreaker("redis-cache")

# Bad
EnhancedCircuitBreaker("cb1")
```

### 2. Set Appropriate Thresholds

```python
# High-availability service (aggressive)
EnhancedCircuitBreaker(
    name="critical-api",
    failure_threshold=3,
    recovery_timeout=10
)

# Best-effort service (lenient)
EnhancedCircuitBreaker(
    name="analytics-api",
    failure_threshold=10,
    recovery_timeout=60
)
```

### 3. Always Have Fallbacks

```python
@with_circuit_breaker(name="stock-api")
async def fetch_stock(ticker: str):
    try:
        return await primary_api.fetch(ticker)
    except CircuitBreakerOpenError:
        # Fallback to cache
        cached = await cache.get(f"stock:{ticker}")
        if cached:
            return cached
        # Fallback to default
        return {"ticker": ticker, "status": "unavailable"}
```

