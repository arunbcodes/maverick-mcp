# Maverick MCP Server

FastMCP-based server providing stock analysis tools for Claude Desktop.

## Overview

This package provides the MCP server implementation that combines all Maverick packages:

- **maverick-core**: Interfaces and domain entities
- **maverick-data**: Data access and caching
- **maverick-capabilities**: Capability registry, orchestration, and audit logging
- **maverick-agents**: AI/LLM agents (optional)
- **maverick-backtest**: Backtesting engine (optional)
- **maverick-india**: Indian market support (optional)

## Installation

```bash
# Base server (US market support only)
pip install maverick-server

# With all features
pip install maverick-server[full]

# With specific features
pip install maverick-server[agents]     # AI agents
pip install maverick-server[backtest]   # Backtesting
pip install maverick-server[india]      # Indian market
```

Or with uv:

```bash
uv add maverick-server
uv add maverick-server --optional full
```

## Running the Server

```bash
# SSE transport (recommended for Claude Desktop)
python -m maverick_server --transport sse --port 8003

# HTTP Streamable transport
python -m maverick_server --transport streamable-http --port 8003

# STDIO transport (direct connection)
python -m maverick_server --transport stdio
```

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "maverick-mcp": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8003/sse"]
    }
  }
}
```

## Available Tools

The server provides 35+ tools organized into groups:

- **Data Tools**: Stock data, quotes, company info
- **Technical Analysis**: RSI, MACD, Bollinger Bands, etc.
- **Screening**: Maverick bullish/bearish, breakout detection
- **Portfolio**: Position tracking, correlation analysis
- **Research**: Deep financial research with AI (optional)
- **Backtesting**: Strategy testing and optimization (optional)
- **Indian Market**: NSE/BSE support, economic indicators (optional)

## Architecture

This package follows a thin orchestration layer pattern:

```
maverick-server (MCP interface)
├── maverick-core (shared interfaces)
├── maverick-data (data access)
├── maverick-capabilities (registry, orchestration, audit)
├── maverick-agents (AI agents) [optional]
├── maverick-backtest (backtesting) [optional]
└── maverick-india (Indian market) [optional]
```

## Capabilities Integration

The server integrates with the capabilities package for:

### Automatic Initialization

On server startup, capabilities are automatically initialized:

```python
# In __main__.py
from maverick_server.capabilities_integration import initialize_capabilities
initialize_capabilities()  # Registers 25 capabilities
```

### Audit Logging

All tool executions are automatically logged via the `@with_audit` decorator:

```python
from maverick_server.capabilities_integration import with_audit

@mcp.tool()
@with_audit("screening_get_maverick_stocks")
async def screening_get_maverick_stocks(limit: int = 20):
    """Tool with automatic audit logging."""
    ...
```

### System Introspection Tools

The following MCP tools are automatically registered:

- `system_list_capabilities` - List all registered capabilities
- `system_get_capability` - Get capability details
- `system_get_audit_stats` - Get audit statistics
- `system_get_recent_executions` - Get recent execution events

## Dependencies

- FastMCP: MCP server framework
- uvicorn: ASGI server
- FastAPI: HTTP framework
- maverick-core: Core interfaces
- maverick-data: Data access
- maverick-capabilities: Capability registry and orchestration
