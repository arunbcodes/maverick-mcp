# maverick-core: Logging

Structured logging with correlation IDs for distributed tracing.

## Quick Start

```python
from maverick_core import get_logger, setup_logging

# Setup logging (call once at startup)
setup_logging(level="INFO", json_format=True)

# Get a logger
logger = get_logger(__name__)

# Log messages
logger.info("Processing request", extra={"ticker": "AAPL"})
logger.error("Failed to fetch data", exc_info=True)
```

---

## Functions

### get_logger

Get a configured logger instance.

```python
from maverick_core import get_logger

logger = get_logger("mymodule")
logger.info("Hello world")
```

**Parameters:**
- `name` (str): Logger name, typically `__name__`

**Returns:**
- `logging.Logger`: Configured logger instance

---

### setup_logging

Configure application-wide logging.

```python
from maverick_core import setup_logging

setup_logging(
    level="DEBUG",
    json_format=True,
    log_file="/var/log/maverick.log"
)
```

**Parameters:**
- `level` (str): Log level (DEBUG, INFO, WARNING, ERROR)
- `json_format` (bool): Use JSON structured logging
- `log_file` (str, optional): File path for log output

---

## Correlation IDs

Track requests across services with correlation IDs.

### Middleware

```python
from fastapi import FastAPI
from maverick_core import CorrelationIDMiddleware

app = FastAPI()
app.add_middleware(CorrelationIDMiddleware)
```

### Decorator

```python
from maverick_core import with_correlation_id

@with_correlation_id
async def process_request(ticker: str):
    logger.info(f"Processing {ticker}")  # Includes correlation ID
```

### Manual Usage

```python
from maverick_core.logging import set_correlation_id, get_correlation_id

# Set correlation ID
set_correlation_id("req-12345")

# Get current correlation ID
current_id = get_correlation_id()
```

---

## Structured Logging Format

When `json_format=True`, logs are output as JSON:

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "maverick_data.providers",
  "message": "Fetched stock data",
  "correlation_id": "req-abc123",
  "ticker": "AAPL",
  "duration_ms": 125
}
```

---

## Error Logger

Enhanced error logging with sensitive data masking.

```python
from maverick_core import ErrorLogger

error_logger = ErrorLogger()

try:
    # risky operation
    pass
except Exception as e:
    error_logger.log_exception(
        e,
        context={"api_key": "secret123"}  # Will be masked
    )
```

**Masked Fields:**
- `api_key`, `password`, `token`, `secret`
- Credit card numbers (pattern-matched)
- Email addresses (partially masked)

