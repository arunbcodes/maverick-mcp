# MaverickMCP Settings Configuration

This document provides comprehensive documentation for all configuration settings available in the MaverickMCP application. Settings are managed through Pydantic models and can be configured via environment variables.

## Environment Variable Prefix

All environment variables use the prefix `MAVERICK_` unless otherwise specified in sub-settings.

---

## Required Variables for Server & API

The following environment variables **must be configured** for the server and API to function correctly in production:

### Critical (Must Set in Production)

| Env Variable | Required | Description | Example |
|--------------|----------|-------------|---------|
| `MAVERICK_JWT_SECRET` | **Yes** | JWT signing secret - must be changed from default | `openssl rand -hex 32` |
| `MAVERICK_DB_HOST` | **Yes** | Database host | `postgres`, `db.example.com` |
| `MAVERICK_DB_PASSWORD` | **Yes** | Database password | `your-secure-password` |
| `MAVERICK_REDIS_HOST` | **Yes** | Redis host | `redis`, `redis.example.com` |
| `MAVERICK_ENVIRONMENT` | **Yes** | Environment mode | `production`, `staging`, `development` |

### Recommended (For Full Functionality)

| Env Variable | Required | Description | Example |
|--------------|----------|-------------|---------|
| `MAVERICK_DB_USERNAME` | Recommended | Database username | `postgres` |
| `MAVERICK_DB_DATABASE` | Recommended | Database name | `maverick_mcp` |
| `MAVERICK_DB_PORT` | Recommended | Database port | `5432` |
| `MAVERICK_REDIS_PORT` | Recommended | Redis port | `6379` |
| `MAVERICK_REDIS_PASSWORD` | Recommended | Redis password (if auth enabled) | `your-redis-password` |
| `MAVERICK_CORS_ORIGINS` | Recommended | Allowed CORS origins | `https://app.example.com` |
| `MAVERICK_LOG_LEVEL` | Recommended | Logging level | `INFO`, `WARNING`, `DEBUG` |

### External API Keys (For AI & Data Features)

| Env Variable | Required | Description | Example |
|--------------|----------|-------------|---------|
| `MAVERICK_OPENAI_API_KEY` | For AI features | OpenAI API key | `sk-...` |
| `MAVERICK_ANTHROPIC_API_KEY` | For AI features | Anthropic API key | `sk-ant-...` |
| `MAVERICK_OPENROUTER_API_KEY` | For AI features | OpenRouter API key | `sk-or-...` |
| `MAVERICK_TIINGO_API_KEY` | For market data | Tiingo API key | `your-tiingo-key` |
| `MAVERICK_FRED_API_KEY` | For economic data | FRED API key | `your-fred-key` |
| `MAVERICK_EXA_API_KEY` | For research | EXA API key | `your-exa-key` |

### Minimal `.env` Example

```bash
# Required for production
MAVERICK_ENVIRONMENT=production
MAVERICK_JWT_SECRET=your-32-byte-hex-secret-here

# Database
MAVERICK_DB_HOST=postgres
MAVERICK_DB_PORT=5432
MAVERICK_DB_USERNAME=postgres
MAVERICK_DB_PASSWORD=your-secure-password
MAVERICK_DB_DATABASE=maverick_mcp

# Redis
MAVERICK_REDIS_HOST=redis
MAVERICK_REDIS_PORT=6379

# CORS (comma-separated for multiple origins)
MAVERICK_CORS_ORIGINS=https://app.example.com,https://admin.example.com

# API Keys (add as needed)
MAVERICK_OPENAI_API_KEY=sk-...
MAVERICK_TIINGO_API_KEY=...
```

---

## Main Settings

The `Settings` class is the main application settings container.

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `app_name` | `str` | `"MaverickMCP"` | `MAVERICK_APP_NAME` | Application name |
| `app_version` | `str` | `"1.0.0"` | `MAVERICK_APP_VERSION` | Application version |
| `environment` | `str` | `"development"` | `MAVERICK_ENVIRONMENT` | Environment (development, staging, production) |

### Authentication - JWT

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `jwt_secret` | `str` | `"change-me-in-production..."` | `MAVERICK_JWT_SECRET` | JWT signing secret |
| `jwt_algorithm` | `str` | `"HS256"` | `MAVERICK_JWT_ALGORITHM` | JWT algorithm |
| `jwt_access_token_expire_minutes` | `int` | `15` | `MAVERICK_JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry in minutes |
| `jwt_refresh_token_expire_days` | `int` | `30` | `MAVERICK_JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry in days |

