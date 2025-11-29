# Maverick MCP Migration Plan

## Overview

This document outlines the complete migration plan from the legacy `maverick_mcp` monolith to the modular package structure under `packages/`.

### Current State

- **Legacy Code**: `maverick_mcp/` - Monolithic codebase with 340+ files
- **New Packages**: `packages/` - Modular structure (partially implemented)
- **Dependencies**: 1,113+ imports from `maverick_mcp` across the codebase

### Target Architecture

```
packages/
├── maverick-core      # Domain logic, interfaces, config, exceptions
├── maverick-data      # Models, providers, cache, repositories
├── maverick-backtest  # Backtesting engine, strategies, workflows
├── maverick-agents    # LLM agents, research, supervisors
├── maverick-india     # Indian market, news, concall, economic
└── maverick-server    # MCP server, routers, tools
```

---

## Dependency Analysis

### By Module (Internal References)

| Module | Count | Target Package | Status |
|--------|-------|----------------|--------|
| `providers` | 103 | maverick-data | 🔄 Partial |
| `utils` | 101 | maverick-core | 🔄 Partial |
| `data` | 70 | maverick-data | 🔄 Partial |
| `config` | 62 | maverick-core | 🔄 Partial |
| `api` | 56 | maverick-server | ❌ Not Started |
| `concall` | 32 | maverick-india | ✅ Done |
| `domain` | 21 | maverick-core | 🔄 Partial |
| `backtesting` | 18 | maverick-backtest | ✅ Done |
| `monitoring` | 14 | maverick-server | ✅ Done |
| `core` | 14 | maverick-core | 🔄 Partial |
| `agents` | 13 | maverick-agents | ✅ Done |
| `infrastructure` | 11 | maverick-data | ❌ Not Started |
| `workflows` | 10 | maverick-backtest | ✅ Done |
| `validation` | 7 | maverick-core | ✅ Done |
| `application` | 7 | maverick-core | ❌ Not Started |
| `tools` | 4 | maverick-agents | ❌ Not Started |
| `services` | 4 | maverick-data | ❌ Not Started |
| `database` | 3 | maverick-data | ❌ Not Started |
| `memory` | 2 | maverick-agents | ✅ Done |
| `auth` | 2 | maverick-server | ❌ Not Started |
| `analysis` | 2 | maverick-backtest | ✅ Done |
| `strategies` | 1 | maverick-backtest | ✅ Done |
| `interfaces` | 1 | maverick-core | ✅ Done |

### Most Used Imports (Top 20)

| Import | Count | Target |
|--------|-------|--------|
| `utils.logging.get_logger` | 29 | maverick-core |
| `utils.currency_converter` | 25 | maverick-india |
| `config.settings.get_settings` | 23 | maverick-core |
| `data.models` | 16 | maverick-data |
| `providers.stock_data` | 24 | maverick-data |
| `config.settings.settings` | 11 | maverick-core |
| `providers.rbi_data` | 10 | maverick-india |
| `concall.models` | 9 | maverick-data |
| `providers.openrouter_provider` | 8 | maverick-agents |
| `agents.deep_research` | 8 | maverick-agents |
| `providers.indian_news` | 8 | maverick-india |
| `data.models.get_session` | 7 | maverick-data |
| `backtesting.strategies` | 7 | maverick-backtest |
| `backtesting.persistence` | 7 | maverick-backtest |
| `workflows.state` | 6 | maverick-backtest |
| `utils.structured_logger` | 6 | maverick-core |
| `infrastructure.data_fetching` | 6 | maverick-data |
| `infrastructure.caching` | 6 | maverick-data |
| `config.database` | 6 | maverick-data |
| `backtesting.VectorBTEngine` | 6 | maverick-backtest |

---

## Migration Phases

### Phase 1: Data Layer (Priority: HIGH) ⏳

**Goal**: Complete migration of all data-related components

#### 1.1 Models (maverick-data)
- [ ] `bulk_insert_screening_data` function
- [ ] `bulk_insert_price_data` function
- [ ] `SessionLocal` factory
- [ ] `engine` singleton
- [ ] `get_db` dependency
- [ ] `get_async_db` dependency
- [ ] All remaining model helpers

#### 1.2 Database Configuration
- [ ] `config.database` → `maverick-data.session`
- [ ] Connection pooling settings
- [ ] Migration utilities (alembic integration)

#### 1.3 Infrastructure Services
- [ ] `infrastructure.data_fetching.StockDataFetchingService`
- [ ] `infrastructure.caching.CacheManagementService`
- [ ] `data.performance` utilities

### Phase 2: Providers Layer (Priority: HIGH) ⏳

