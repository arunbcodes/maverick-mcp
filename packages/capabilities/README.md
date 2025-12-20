# Maverick Capabilities

Capability registry, orchestration abstraction, audit logging, and async task queue for MaverickMCP.

## Overview

The capabilities package provides a centralized abstraction layer between MCP tools/REST API endpoints and the underlying services. It enables:

- **Unified Capability Registry**: Single source of truth for all capabilities
- **Swappable Orchestrators**: Execute capabilities through different backends
- **Audit Logging**: Compliance-ready logging with query support
- **Async Task Queue**: Long-running task execution with progress tracking

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MCP Server / REST API                             │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ @with_audit  │  │ @with_audit  │  │ @with_audit  │               │
│  │  Screening   │  │  Portfolio   │  │  Technical   │  ...          │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Capabilities Layer                               │
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │    Registry     │  │   Orchestrator  │  │    Audit Logger     │  │
│  │   (25 caps)     │  │   (Service)     │  │  (Memory/Database)  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      Task Queue                               │   │
│  │     MemoryTaskQueue (dev)  │  RedisTaskQueue (production)     │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Services Layer                                   │
│                                                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │ Screening  │  │ Portfolio  │  │ Technical  │  │  Research  │    │
│  │  Service   │  │  Service   │  │  Service   │  │  Service   │    │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## Features

### 1. Capability Registry

Type-safe, IDE-friendly capability definitions with Python dataclasses.

```python
from maverick_capabilities import (
    Capability,
    CapabilityGroup,
    ExecutionConfig,
    MCPConfig,
    get_registry,
)

# Define a capability
capability = Capability(
    id="get_maverick_stocks",
    title="Get Maverick Bullish Stocks",
    description="Get bullish stock picks from S&P 500",
    group=CapabilityGroup.SCREENING,
    service_class=ScreeningService,
    method_name="get_maverick_stocks",
    execution=ExecutionConfig(
        timeout_seconds=30,
        cache_enabled=True,
    ),
    mcp=MCPConfig(
        expose=True,
        tool_name="screening_get_maverick_stocks",
    ),
)

# Register and use
registry = get_registry()
registry.register(capability)

# Query capabilities
mcp_caps = registry.list_mcp()
api_caps = registry.list_api()
screening_caps = registry.list_by_group(CapabilityGroup.SCREENING)
```

### 2. Orchestrator Abstraction

Swappable execution backends with a protocol-based design.

```python
from maverick_capabilities.orchestration import (
    get_orchestrator,
    create_orchestrator,
    OrchestratorType,
)

# Get default orchestrator (ServiceOrchestrator)
orchestrator = get_orchestrator()

# Execute a capability
result = await orchestrator.execute(
    "get_maverick_stocks",
    {"limit": 10}
)

# Check result
if result.status == ExecutionStatus.COMPLETED:
    print(result.result)
else:
    print(f"Error: {result.error}")
```

**Available Orchestrators:**
- `ServiceOrchestrator`: Direct service method calls (default)
- Future: `AgentFieldOrchestrator` for enterprise deployment

### 3. Audit Logging

Compliance-ready audit logging with query support.

```python
from maverick_capabilities.audit import (
    AuditEvent,
    AuditEventType,
    get_audit_logger,
)

# Log an event
audit = get_audit_logger()
await audit.log(AuditEvent(
    event_type=AuditEventType.EXECUTION_COMPLETED,
    capability_id="get_maverick_stocks",
    input_data={"limit": 10},
    output_data={"stocks": [...]},
    duration_ms=150,
))

# Query events
events = await audit.query(
    capability_id="get_maverick_stocks",
    start_time=datetime.now() - timedelta(hours=1),
)

# Get execution trace
trace = await audit.get_execution_trace(execution_id)
```

**Available Loggers:**
- `MemoryAuditLogger`: In-memory storage (development)
- `DatabaseAuditLogger`: PostgreSQL/SQLite persistence (production)

### Enabling Database Audit Logging

To persist audit events to PostgreSQL:

```python
from maverick_server.capabilities_integration import initialize_capabilities
from maverick_data.session import get_async_session_context

# Initialize with database audit logging
initialize_capabilities(
    use_database_audit=True,
    async_session_factory=get_async_session_context,
)
```

Run the migration to create the `audit_logs` table:

```bash
alembic upgrade 019_add_audit_logs
```

The database logger provides:
- Persistent storage for compliance
- Query by capability, user, ticker, time range
- Execution trace reconstruction
- Automatic cleanup of old events

### 4. Async Task Queue

Long-running task execution with progress tracking.

```python
from maverick_capabilities.tasks import (
    TaskConfig,
    TaskPriority,
    get_task_queue,
)

queue = get_task_queue()

# Enqueue a task
result = await queue.enqueue(
    "run_backtest",
    {"ticker": "AAPL", "strategy": "momentum"},
    config=TaskConfig(
        priority=TaskPriority.HIGH,
        timeout_seconds=600,
        webhook_url="https://example.com/webhook",
    ),
)

# Check status
status = await queue.get_status(result.task_id)

# Update progress (from within task)
await queue.update_progress(task_id, percent=50, message="Running...")

# List tasks
tasks = await queue.list_tasks(capability_id="run_backtest")
```

