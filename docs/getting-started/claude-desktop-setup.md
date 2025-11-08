# Claude Desktop Setup

Detailed guide for connecting Maverick MCP to Claude Desktop.

## Recommended Configuration (SSE Transport)

```json
{
  "mcpServers": {
    "maverick-mcp": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8003/sse/"]
    }
  }
}
```

[See Quick Start for complete instructions →](quick-start.md#connect-to-claude-desktop)
