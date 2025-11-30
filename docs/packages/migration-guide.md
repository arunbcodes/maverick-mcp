# Migration Guide

Guide for migrating from the legacy `maverick_mcp` monolith to the new modular packages.

## Overview

The Maverick MCP codebase has been refactored from a monolithic structure to a modular package architecture:

| Legacy | New Package | Purpose |
|--------|-------------|---------|
| `maverick_mcp/config/` | `maverick-core` | Configuration |
| `maverick_mcp/utils/` | `maverick-core` | Utilities, resilience |
| `maverick_mcp/data/` | `maverick-data` | Models, session |
| `maverick_mcp/providers/` | `maverick-data` | Data providers |
| `maverick_mcp/services/` | `maverick-data` | Services |
| `maverick_mcp/backtesting/` | `maverick-backtest` | Backtesting engine |
| `maverick_mcp/concall/` | `maverick-india` | Conference calls |
| `maverick_mcp/config/markets/` | `maverick-india` | Indian market |
| `maverick_mcp/domain/agents/` | `maverick-agents` | LLM agents |
| `maverick_mcp/api/` | `maverick-server` | MCP server |

## Import Changes

### Configuration

```python
# ❌ Old
from maverick_mcp.config.settings import settings
from maverick_mcp.config.settings import Settings

# ✅ New
from maverick_core import get_settings, Settings

settings = get_settings()
```

### Logging

```python
# ❌ Old
from maverick_mcp.logging_config import setup_logging, get_logger
from maverick_mcp.config.logging_settings import LoggingSettings

# ✅ New
from maverick_core import get_logger, setup_logging
from maverick_core.logging import LoggingSettings

logger = get_logger(__name__)
```

### Models

```python
# ❌ Old
from maverick_mcp.data.models import Stock, PriceCache, MaverickStocks
from maverick_mcp.data.models import SessionLocal, engine
from maverick_mcp.database.base import Base

# ✅ New
from maverick_data import Stock, PriceCache, MaverickStocks
from maverick_data import SessionLocal, engine, get_session
from maverick_data.models import Base
```

### Providers

```python
# ❌ Old
from maverick_mcp.providers.stock_data import (
    StockDataProvider,
    EnhancedStockDataProvider
)
from maverick_mcp.providers.yfinance_pool import YFinancePool

# ✅ New
from maverick_data.providers import (
    StockDataProvider,
    EnhancedStockDataProvider,
    YFinancePool
)
```

### Services

```python
# ❌ Old
from maverick_mcp.services.screening_service import ScreeningService
from maverick_mcp.services.market_calendar_service import MarketCalendarService
from maverick_mcp.services.stock_cache_manager import StockCacheManager

# ✅ New
from maverick_data.services import (
    ScreeningService,
    MarketCalendarService,
    StockCacheManager
)
```

### Exceptions

```python
# ❌ Old
from maverick_mcp.exceptions import (
    MaverickMCPError,
    DataFetchError,
    ValidationError
)

# ✅ New
from maverick_core import (
    MaverickException,
    DataFetchError,
    ValidationError
)
```

### Circuit Breaker

```python
# ❌ Old
from maverick_mcp.utils.circuit_breaker import EnhancedCircuitBreaker
from maverick_mcp.utils.circuit_breaker_decorators import circuit_breaker

# ✅ New
from maverick_core.resilience import (
    EnhancedCircuitBreaker,
    circuit_breaker
)
```

### Technical Analysis

```python
# ❌ Old
from maverick_mcp.core.technical_analysis import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands
)

# ✅ New
from maverick_core.technical import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands
)

# Or from backtest package
from maverick_backtest.analysis import TechnicalAnalyzer
```

### Backtesting

```python
# ❌ Old
from maverick_mcp.backtesting.strategy_executor import (
    ExecutionContext,
    get_strategy_executor
)
from maverick_mcp.backtesting import BacktestingEngine

# ✅ New
from maverick_backtest import (
    BacktestEngine,
    ExecutionContext,
    run_backtest
)
```

### Conference Calls

```python
# ❌ Old
from maverick_mcp.concall.models import (
    Transcript,
    TranscriptSummary,
    SentimentAnalysis
)
from maverick_mcp.concall.services import TranscriptFetcher

# ✅ New
from maverick_india.concall.models import (
    Transcript,
    TranscriptSummary,
    SentimentAnalysis
)
from maverick_india.concall import TranscriptFetcher
```

### Indian Market

```python
# ❌ Old
from maverick_mcp.config.markets import get_market_config, Market
from maverick_mcp.providers.indian_market_data import IndianMarketDataProvider

# ✅ New
from maverick_india.market import (
    get_market_config,
    Market,
    IndianMarketDataProvider
)
```