### Authentication - API Keys

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `api_key_prefix` | `str` | `"mav_"` | `MAVERICK_API_KEY_PREFIX` | Prefix for API keys |

### CORS

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `cors_origins` | `list[str]` | `["http://localhost:3000", "http://localhost:5173"]` | `MAVERICK_CORS_ORIGINS` | Allowed CORS origins (comma-separated) |
| `cors_allow_credentials` | `bool` | `True` | `MAVERICK_CORS_ALLOW_CREDENTIALS` | Allow credentials in CORS |

### Rate Limiting

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `rate_limit_enabled` | `bool` | `True` | `MAVERICK_RATE_LIMIT_ENABLED` | Enable rate limiting |
| `rate_limit_free_rpm` | `int` | `100` | `MAVERICK_RATE_LIMIT_FREE_RPM` | Requests per minute for free tier |
| `rate_limit_pro_rpm` | `int` | `1000` | `MAVERICK_RATE_LIMIT_PRO_RPM` | Requests per minute for pro tier |
| `rate_limit_enterprise_rpm` | `int` | `10000` | `MAVERICK_RATE_LIMIT_ENTERPRISE_RPM` | Requests per minute for enterprise tier |

### LLM Token Budgets

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `token_budget_free_daily` | `int` | `10,000` | `MAVERICK_TOKEN_BUDGET_FREE_DAILY` | Daily token budget for free tier |
| `token_budget_pro_daily` | `int` | `100,000` | `MAVERICK_TOKEN_BUDGET_PRO_DAILY` | Daily token budget for pro tier |
| `token_budget_enterprise_daily` | `int` | `1,000,000` | `MAVERICK_TOKEN_BUDGET_ENTERPRISE_DAILY` | Daily token budget for enterprise tier |

