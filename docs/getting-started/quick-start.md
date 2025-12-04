# Quick Start Guide

Get Maverick MCP up and running in minutes!

## Choose Your Setup

=== "🐳 Docker (Recommended)"

    The fastest way to get started with the full stack (Web UI + API + MCP).

    ### Prerequisites
    - **Docker** and **Docker Compose** installed
    - **Tiingo API key** (free at [tiingo.com](https://tiingo.com))

    ### Steps

    ```bash
    # 1. Clone repository
    git clone https://github.com/arunbcodes/maverick-mcp.git
    cd maverick-mcp

    # 2. Configure environment
    cp docker/env.example docker/.env
    # Edit docker/.env and add your TIINGO_API_KEY

    # 3. Start all services
    make docker-full-up

    # 4. Access the dashboard
    open http://localhost:3000
    ```

    **Services Running:**

    | Service | URL | Description |
    |---------|-----|-------------|
    | Web Dashboard | http://localhost:3000 | Main UI |
    | REST API | http://localhost:8000 | API endpoints |
    | API Docs | http://localhost:8000/docs | Swagger UI |
    | MCP Server | http://localhost:8003 | For Claude/Cursor |

    For more details, see the [Docker Guide](../deployment/docker.md).

=== "🐍 Local Python"

    For development or when you don't need the Web UI.

    ### Prerequisites
    - **Python 3.12+** installed
    - **[uv](https://docs.astral.sh/uv/)** package manager (recommended) or pip
    - **Git** for cloning the repository
    - **Tiingo API key** (free tier available at [tiingo.com](https://tiingo.com))

    ### Optional (Recommended)
    - **OpenRouter API key** for AI features ([openrouter.ai](https://openrouter.ai))
    - **OpenAI API key** for embeddings/RAG ([platform.openai.com](https://platform.openai.com))
    - **Redis** for enhanced caching performance

---

## Local Python Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/arunbcodes/maverick-mcp.git
cd maverick-mcp
```

### Step 2: Install Dependencies

=== "Using uv (Recommended)"

    ```bash
    # Install uv if you haven't already
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Install dependencies
    uv sync
    ```

=== "Using pip"

    ```bash
    # Create virtual environment
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate

    # Install dependencies
    pip install -e .
    ```

### Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```ini
# Required - Stock data provider
TIINGO_API_KEY=your-tiingo-key-here

# Recommended - AI features
OPENROUTER_API_KEY=your-openrouter-key-here

# Optional - For RAG Q&A
OPENAI_API_KEY=your-openai-key-here

# Optional - For enhanced data
FRED_API_KEY=your-fred-key-here
EXA_API_KEY=your-exa-key-here

# Optional - Database (uses SQLite by default)
# DATABASE_URL=postgresql://localhost/maverick_mcp

# Optional - Redis caching
# REDIS_HOST=localhost
# REDIS_PORT=6379
```

!!! tip "Get Free API Keys"
    - **Tiingo**: Free tier includes 500 requests/day - [Sign up](https://tiingo.com)
    - **OpenRouter**: Pay-as-you-go pricing, access to 400+ models - [Sign up](https://openrouter.ai)
    - **OpenAI**: Required only for RAG features - [Sign up](https://platform.openai.com)

### Step 4: Initialize Database

The database will be automatically initialized on first run with 520+ S&P 500 stocks:

```bash
make dev
```

This will:
- Create SQLite database (or connect to PostgreSQL if configured)
- Seed S&P 500 companies and screening data
- Start the MCP server on port 8003

## Verify Installation

Check that the server is running:

```bash
# Check if server is listening
lsof -i :8003

# You should see:
# COMMAND   PID   USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
# Python  12345  abalak   8u  IPv4 0x1234567890abcdef      0t0  TCP *:8003 (LISTEN)
```

## Connect to Claude Desktop

### Method A: SSE Transport (Recommended - Most Stable)

1. **Ensure server is running**:
   ```bash
   make dev  # Server runs on port 8003
   ```

2. **Configure Claude Desktop**:

   Edit your Claude Desktop config file:

   === "macOS"
       ```bash
       nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
       ```

   === "Windows"
       ```bash
       notepad %APPDATA%\Claude\claude_desktop_config.json
       ```

   === "Linux"
       ```bash
       nano ~/.config/Claude/claude_desktop_config.json
       ```

3. **Add this configuration**:
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

   !!! warning "Critical: Trailing Slash Required"
       The `/sse/` endpoint **must** include the trailing slash to prevent 307 redirects that cause tools to disappear!

4. **Restart Claude Desktop** completely

5. **Test the connection**:
   ```
   User: "List available tools"
   Claude: [Shows 40+ Maverick MCP tools including conference call tools]
   ```

### Method B: HTTP Streamable (Alternative)

Follow the same steps but use:
```json
{
  "mcpServers": {
    "maverick-mcp": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8003/mcp/"]
    }
  }
}
```

## Quick Test

Try these commands in Claude Desktop:

### Stock Analysis
```
Get technical analysis for AAPL
```

### Conference Call Analysis
```
Fetch the transcript for RELIANCE.NS Q1 2025
```

```
Summarize the TCS Q4 2024 earnings call
```

```
What did management say about revenue growth in the INFY Q1 2025 call?
```

### Stock Screening
```
Show me the top Maverick bullish stocks
```

### Portfolio Analysis
```
Add AAPL 10 shares at $150 to my portfolio
Compare AAPL vs MSFT performance
```

## Common Commands

### Development
```bash
make dev          # Start server
make stop         # Stop server
make tail-log     # Follow logs
make test         # Run tests
make lint         # Check code quality
```

### Database
```bash
make migrate      # Run migrations
make setup        # Initial setup
```

### Utilities
```bash
make clean        # Clean temporary files
make redis-start  # Start Redis (if using caching)
```

## Troubleshooting

### Server won't start
```bash
make stop          # Stop any running processes
make clean         # Clean temporary files
make dev           # Restart
```

### Port already in use
```bash
lsof -i :8003      # Find what's using port 8003
kill -9 <PID>      # Kill the process
make dev           # Restart
```

### Claude Desktop not connecting
1. Verify server is running: `lsof -i :8003`
2. Check config syntax in `claude_desktop_config.json`
3. Ensure you're using the SSE endpoint with trailing slash
4. Restart Claude Desktop completely
5. Check logs: `make tail-log`

### Tools disappearing after initial connection
This usually means missing trailing slash in the SSE endpoint. Use:
```json
"args": ["-y", "mcp-remote", "http://localhost:8003/sse/"]
```

NOT:
```json
"args": ["-y", "mcp-remote", "http://localhost:8003/sse"]
```

## Next Steps

Now that you're up and running:

- 📖 [Learn about Configuration](configuration.md)
- 📞 [Explore Conference Call Analysis](../concall/overview.md)
- 🔧 [Configure Claude Desktop properly](claude-desktop-setup.md)
- 📚 [Browse MCP Tools Reference](../user-guide/mcp-tools-reference.md)
- 💡 [See Examples](../user-guide/examples.md)

## Need Help?

- 📖 Check the [FAQ](../about/faq.md)
- 🐛 [Report Issues](https://github.com/arunbcodes/maverick-mcp/issues)
- 📚 Read the [Troubleshooting Guide](../user-guide/troubleshooting.md)
