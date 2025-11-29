# maverick-core: Configuration

Core configuration management for Maverick MCP.

## Settings

The `Settings` class provides centralized configuration management.

### Basic Usage

```python
from maverick_core import Settings, get_settings

# Get singleton settings instance
settings = get_settings()

# Access configuration
print(settings.database_url)
print(settings.redis_url)
print(settings.log_level)
```

### Settings Class

::: maverick_core.config.settings.Settings
    options:
      show_source: true
      members:
        - database_url
        - redis_url
        - log_level
        - environment

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///maverick.db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENVIRONMENT` | Environment name | `development` |
| `TIINGO_API_KEY` | Tiingo API key | Required |
| `OPENROUTER_API_KEY` | OpenRouter API key | Optional |

### Configuration Validation

Settings are validated on startup using Pydantic:

```python
from maverick_core import Settings

# Create with custom values
settings = Settings(
    database_url="postgresql://user:pass@localhost/db",
    log_level="DEBUG"
)
```

---

## Constants

Common constants used across the application.

```python
from maverick_core.config.constants import (
    DEFAULT_CACHE_TTL,
    MAX_RETRY_ATTEMPTS,
    RATE_LIMIT_REQUESTS,
)
```

| Constant | Value | Description |
|----------|-------|-------------|
| `DEFAULT_CACHE_TTL` | 3600 | Default cache TTL in seconds |
| `MAX_RETRY_ATTEMPTS` | 3 | Maximum API retry attempts |
| `RATE_LIMIT_REQUESTS` | 100 | Rate limit per minute |

