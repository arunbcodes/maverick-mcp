# Maverick MCP Server

FastMCP-based server providing stock analysis tools for Claude Desktop.

## Overview

This package provides the MCP server implementation that combines all Maverick packages:

- **maverick-core**: Interfaces and domain entities
- **maverick-data**: Data access and caching
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
├── maverick-agents (AI agents) [optional]
├── maverick-backtest (backtesting) [optional]
└── maverick-india (Indian market) [optional]
```

## Dependencies

- FastMCP: MCP server framework
- uvicorn: ASGI server
- FastAPI: HTTP framework
- maverick-core: Core interfaces
- maverick-data: Data access
