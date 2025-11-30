# maverick-server

MCP server, API routers, and monitoring for Maverick MCP.

## Overview

`maverick-server` provides:

- **MCP Server**: FastMCP-based Model Context Protocol server
- **Tool Routers**: MCP tool implementations for all features
- **Monitoring**: Prometheus metrics, Sentry integration, health checks
- **API Layer**: REST endpoints (optional)

## Installation

```bash
pip install maverick-server
```

## Quick Start

```python
from maverick_server import mcp, register_all_tools

# Register all MCP tools
register_all_tools(mcp)

# Run server
if __name__ == "__main__":
    mcp.run()
```

## MCP Server

### Configuration

```python
from maverick_server import create_mcp_server

# Create server with configuration
mcp = create_mcp_server(
    name="maverick-mcp",
    version="0.1.0",
    description="Stock analysis MCP server"
)
```

### Run Options

```bash
# Development mode
python -m maverick_server

# With hot reload
python -m maverick_server --reload

# Production (uvicorn)
uvicorn maverick_server.api:app --host 0.0.0.0 --port 8000
```

### Claude Desktop Integration

```json
{
  "mcpServers": {
    "maverick-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/maverick-mcp", "run", "python", "-m", "maverick_server"],
      "env": {
        "TIINGO_API_KEY": "your-key",
        "DATABASE_URL": "postgresql://..."
      }
    }
  }
}
```

## Tool Routers

### Data Tools

Stock data and market information.

```python
from maverick_server.routers import register_data_tools

# Registers:
# - fetch_stock_data(ticker, start_date, end_date)
# - fetch_stock_data_batch(tickers, start_date, end_date)
# - get_stock_info(ticker)
# - get_news_sentiment(ticker, timeframe, limit)
# - get_cached_price_data(ticker, start_date, end_date)
# - get_chart_links(ticker)
# - clear_cache(ticker)
```

### Technical Analysis Tools

```python
from maverick_server.routers import register_technical_tools

# Registers:
# - get_rsi_analysis(ticker, period, days)
# - get_macd_analysis(ticker, fast, slow, signal, days)
# - get_support_resistance(ticker, days)
# - get_full_technical_analysis(ticker, days)
# - get_stock_chart_analysis(ticker)
```

### Screening Tools

```python
from maverick_server.routers import register_screening_tools

# Registers:
# - get_maverick_stocks(limit)
# - get_maverick_bear_stocks(limit)
# - get_supply_demand_breakouts(limit)
# - get_all_screening_recommendations()
# - get_screening_by_criteria(min_momentum, min_volume, max_price, sector)
```

### Portfolio Tools

```python
from maverick_server.routers import register_portfolio_tools

# Registers:
# - add_portfolio_position(ticker, shares, purchase_price, date, notes)
# - get_my_portfolio(include_current_prices)
# - remove_portfolio_position(ticker, shares)
# - clear_my_portfolio(confirm)
# - risk_adjusted_analysis(ticker, risk_level)
# - compare_tickers(tickers, days)
# - portfolio_correlation_analysis(tickers, days)
```

### Backtesting Tools

```python
from maverick_server.routers import register_backtest_tools

# Registers:
# - run_backtest(symbol, strategy, start_date, end_date, ...)
# - optimize_strategy(symbol, strategy, optimization_metric, level)
# - walk_forward_analysis(symbol, strategy, window_size, step_size)
# - monte_carlo_simulation(symbol, strategy, num_simulations)
# - compare_strategies(symbol, strategies)
# - list_strategies()
# - parse_strategy(description)
# - backtest_portfolio(symbols, strategy, position_size)
# - generate_backtest_charts(symbol, strategy, theme)
```

### ML Strategy Tools

```python
from maverick_server.routers import register_ml_tools

# Registers:
# - run_ml_strategy_backtest(symbol, strategy_type, model_type, ...)
# - train_ml_predictor(symbol, model_type, n_estimators, ...)
# - analyze_market_regimes(symbol, method, n_regimes)
# - create_strategy_ensemble(symbols, strategies, weighting)
```

### Agent Tools

```python
from maverick_server.routers import register_agents_tools

# Registers:
# - analyze_market_with_agent(query, persona, strategy)
# - orchestrated_analysis(query, persona, routing_strategy)
# - deep_research_financial(topic, persona, depth, focus_areas)
# - compare_personas_analysis(query)
# - compare_multi_agent_analysis(query, agent_types)
# - list_available_agents()
```

### Research Tools

```python
from maverick_server.routers import register_research_tools

# Registers:
# - comprehensive_research(query, persona, scope, max_sources)
# - company_comprehensive(symbol, include_competitive)
# - analyze_market_sentiment(topic, timeframe, persona)
```

### Conference Call Tools

```python
from maverick_server.routers import register_concall_tools

# Registers:
# - fetch_transcript(ticker, quarter, fiscal_year)
# - summarize_transcript(ticker, quarter, fiscal_year, mode)
# - analyze_sentiment(ticker, quarter, fiscal_year)
# - query_transcript(question, ticker, quarter, fiscal_year)
# - compare_quarters(ticker, quarters)
```

### Indian Market Tools

