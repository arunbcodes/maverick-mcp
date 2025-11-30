# Package Architecture

Maverick MCP is built on a modular package architecture for maintainability, testability, and clean separation of concerns.

## Package Overview

```
packages/
├── maverick-core      # Domain logic, interfaces, config, exceptions
├── maverick-data      # Models, providers, cache, repositories
├── maverick-backtest  # Backtesting engine, strategies, workflows
├── maverick-india     # Indian market support, news, concall
├── maverick-agents    # LLM agents, research, supervisors
├── maverick-crypto    # Cryptocurrency data, DeFi, news sentiment
└── maverick-server    # MCP server, routers, tools
```

## Architecture Diagram

```mermaid
graph TB
    subgraph "Presentation Layer"
        MCP[MCP Server]
        REST[REST API]
    end
    
    subgraph "maverick-server"
        Routers[Tool Routers]
        Monitoring[Monitoring]
    end
    
    subgraph "Domain Layer"
        Agents[maverick-agents]
        Backtest[maverick-backtest]
        India[maverick-india]
        Crypto[maverick-crypto]
    end
    
    subgraph "Data Layer"
        Data[maverick-data]
    end
    
    subgraph "Core"
        Core[maverick-core]
    end
    
    MCP --> Routers
    REST --> Routers
    Routers --> Agents
    Routers --> Backtest
    Routers --> India
    Routers --> Crypto
    Agents --> Data
    Backtest --> Data
    India --> Data
    Crypto --> Data
    Data --> Core
    Agents --> Core
    Backtest --> Core
    India --> Core
    Crypto --> Core
```

## Package Dependencies

| Package | Dependencies | Purpose |
|---------|-------------|---------|
| **maverick-core** | numpy, pandas, pydantic | Foundation - zero framework deps |
| **maverick-data** | maverick-core, sqlalchemy, redis | Data persistence and caching |
| **maverick-backtest** | maverick-core, maverick-data, vectorbt | Strategy backtesting |
| **maverick-india** | maverick-core, maverick-data | Indian market support |
| **maverick-agents** | maverick-core, langchain, langgraph | AI-powered analysis |
| **maverick-crypto** | maverick-core, pycoingecko, vectorbt | Cryptocurrency analysis |
| **maverick-server** | All packages, fastmcp | MCP server and API |

## Quick Start

### Installation

```bash
# Install all packages
pip install maverick-core maverick-data maverick-backtest maverick-india maverick-server

# Or install from workspace
cd maverick-mcp
uv sync
```

### Basic Usage

```python
# Core configuration
from maverick_core import get_settings, get_logger

settings = get_settings()
logger = get_logger(__name__)

# Data access
from maverick_data import Stock, SessionLocal, StockDataProvider

provider = StockDataProvider()
df = provider.fetch_stock_data("AAPL", period="1y")

# Technical analysis
from maverick_core.technical import calculate_rsi, calculate_macd

df = calculate_rsi(df, period=14)
macd = calculate_macd(df)

# Backtesting
from maverick_backtest import BacktestEngine

engine = BacktestEngine()
results = engine.run_backtest("AAPL", strategy="sma_cross")
```

## Design Principles

### 1. Clean Architecture

```
┌──────────────────────────────────────────┐
│           Presentation (Server)           │
├──────────────────────────────────────────┤
│           Application (Routers)           │
├──────────────────────────────────────────┤
│           Domain (Agents, Backtest)       │
├──────────────────────────────────────────┤
│           Data (Models, Providers)        │
├──────────────────────────────────────────┤
│           Core (Interfaces, Entities)     │
└──────────────────────────────────────────┘
```

- Dependencies point inward
- Core has no external dependencies
- Domain is framework-agnostic

### 2. Interface-Based Design

All services implement interfaces from `maverick-core`:

```python
from maverick_core.interfaces import IStockDataFetcher

class MyProvider(IStockDataFetcher):
    async def get_stock_data(self, symbol: str, ...) -> pd.DataFrame:
        # Custom implementation
        ...
```

### 3. Dependency Injection

```python
from maverick_data import StockDataProvider
from maverick_data.services import ScreeningService

# Inject dependencies
provider = StockDataProvider()
service = ScreeningService(data_provider=provider)
```

### 4. Resilience Patterns

```python
from maverick_core.resilience import circuit_breaker

@circuit_breaker(name="api", failure_threshold=3)
def fetch_data(ticker: str) -> dict:
    return api.get(ticker)
```

## Package Details

- [maverick-core](maverick-core.md) - Core domain logic
- [maverick-data](maverick-data.md) - Data access layer
- [maverick-backtest](maverick-backtest.md) - Backtesting engine
- [maverick-india](maverick-india.md) - Indian market support
- [maverick-crypto](maverick-crypto.md) - Cryptocurrency analysis
- [maverick-server](maverick-server.md) - MCP server
- [Migration Guide](migration-guide.md) - Migrating from legacy code

## Version Compatibility

| Package | Version | Python |
|---------|---------|--------|
| maverick-core | 0.1.0 | ≥3.12 |
| maverick-data | 0.1.0 | ≥3.12 |
| maverick-backtest | 0.1.0 | ≥3.12 |
| maverick-india | 0.1.0 | ≥3.12 |
| maverick-agents | 0.1.0 | ≥3.12 |
| maverick-crypto | 0.1.0 | ≥3.12 |
| maverick-server | 0.1.0 | ≥3.12 |