**Goal**: Migrate all data providers

#### 2.1 Stock Data Providers (maverick-data)
- [ ] `providers.stock_data.StockDataProvider`
- [ ] `providers.stock_data.EnhancedStockDataProvider`
- [ ] `providers.optimized_stock_data`
- [ ] `providers.optimized_screening`

#### 2.2 Market Data Providers (maverick-data)
- [ ] `providers.market_data.MarketDataProvider`
- [ ] `providers.macro_data.MacroDataProvider`

#### 2.3 Indian Market Providers (maverick-india)
- [ ] `providers.indian_market_data.IndianMarketDataProvider`
- [ ] `providers.rbi_data.RBIDataProvider`
- [ ] `providers.exchange_rate`
- [ ] `providers.indian_news.IndianNewsProvider`
- [ ] `providers.moneycontrol_scraper`
- [ ] `providers.economic_times_scraper`
- [ ] `providers.multi_source_news_aggregator`

#### 2.4 LLM Providers (maverick-agents)
- [ ] `providers.openrouter_provider.OpenRouterProvider`
- [ ] `providers.llm_factory`

### Phase 3: Configuration & Utils (Priority: HIGH) ⏳

**Goal**: Complete core utilities migration

#### 3.1 Configuration (maverick-core)
- [ ] `config.settings.get_settings`
- [ ] `config.settings.settings` singleton
- [ ] `config.markets` (Market enum, configs)
- [ ] `config.logging_settings`

#### 3.2 Logging (maverick-core)
- [ ] `utils.logging.get_logger`
- [ ] `utils.structured_logger`
- [ ] `utils.logging_init`
- [ ] `utils.orchestration_logging`

#### 3.3 Utilities (maverick-core)
- [ ] `utils.currency_converter` → maverick-india
- [ ] `utils.monitoring`
- [ ] `utils.memory_profiler`
- [ ] `utils.parallel_research` → maverick-agents
- [ ] `utils.stock_helpers`
- [ ] `utils.data_chunking`
- [ ] `utils.batch_processing`

#### 3.4 Circuit Breakers (maverick-core) ✅
- [x] `utils.circuit_breaker`
- [x] `utils.circuit_breaker_decorators`
- [x] `utils.fallback_strategies`

### Phase 4: Domain Layer (Priority: MEDIUM) ⏳

**Goal**: Complete domain model migration

#### 4.1 Domain Services (maverick-core)
- [ ] `domain.stock_analysis.StockAnalysisService`
- [ ] `domain.services.technical_analysis_service`
- [ ] `core.technical_analysis`

#### 4.2 Value Objects (maverick-core)
- [ ] `domain.value_objects.technical_indicators`

#### 4.3 Application Services
- [ ] `application.screening.indian_market`
- [ ] `analysis.market_comparison`

### Phase 5: API Layer (Priority: HIGH) ⏳

**Goal**: Migrate server and all routers

#### 5.1 Server Core (maverick-server)
- [ ] `api.server.mcp` - Main MCP server
- [ ] `api.api_server.create_api_app`
- [ ] Entry point (`__main__.py`)

#### 5.2 Routers (maverick-server)
- [ ] `api.routers.tool_registry`
- [ ] `api.routers.concall`
- [ ] `api.routers.research`
- [ ] `api.routers.data`
- [ ] `api.routers.portfolio`
- [ ] `api.routers.health_enhanced`
- [ ] All other routers

#### 5.3 Authentication (maverick-server)
- [ ] `auth` module (if applicable)

### Phase 6: Agents Layer (Priority: MEDIUM) ✅

**Goal**: Complete agents migration

- [x] `agents.deep_research.DeepResearchAgent`
- [x] `agents.supervisor`
- [x] Research subagents
- [x] Memory stores
- [x] `maverick_server.routers.agents` - LangGraph agent tools

### Phase 7: Utility Functions ✅

**Goal**: Add utility helpers to new packages

- [x] `maverick_core.utils.datetime_utils` - Date/time operations
- [x] `maverick_data.utils.stock_helpers` - Stock data helpers

### Phase 8: Scripts & Tools ✅

**Goal**: Update all scripts to use new packages (with fallback)

#### 8.1 Seed Scripts
- [x] `scripts/seed_sp500.py` - Uses maverick_data with fallback
- [x] `scripts/seed_indian_stocks.py` - Uses maverick_data/maverick_india with fallback
- [x] `scripts/seed_concall_mappings.py` - Already had fallback

#### 8.2 Docker Scripts
- [x] `scripts/docker-entrypoint.sh` - Uses new packages with fallback

### Phase 9: Tests ✅

