# maverick-core: Exceptions

Comprehensive exception hierarchy for consistent error handling.

## Base Exception

All Maverick exceptions inherit from `MaverickException`:

```python
from maverick_core import MaverickException

try:
    # operation
    pass
except MaverickException as e:
    print(f"Error code: {e.error_code}")
    print(f"Message: {e.message}")
    print(f"Details: {e.details}")
```

---

## Exception Hierarchy

```
MaverickException (base)
├── DataError
│   ├── DataFetchError
│   ├── DataValidationError
│   └── DataNotFoundError
├── ConfigurationError
│   ├── MissingConfigError
│   └── InvalidConfigError
├── ServiceError
│   ├── ExternalServiceError
│   ├── CircuitBreakerOpenError
│   └── RateLimitError
├── AuthenticationError
│   ├── InvalidTokenError
│   └── TokenExpiredError
└── ValidationError
    ├── InvalidTickerError
    └── InvalidDateRangeError
```

---

## Common Exceptions

### DataFetchError

Raised when data fetching fails.

```python
from maverick_core import DataFetchError

try:
    data = fetch_stock_data("INVALID")
except DataFetchError as e:
    print(f"Failed to fetch: {e.ticker}")
```

**Attributes:**
- `ticker` (str): Stock symbol
- `source` (str): Data source that failed
- `retry_after` (int, optional): Seconds to wait before retry

---

### ValidationError

Raised for input validation failures.

```python
from maverick_core import ValidationError

try:
    validate_ticker("!!INVALID!!")
except ValidationError as e:
    print(f"Invalid input: {e.field} - {e.message}")
```

**Attributes:**
- `field` (str): Field that failed validation
- `value` (Any): Invalid value
- `constraints` (dict): Validation constraints

---

### CircuitBreakerOpenError

Raised when circuit breaker is open.

```python
from maverick_core import CircuitBreakerOpenError

try:
    result = call_external_api()
except CircuitBreakerOpenError as e:
    print(f"Service unavailable, retry after {e.retry_after}s")
```

**Attributes:**
- `service_name` (str): Name of the service
- `retry_after` (int): Seconds until circuit closes
- `failure_count` (int): Number of consecutive failures

---

### RateLimitError

Raised when rate limit is exceeded.

```python
from maverick_core import RateLimitError

try:
    result = api_call()
except RateLimitError as e:
    await asyncio.sleep(e.retry_after)
    result = api_call()  # Retry
```

**Attributes:**
- `limit` (int): Rate limit
- `remaining` (int): Remaining requests
- `retry_after` (int): Seconds to wait

---

## Creating Custom Exceptions

```python
from maverick_core import MaverickException

class MyCustomError(MaverickException):
    """Custom error for my feature."""
    
    error_code = "MY_ERROR"
    
    def __init__(self, message: str, custom_field: str):
        super().__init__(message)
        self.custom_field = custom_field
```

---

## Error Handling Best Practices

### Catch Specific Exceptions

```python
from maverick_core import (
    DataFetchError,
    ValidationError,
    CircuitBreakerOpenError,
)

try:
    data = fetch_data(ticker)
except ValidationError:
    return {"error": "Invalid ticker format"}
except CircuitBreakerOpenError as e:
    return {"error": f"Service unavailable, retry in {e.retry_after}s"}
except DataFetchError as e:
    logger.error(f"Data fetch failed for {e.ticker}")
    return {"error": "Data temporarily unavailable"}
```

### Use Error Codes for API Responses

```python
except MaverickException as e:
    return {
        "error": {
            "code": e.error_code,
            "message": str(e),
            "details": e.details
        }
    }
```