**Available Queues:**
- `MemoryTaskQueue`: In-memory asyncio (development)
- `RedisTaskQueue`: Redis-backed with persistence (production)

## MCP Server Integration

### Automatic Initialization

Capabilities are automatically initialized on server startup:

```python
# In __main__.py
from maverick_server.capabilities_integration import initialize_capabilities

initialize_capabilities()  # Registers 25 capabilities
```

### Audit Middleware

Add audit logging to any MCP tool:

```python
from maverick_server.capabilities_integration import with_audit

@mcp.tool()
@with_audit("screening_get_maverick_stocks")
async def screening_get_maverick_stocks(limit: int = 20):
    """Get bullish stocks with automatic audit logging."""
    # Your implementation
    ...
```

### Capabilities MCP Tools

System introspection tools are automatically registered:

- `system_list_capabilities` - List all registered capabilities
- `system_get_capability` - Get capability details
- `system_get_audit_stats` - Get audit statistics
- `system_get_recent_executions` - Get recent execution events
- `system_execute_capability` - Execute any capability via orchestrator

### Orchestrator-Based Execution

The `system_execute_capability` tool provides universal capability execution:

```python
# Execute any capability through the orchestrator
result = await system_execute_capability(
    capability_id="get_maverick_stocks",
    parameters={"limit": 10}
)

# The orchestrator handles:
# - Timeout management
# - Error handling
# - Audit logging
# - Future: caching, retry logic, AgentField routing
```

You can also use the `execute_capability` function directly in code:

```python
from maverick_server.capabilities_integration import execute_capability

result = await execute_capability("get_maverick_stocks", {"limit": 10})
if result["success"]:
    stocks = result["data"]
else:
    print(f"Error: {result['error']}")
```

## REST API Integration

New endpoints are available at `/api/v1/capabilities`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/capabilities` | GET | List all capabilities |
| `/capabilities/groups` | GET | List capability groups |
| `/capabilities/stats` | GET | Get registry statistics |
| `/capabilities/{id}` | GET | Get capability details |
| `/capabilities/audit/stats` | GET | Get audit statistics |
| `/capabilities/audit/recent` | GET | Get recent executions |

## Capability Groups

| Group | Description | Count |
|-------|-------------|-------|
| `screening` | Stock screening strategies | 5 |
| `portfolio` | Portfolio management | 5 |
| `technical` | Technical analysis | 6 |
| `research` | AI-powered research | 4 |
| `risk` | Risk analytics | 5 |

## Package Structure

```
maverick_capabilities/
├── __init__.py              # Public exports
├── models.py                # Capability, ExecutionConfig, etc.
├── registry.py              # CapabilityRegistry
├── orchestration/
│   ├── protocols.py         # Orchestrator protocol
│   ├── service_orchestrator.py  # ServiceOrchestrator
│   └── factory.py           # get_orchestrator()
├── audit/
│   ├── protocols.py         # AuditLogger protocol
│   ├── memory_logger.py     # MemoryAuditLogger
│   ├── db_logger.py         # DatabaseAuditLogger
│   └── factory.py           # get_audit_logger()
├── tasks/
│   ├── protocols.py         # TaskQueue protocol
│   ├── memory_queue.py      # MemoryTaskQueue
│   ├── redis_queue.py       # RedisTaskQueue
│   └── factory.py           # get_task_queue()
└── definitions/
    ├── screening.py         # Screening capabilities
    ├── portfolio.py         # Portfolio capabilities
    ├── technical.py         # Technical capabilities
    ├── research.py          # Research capabilities
    └── risk.py              # Risk capabilities
```

## Testing

```bash
# Run all tests
uv run pytest packages/capabilities/tests/ -v

# Run with coverage
uv run pytest packages/capabilities/tests/ --cov=maverick_capabilities

# Run specific test
uv run pytest packages/capabilities/tests/test_registry.py -v
```

**Test Coverage:**
- 39 tests covering registry, orchestrator, and audit
- Unit tests for all core components
- Integration tests for MCP/API integration

## Future: AgentField Migration

The orchestrator abstraction enables future migration to AgentField:

```python
from maverick_capabilities.orchestration import (
    set_orchestrator,
    OrchestratorType,
)

# Switch to AgentField (when implemented)
set_orchestrator(
    orchestrator_type=OrchestratorType.AGENTFIELD,
    control_plane_url="http://localhost:8080",
)

# Everything else stays the same!
result = await orchestrator.execute("get_maverick_stocks", {"limit": 10})
```

## Dependencies

- `maverick-schemas`: Shared Pydantic models
- `maverick-core`: Core configuration and logging
- `maverick-data`: Database models
- `maverick-services`: Domain services
- `pydantic>=2.0.0`: Data validation
- `redis>=5.0.0`: Redis client (optional)