**Goal**: Update test infrastructure to use new packages

- [x] `tests/conftest.py` - New packages with fallback
- [x] Service tests - Dynamic MODULE_PATH for @patch
- [ ] Remaining tests (281 files have fallback imports)

### Phase 10: Docker Configuration ✅

**Goal**: Update Docker for new packages

- [x] `Dockerfile` - PYTHONPATH includes new packages
- [x] `docker-compose.yml` - PYTHONPATH environment variable
- [x] Both old and new packages mounted for hot-reload
- [ ] Full removal of maverick_mcp (requires 340+ file updates)

---

## Current Status (2025-11-29)

### Completed Infrastructure

| Component | Package | Status |
|-----------|---------|--------|
| Circuit Breaker | maverick-core | ✅ |
| Exceptions | maverick-core | ✅ |
| Validation | maverick-core | ✅ |
| Logging | maverick-core | ✅ |
| Resilience | maverick-core | ✅ |
| Config | maverick-core | ✅ |
| Date Utils | maverick-core | ✅ |
| Models | maverick-data | ✅ |
| Session/Engine | maverick-data | ✅ |
| StockDataProvider | maverick-data | ✅ |
| Services (Cache, Fetch, Screen) | maverick-data | ✅ |
| Stock Helpers | maverick-data | ✅ |
| YFinance Pool | maverick-data | ✅ |
| Monitoring | maverick-server | ✅ |
| Agents Router | maverick-server | ✅ |
| Workflows | maverick-backtest | ✅ |
| Analysis | maverick-backtest | ✅ |
| Indian Market | maverick-india | ✅ |
| Concall | maverick-india | ✅ |

### Remaining Work

There are still **1,111+ imports from maverick_mcp** across **340 files**.

**Strategy**: Keep maverick_mcp in Docker until all imports are migrated.
All new code should import from new packages; legacy code will use fallbacks.

---

## Migration Strategy

### Approach: Gradual Migration with Compatibility Layer

1. **Keep Legacy Working**: Maintain `maverick_mcp` imports working during migration
2. **Create Aliases**: Add re-exports in legacy modules pointing to new packages
3. **Update Incrementally**: Migrate one module at a time
4. **Test Continuously**: Run full test suite after each module migration
5. **Docker Last**: Only update Docker once all migrations complete

### Example: Creating Compatibility Alias

```python
# In maverick_mcp/utils/logging.py (legacy)
# Add re-export to new location
try:
    from maverick_core.logging import get_logger, setup_logging
except ImportError:
    # Keep legacy implementation as fallback
    def get_logger(name):
        ...
```

---

## Files to Create/Update

### New Package Additions Needed

| Package | Missing Component | Priority |
|---------|-------------------|----------|
| maverick-data | `bulk_insert_*` functions | HIGH |
| maverick-data | `SessionLocal`, `engine` | HIGH |
| maverick-data | `StockDataProvider` | HIGH |
| maverick-data | `MarketDataProvider` | HIGH |
| maverick-core | `get_settings`, `settings` | HIGH |
| maverick-core | `get_logger` | HIGH |
| maverick-india | `CurrencyConverter` | MEDIUM |
| maverick-india | `RBIDataProvider` | MEDIUM |
| maverick-server | All routers | HIGH |
| maverick-server | Main server entry | HIGH |

---

## Success Criteria

- [ ] All 340 files updated to use new package imports
- [ ] Zero imports from `maverick_mcp` in production code
- [ ] All tests passing with new imports
- [ ] Docker builds without `maverick_mcp` directory
- [ ] Performance benchmarks unchanged
- [ ] All MCP tools functional

---

## Timeline Estimate

| Phase | Estimated Effort | Priority |
|-------|------------------|----------|
| Phase 1: Data Layer | 4-6 hours | HIGH |
| Phase 2: Providers | 4-6 hours | HIGH |
| Phase 3: Config & Utils | 3-4 hours | HIGH |
| Phase 4: Domain | 2-3 hours | MEDIUM |
| Phase 5: API Layer | 4-6 hours | HIGH |
| Phase 6: Agents | ✅ Complete | - |
| Phase 7: Scripts | 2-3 hours | LOW |
| Phase 8: Tests | 4-6 hours | LOW |
| **Total** | **~25-35 hours** | - |

---

## Next Steps

1. Start with **Phase 1.1**: Migrate remaining data model functions
2. Then **Phase 3.1**: Migrate `get_settings` and configuration
3. Then **Phase 2.1**: Migrate stock data providers
4. Continue through remaining phases

---

*Last Updated: 2025-11-29*
*Status: In Progress*