### Logging

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `log_level` | `str` | `"INFO"` | `MAVERICK_LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `log_format` | `str` | `"%(asctime)s %(levelname)s..."` | `MAVERICK_LOG_FORMAT` | Log message format |
| `request_log_format` | `str` | `"%(asctime)s [%(request_id)s]..."` | `MAVERICK_REQUEST_LOG_FORMAT` | Request log format |

### External API Keys

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `tiingo_api_key` | `str` | `None` | `MAVERICK_TIINGO_API_KEY` | Tiingo API key for market data |
| `openai_api_key` | `str` | `None` | `MAVERICK_OPENAI_API_KEY` | OpenAI API key |
| `anthropic_api_key` | `str` | `None` | `MAVERICK_ANTHROPIC_API_KEY` | Anthropic API key |
| `fred_api_key` | `str` | `None` | `MAVERICK_FRED_API_KEY` | Federal Reserve Economic Data API key |
| `openrouter_api_key` | `str` | `None` | `MAVERICK_OPENROUTER_API_KEY` | OpenRouter API key |
| `exa_api_key` | `str` | `None` | `MAVERICK_EXA_API_KEY` | EXA API key |

### CI/CD

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `github_actions` | `bool` | `False` | `MAVERICK_GITHUB_ACTIONS` | Running in GitHub Actions |
| `ci` | `bool` | `False` | `MAVERICK_CI` | Running in CI environment |

### Feature Flags

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `enable_redis` | `bool` | `True` | `MAVERICK_ENABLE_REDIS` | Enable Redis for server |
| `enable_research` | `bool` | `True` | `MAVERICK_ENABLE_RESEARCH` | Enable research features |
| `enable_india` | `bool` | `True` | `MAVERICK_ENABLE_INDIA` | Enable India stock market |

---

## Database Settings

Prefix: `MAVERICK_DB_`

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `host` | `str` | `"localhost"` | `MAVERICK_DB_HOST` | Database host |
| `port` | `int` | `5432` | `MAVERICK_DB_PORT` | Database port |
| `username` | `str` | `"postgres"` | `MAVERICK_DB_USERNAME` | Database username |
| `password` | `str` | `"postgres"` | `MAVERICK_DB_PASSWORD` | Database password |
| `database` | `str` | `"maverick_mcp"` | `MAVERICK_DB_DATABASE` | Database name |
| `max_connections` | `int` | `10` | `MAVERICK_DB_MAX_CONNECTIONS` | Maximum number of connections |
| `pool_size` | `int` | `20` | `MAVERICK_DB_POOL_SIZE` | Connection pool size |
| `pool_max_overflow` | `int` | `10` | `MAVERICK_DB_POOL_MAX_OVERFLOW` | Maximum overflow connections |
| `pool_timeout` | `int` | `30` | `MAVERICK_DB_POOL_TIMEOUT` | Pool connection timeout (seconds) |
| `pool_recycle` | `int` | `3600` | `MAVERICK_DB_POOL_RECYCLE` | Pool recycle time (seconds) |
| `pool_pre_ping` | `bool` | `True` | `MAVERICK_DB_POOL_PRE_PING` | Enable pool pre-ping |
| `echo` | `bool` | `False` | `MAVERICK_DB_ECHO` | Echo SQL statements |
| `use_pooling` | `bool` | `True` | `MAVERICK_DB_USE_POOLING` | Use connection pooling |
| `statement_timeout` | `int` | `30000` | `MAVERICK_DB_STATEMENT_TIMEOUT` | Statement timeout (ms) |
| `database_url` | `str` | `""` | `MAVERICK_DB_DATABASE_URL` | Full database URL (overrides individual settings) |
| `postgres_url` | `str` | `""` | `MAVERICK_DB_POSTGRES_URL` | Alternative full database URL |

---

## API Settings

Prefix: `MAVERICK_API_`

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `host` | `str` | `"0.0.0.0"` | `MAVERICK_API_HOST` | API host |
| `port` | `int` | `8000` | `MAVERICK_API_PORT` | API port |
| `debug` | `bool` | `False` | `MAVERICK_API_DEBUG` | Debug mode |
| `cache_timeout` | `int` | `300` | `MAVERICK_API_CACHE_TIMEOUT` | Cache timeout (seconds) |
| `request_timeout` | `int` | `120` | `MAVERICK_API_REQUEST_TIMEOUT` | Request timeout (seconds) |
| `log_level` | `str` | `"INFO"` | `MAVERICK_API_LOG_LEVEL` | API log level |

---

## Redis Settings

Prefix: `MAVERICK_REDIS_`

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `host` | `str` | `"localhost"` | `MAVERICK_REDIS_HOST` | Redis host |
| `port` | `int` | `6379` | `MAVERICK_REDIS_PORT` | Redis port |
| `db` | `int` | `0` | `MAVERICK_REDIS_DB` | Redis database number |
| `username` | `str` | `None` | `MAVERICK_REDIS_USERNAME` | Redis username |
| `password` | `str` | `None` | `MAVERICK_REDIS_PASSWORD` | Redis password |
| `ssl` | `bool` | `False` | `MAVERICK_REDIS_SSL` | Use SSL for connection |
| `max_connections` | `int` | `50` | `MAVERICK_REDIS_MAX_CONNECTIONS` | Maximum connections in pool |
| `socket_timeout` | `int` | `5` | `MAVERICK_REDIS_SOCKET_TIMEOUT` | Socket timeout (seconds) |

---

## Cache Settings

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `enabled` | `bool` | `True` | `MAVERICK_CACHE_ENABLED` | Enable caching |
| `ttl_seconds` | `int` | `604800` | `MAVERICK_TTL_SECONDS` | Default cache TTL (7 days) |
| `quick_ttl` | `int` | `300` | `MAVERICK_QUICK_CACHE_TTL` | Quick cache TTL (5 minutes) |
| `max_size_mb` | `int` | `500` | `MAVERICK_MAX_CACHE_SIZE_MB` | Maximum cache size (MB) |

---

## Provider Settings

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `yfinance_timeout` | `int` | `30` | - | yfinance API timeout (seconds) |
| `yfinance_rate_limit` | `int` | `120` | - | yfinance requests per minute |
| `external_data_timeout` | `int` | `120` | - | External data API timeout (seconds) |
| `max_symbols_per_batch` | `int` | `100` | - | Maximum symbols per batch request |

---

## Performance Settings

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `api_timeout` | `int` | `120` | `MAVERICK_API_REQUEST_TIMEOUT` | Default API request timeout (seconds) |
| `max_retry_attempts` | `int` | `3` | - | Maximum retry attempts |
| `retry_backoff_factor` | `float` | `2.0` | - | Exponential backoff factor |
| `default_batch_size` | `int` | `50` | - | Default batch size |
| `parallel_workers` | `int` | `4` | - | Number of parallel workers |

---

## Agent Settings

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `cache_ttl` | `int` | `300` | `MAVERICK_AGENT_CACHE_TTL_SECONDS` | Agent cache TTL (seconds) |
| `max_iterations` | `int` | `10` | `MAVERICK_MAX_AGENT_ITERATIONS` | Maximum workflow iterations |
| `max_parallel_agents` | `int` | `5` | - | Maximum parallel agents |
| `max_execution_time` | `int` | `720` | `MAVERICK_MAX_AGENT_EXECUTION_TIME_SECONDS` | Maximum execution time (seconds) |
| `circuit_breaker_threshold` | `int` | `5` | - | Circuit breaker threshold |
| `circuit_breaker_recovery` | `int` | `60` | `MAVERICK_CIRCUIT_BREAKER_RECOVERY_TIMEOUT` | Recovery timeout (seconds) |

---

## Financial Settings

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `default_account_size` | `Decimal` | `100000` | - | Default account size (USD) |
| `max_position_size_conservative` | `float` | `0.05` | - | Max position size - conservative (5%) |
| `max_position_size_moderate` | `float` | `0.10` | - | Max position size - moderate (10%) |
| `max_position_size_aggressive` | `float` | `0.20` | - | Max position size - aggressive (20%) |

---

## UI Settings

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `default_page_size` | `int` | `20` | - | Default items per page |
| `max_page_size` | `int` | `100` | - | Maximum items per page |
| `default_screening_limit` | `int` | `20` | - | Default stocks in screening results |
| `max_screening_limit` | `int` | `100` | - | Maximum stocks in screening results |
| `default_history_days` | `int` | `365` | - | Default days of historical data |

---

## Validation Settings

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `min_symbol_length` | `int` | `1` | - | Minimum stock symbol length |
| `max_symbol_length` | `int` | `10` | - | Maximum stock symbol length |
| `max_text_field_length` | `int` | `100` | - | Maximum text field length |
| `max_description_length` | `int` | `500` | - | Maximum description length |

---

## Research Settings

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `default_max_sources` | `int` | `50` | - | Default max sources per research |
| `default_depth` | `str` | `"comprehensive"` | - | Default research depth |
| `cache_ttl_hours` | `int` | `4` | - | Research cache TTL (hours) |
| `max_content_length` | `int` | `50000` | - | Maximum content length |
| `trusted_domains` | `list[str]` | See below | - | List of trusted domains |

**Default Trusted Domains:**
- reuters.com
- bloomberg.com
- wsj.com
- ft.com
- marketwatch.com
- cnbc.com
- yahoo.com
- seekingalpha.com

---

## AI Config

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `ollama_model` | `str` | `"gpt-oss-20b"` | - | OLLAMA model name |
| `ollama_base_url` | `str` | `"http://localhost:11434"` | - | OLLAMA base URL |
| `ollama_base_url_with_version` | `str` | `"http://localhost:11434/v1"` | - | OLLAMA base URL with version |

---

## Sentry Settings

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `sentry_dsn` | `str` | `""` | - | Sentry DSN |
| `sentry_release_version` | `str` | `""` | - | Sentry release version |

---

## Server Settings

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `server_name` | `str` | `"MaverickMCP"` | - | MCP server name |
| `server_host` | `str` | `"0.0.0.0"` | - | Server listener IP address |
| `server_port` | `int` | `8000` | - | Server listener TCP port |
| `server_transport` | `str` | `"sse"` | - | MCP transport (SSE, Streaminghttp, STDIO) |

---

## Usage

### Loading Settings

```python
from maverick_core.config.settings import get_settings