```python
from maverick_server.routers import register_india_tools

# Registers:
# - get_indian_market_recommendations(strategy, limit)
# - analyze_nifty_sectors()
# - get_indian_market_overview()
# - get_indian_economic_indicators()
# - get_indian_stock_news(symbol, limit)
# - compare_us_indian_markets(period)
# - convert_currency(amount, from_currency, to_currency)
# - compare_similar_companies(us_symbol, indian_symbol)
```

### System Tools

```python
from maverick_server.routers import register_system_tools

# Registers:
# - get_system_health()
# - get_component_status(component_name)
# - get_circuit_breaker_status()
# - get_resource_usage()
# - get_status_dashboard()
# - reset_circuit_breaker(breaker_name)
# - get_health_history()
# - run_health_diagnostics()
```

## Custom Router

Create a custom tool router.

```python
from fastmcp import FastMCP

def register_custom_tools(mcp: FastMCP):
    """Register custom MCP tools."""
    
    @mcp.tool()
    async def my_custom_tool(
        param1: str,
        param2: int = 10
    ) -> dict:
        """
        My custom tool description.
        
        Args:
            param1: First parameter
            param2: Second parameter (default: 10)
            
        Returns:
            Dictionary with results
        """
        # Implementation
        return {"result": f"{param1} * {param2}"}
```

## Monitoring

### Prometheus Metrics

```python
from maverick_server.monitoring import (
    PrometheusMetrics,
    get_metrics
)

metrics = get_metrics()

# Track request
metrics.track_request("fetch_stock_data", "AAPL", 0.5)

# Track cache
metrics.track_cache_hit("stock_data")
metrics.track_cache_miss("stock_data")

# Track errors
metrics.track_error("DataFetchError", "fetch_stock_data")
```

### Available Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `maverick_requests_total` | Counter | Total MCP tool requests |
| `maverick_request_duration_seconds` | Histogram | Request duration |
| `maverick_cache_hits_total` | Counter | Cache hits |
| `maverick_cache_misses_total` | Counter | Cache misses |
| `maverick_errors_total` | Counter | Error count by type |
| `maverick_active_requests` | Gauge | Active requests |
| `maverick_backtest_duration_seconds` | Histogram | Backtest duration |

### Expose Metrics Endpoint

```python
from maverick_server.monitoring import create_metrics_app

# Create Prometheus metrics app
metrics_app = create_metrics_app()

# Mount at /metrics
app.mount("/metrics", metrics_app)
```

### Sentry Integration

```python
from maverick_server.monitoring import init_sentry

# Initialize Sentry
init_sentry(
    dsn="https://your-sentry-dsn",
    environment="production",
    traces_sample_rate=0.1
)
```

### Health Checks

```python
from maverick_server.monitoring import (
    HealthChecker,
    HealthStatus
)

checker = HealthChecker()

# Register health check
@checker.check("database")
async def check_database():
    # Check database connection
    return HealthStatus.HEALTHY

@checker.check("redis")
async def check_redis():
    # Check Redis connection
    return HealthStatus.DEGRADED

# Get health status
status = await checker.get_health()
print(f"Overall: {status['status']}")
for name, check in status['checks'].items():
    print(f"  {name}: {check['status']}")
```

### Health Endpoint

```python
from maverick_server.monitoring import create_health_app

# Create health check app
health_app = create_health_app()

# Mount at /health
app.mount("/health", health_app)
```

## Error Handling

```python
from maverick_core import MaverickException
from maverick_server import error_handler

@mcp.tool()
@error_handler
async def safe_tool(ticker: str) -> dict:
    """Tool with automatic error handling."""
    # Any MaverickException is caught and returned as error
    raise ValidationError("Invalid ticker")
```

## Middleware

### Correlation ID Middleware

```python
from maverick_core.logging import CorrelationIDMiddleware

# Add to FastAPI app
app.add_middleware(CorrelationIDMiddleware)
```

### Request Logging

```python
from maverick_server.middleware import RequestLoggingMiddleware

app.add_middleware(
    RequestLoggingMiddleware,
    log_request_body=True,
    log_response_body=False
)
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_HOST` | Server host | `0.0.0.0` |
| `MCP_PORT` | Server port | `8000` |
| `SENTRY_DSN` | Sentry DSN | None |
| `METRICS_ENABLED` | Enable Prometheus | `true` |
| `HEALTH_CHECK_INTERVAL` | Health check interval | `30` |

## Testing

### Test MCP Tools

```python
import pytest
from maverick_server import mcp

@pytest.mark.asyncio
async def test_fetch_stock_data():
    result = await mcp.call_tool(
        "fetch_stock_data",
        ticker="AAPL",
        period="1mo"
    )
    
    assert result['ticker'] == "AAPL"
    assert 'data' in result
```

### Mock Providers

```python
from unittest.mock import patch

@pytest.mark.asyncio
async def test_with_mock():
    with patch('maverick_data.providers.StockDataProvider') as mock:
        mock.return_value.fetch_stock_data.return_value = mock_df
        
        result = await mcp.call_tool("fetch_stock_data", ticker="AAPL")
        
        assert result is not None
```

## API Reference

For detailed API documentation, see:

- [MCP Routers API](../api-reference/maverick-server/routers.md)
- [Monitoring API](../api-reference/maverick-server/monitoring.md)