### MCP Server

```python
# ❌ Old
from maverick_mcp.api.server import mcp
from maverick_mcp.api.routers import register_tools

# ✅ New
from maverick_server import mcp
from maverick_server.routers import register_all_tools
```

### Agents

```python
# ❌ Old
from maverick_mcp.domain.research.agents import (
    ResearchAgent,
    ParallelResearchOrchestrator
)

# ✅ New
from maverick_agents.research import (
    ResearchAgent,
    ParallelResearchOrchestrator
)
```

## Migration Steps

### Step 1: Update Dependencies

Add new packages to your `pyproject.toml`:

```toml
dependencies = [
    "maverick-core",
    "maverick-data",
    "maverick-backtest",
    "maverick-india",
    "maverick-server",
]
```

Or install from workspace:

```bash
cd maverick-mcp
uv sync
```

### Step 2: Update Import Paths

Use find/replace to update imports:

```bash
# Find all maverick_mcp imports
grep -r "from maverick_mcp" --include="*.py"

# Replace patterns (use your IDE's search/replace)
# maverick_mcp.config.settings -> maverick_core
# maverick_mcp.data.models -> maverick_data
# maverick_mcp.providers -> maverick_data.providers
# etc.
```

### Step 3: Test Imports

Verify imports work correctly:

```python
# Test script
try:
    from maverick_core import get_settings, get_logger
    from maverick_data import Stock, get_session
    from maverick_backtest import run_backtest
    from maverick_india import get_indian_market_overview
    from maverick_server import mcp
    print("All imports successful!")
except ImportError as e:
    print(f"Import error: {e}")
```

### Step 4: Run Tests

```bash
# Run tests for new packages
pytest packages/ -v

# Run your project tests
pytest tests/ -v
```

## Compatibility Layer

For gradual migration, a compatibility layer is available:

```python
# In your conftest.py or early in your app
import sys

# Add fallback paths
sys.path.insert(0, "packages/core/src")
sys.path.insert(0, "packages/data/src")
sys.path.insert(0, "packages/server/src")
sys.path.insert(0, "packages/backtest/src")
sys.path.insert(0, "packages/india/src")
```

## Common Issues

### Issue 1: Module Not Found

```
ModuleNotFoundError: No module named 'maverick_core'
```

**Solution**: Ensure packages are installed or add to `sys.path`:

```python
import sys
sys.path.insert(0, "/path/to/maverick-mcp/packages/core/src")
```

### Issue 2: Circular Import

```
ImportError: cannot import name 'X' from partially initialized module
```

**Solution**: Use lazy imports or import at function level:

```python
def my_function():
    from maverick_data import Stock  # Import when needed
    ...
```

### Issue 3: Settings Not Found

```
ValidationError: TIINGO_API_KEY is required
```

**Solution**: Ensure environment variables are set:

```bash
export TIINGO_API_KEY=your-key
export DATABASE_URL=postgresql://...
```

Or use `.env` file with `python-dotenv`.

### Issue 4: Database Connection

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution**: Verify database URL and ensure database is running:

```bash
# Check connection
python -c "from maverick_data import engine; engine.connect()"
```

## Docker Migration

### Old Dockerfile

```dockerfile
COPY maverick_mcp /app/maverick_mcp
CMD ["python", "-m", "maverick_mcp.api.server"]
```

### New Dockerfile

```dockerfile
# Copy all packages
COPY packages /app/packages

# Set PYTHONPATH
ENV PYTHONPATH=/app/packages/core/src:/app/packages/data/src:...

# Use new entry point
CMD ["python", "-m", "maverick_server"]
```

## Scripts Migration

Scripts use fallback imports for compatibility:

```python
# Example from seed_sp500.py
try:
    from maverick_data import Stock, get_session, bulk_insert_stocks
except ImportError:
    # Fallback to legacy
    from maverick_mcp.data.models import Stock, SessionLocal
```

## Help

If you encounter issues:

1. Check the [Troubleshooting Guide](../user-guide/troubleshooting.md)
2. Review [Package Documentation](index.md)
3. Open an issue on GitHub

## Timeline

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1-3 | ✅ Complete | Core infrastructure |
| Phase 4-6 | ✅ Complete | Data layer, providers |
| Phase 7 | ✅ Complete | Services |
| Phase 8 | ✅ Complete | Scripts with fallbacks |
| Phase 9 | ✅ Complete | Test compatibility |
| Phase 10 | ✅ Complete | Docker updates |
| Phase 11 | ✅ Complete | Documentation |

The migration is **complete**. New packages have 100% feature parity with the legacy code.