# Get cached settings singleton
settings = get_settings()

# Access settings
print(settings.app_name)
print(settings.database.url)
print(settings.redis.host)
```

### Environment Variables

Settings can be configured via environment variables:

```bash
# Main settings
export MAVERICK_ENVIRONMENT=production
export MAVERICK_LOG_LEVEL=WARNING

# Database
export MAVERICK_DB_HOST=db.example.com
export MAVERICK_DB_PASSWORD=secret

# Redis
export MAVERICK_REDIS_HOST=redis.example.com

# API Keys
export MAVERICK_OPENAI_API_KEY=sk-...
export MAVERICK_TIINGO_API_KEY=...
```

### Docker Compose

In Docker Compose, use the `.env` file:

```yaml
environment:
  - MAVERICK_ENVIRONMENT=${ENVIRONMENT:-development}
  - MAVERICK_DB_HOST=${DB_HOST:-postgres}
  - MAVERICK_REDIS_HOST=${REDIS_HOST:-redis}
```

---

## Properties

The `Settings` class provides convenience properties:

| Property | Returns | Description |
|----------|---------|-------------|
| `is_production` | `bool` | `True` if environment is "production" |
| `is_development` | `bool` | `True` if environment is "development" or "dev" |

The `DatabaseSettings` class provides:

| Property | Returns | Description |
|----------|---------|-------------|
| `url` | `str` | Complete database connection URL |

The `RedisSettings` class provides:

| Property | Returns | Description |
|----------|---------|-------------|
| `url` | `str` | Complete Redis connection URL |
