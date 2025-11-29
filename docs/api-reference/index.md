# Package Reference

Maverick MCP is organized into modular packages, each with a specific responsibility.

## Package Overview

```
packages/
├── maverick-core      # Core utilities, config, logging, resilience
├── maverick-data      # Data models, providers, services, caching
├── maverick-backtest  # Backtesting engine, strategies, ML workflows
├── maverick-india     # Indian market support, conference calls
├── maverick-server    # MCP server, routers, monitoring
└── maverick-agents    # AI agents (future)
```

---

## Quick Import Reference

### maverick-core

```python
from maverick_core import (
    # Configuration
    Settings, get_settings,
    
    # Logging
    get_logger, setup_logging, CorrelationIDMiddleware,
    
    # Exceptions
    MaverickException, DataFetchError, ValidationError,
    
    # Resilience
    EnhancedCircuitBreaker, CircuitState, with_circuit_breaker,
    
    # Validation
    validate_ticker, validate_date_range,
)
```

### maverick-data

```python
from maverick_data import (
    # Models
    Stock, PriceCache, MaverickStocks, MaverickBearStocks,
    
    # Session
    SessionLocal, engine, get_session, get_db,
    
    # Providers
    StockDataProvider, EnhancedStockDataProvider,
    
    # Services
    StockCacheManager, StockDataFetcher, ScreeningService,
    MarketCalendarService,
)
```

### maverick-backtest

```python
from maverick_backtest import (
    # Engine
    VectorBTEngine,
    
    # Strategies
    SMAStrategy, RSIStrategy, MACDStrategy,
    
    # Analysis
    StrategyOptimizer, WalkForwardAnalyzer,
)
```

### maverick-india

```python
from maverick_india import (
    # Market
    IndianMarket, INDIAN_MARKET_CONFIG,
    
    # Concall
    TranscriptFetcher, ConcallSummarizer, SentimentAnalyzer,
)
```

### maverick-server

```python
from maverick_server import (
    # Monitoring
    PrometheusMetrics, HealthChecker, SentryIntegration,
)
```

---

## Package Details

| Package | Description | Key Exports |
|---------|-------------|-------------|
| [maverick-core](maverick-core/config.md) | Core utilities | Settings, logging, exceptions, validation |
| [maverick-data](maverick-data/models.md) | Data layer | Models, providers, services, caching |
| [maverick-backtest](maverick-backtest/engine.md) | Backtesting | VectorBT engine, strategies, optimization |
| [maverick-india](maverick-india/market.md) | Indian market | NSE/BSE support, concall analysis |
| [maverick-server](maverick-server/routers.md) | MCP server | Routers, monitoring, health checks |

---

## Installation

All packages are installed together:

```bash
# Install from workspace
uv sync

# Or install individual package
pip install -e packages/core
pip install -e packages/data
```

---

## Migration from Legacy

If you're migrating from `maverick_mcp`, see the [Migration Guide](../MIGRATION_PLAN.md).

**Old imports** (deprecated):
```python
from maverick_mcp.data.models import Stock
from maverick_mcp.config.settings import get_settings
```

**New imports** (recommended):
```python
from maverick_data import Stock
from maverick_core import get_settings
```

