# ChatGPT Integration Setup

Connect Maverick MCP to ChatGPT for AI-powered stock analysis through custom connectors.

!!! warning "Beta Feature"
    ChatGPT's MCP connector support is currently in **BETA** (as of November 2025). Some features may have compatibility issues. For a production-ready experience, we recommend using [Claude Desktop](claude-desktop-setup.md) which has full MCP support.

## Prerequisites

- **ChatGPT Plus or Pro subscription** ($20/month) - Required for custom connectors
- **Docker Desktop or Rancher Desktop** - For running the MCP server
- **Cloudflare Tunnel** (free) - For exposing local server to public HTTPS endpoint
- **API Keys** - At minimum, `TIINGO_API_KEY` for stock data

## Overview

ChatGPT integration requires:

1. Running Maverick MCP server with **Streamable-HTTP transport**
2. Exposing the server via **Cloudflare Tunnel** (public HTTPS endpoint)
3. Configuring **ChatGPT Custom Connector** with the tunnel URL

## Step 1: Docker Configuration

### Required Docker Changes

ChatGPT requires the MCP server to use **Streamable-HTTP transport** (not SSE). This is already configured in the `docker-compose.yml` file.

#### Verify docker-compose.yml

Ensure your `docker-compose.yml` has the following command override for the backend service:

```yaml
services:
  backend:
    build: .
    command: ["uv", "run", "python", "-m", "maverick_server", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
    ports:
      - "8003:8000"
    environment:
      # ... your environment variables
```

**Key Point**: The `--transport streamable-http` flag is critical for ChatGPT compatibility.

### Environment Setup

Create a `.env` file with your API keys:

```bash
# Required - Stock data provider
TIINGO_API_KEY=your-tiingo-key

# Optional - Enhanced features
OPENROUTER_API_KEY=your-openrouter-key
EXA_API_KEY=your-exa-key
FRED_API_KEY=your-fred-key
```

### Start Docker Containers

```bash
# Start all containers (backend, postgres, redis)
docker-compose up -d

# Verify backend is running with Streamable-HTTP
docker logs maverick-mcp-backend-1 | grep "Transport"
# Should show: 📦 Transport: Streamable-HTTP

# Check server URL
docker logs maverick-mcp-backend-1 | grep "Server URL"
# Should show: 🔗 Server URL: http://0.0.0.0:8000/mcp/
```

**Verify the server is accessible**:

```bash
curl http://localhost:8003/mcp/ -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"ping","id":1}'
```

You should get a successful response (not 404 or 400).

## Step 2: Cloudflare Tunnel Setup

ChatGPT needs a **public HTTPS endpoint** to connect to your local MCP server. Cloudflare Tunnel provides this for free without requiring a Cloudflare account (though production use should use named tunnels).

### Option A: Quick Tunnel (Testing - Recommended)

**Install cloudflared locally** (in project directory):

```bash
# Download ARM64 binary for macOS (Apple Silicon)
curl -L https://github.com/cloudflare/cloudflared/releases/download/2025.11.1/cloudflared-darwin-arm64.tgz -o cloudflared.tgz
tar -xzf cloudflared.tgz
rm cloudflared.tgz
chmod +x cloudflared

# For Intel Macs, use:
# curl -L https://github.com/cloudflare/cloudflared/releases/download/2025.11.1/cloudflared-darwin-amd64.tgz -o cloudflared.tgz
```

**Start the tunnel**:

```bash
./cloudflared tunnel --url http://localhost:8003
```

You'll see output like:

```
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
|  https://random-words-subdomain.trycloudflare.com                              |
+--------------------------------------------------------------------------------------------+
```

**Copy the tunnel URL** - you'll need it for ChatGPT configuration.

!!! warning "Temporary URL"
    Quick tunnels generate a **new random URL each time** you restart the tunnel. For production use, create a named tunnel with a Cloudflare account.

### Option B: Named Tunnel (Production)

For a permanent URL:

1. Create free Cloudflare account
2. Install cloudflared: `brew install cloudflare/cloudflare/cloudflared`
3. Authenticate: `cloudflared tunnel login`
4. Create named tunnel: `cloudflared tunnel create maverick-mcp`
5. Configure DNS: Point subdomain to tunnel
6. Run tunnel: `cloudflared tunnel run maverick-mcp`

See [Cloudflare documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) for details.

## Step 3: ChatGPT Connector Configuration

### Enable Developer Mode

1. Go to [ChatGPT](https://chatgpt.com)
2. Click your **profile icon** (bottom-left corner)
3. Navigate to **Settings** → **Connectors**
4. Scroll to **Advanced Settings**
5. Toggle **Enable Developer Mode** to ON

### Add MCP Server Connector

1. In the Connectors section, click **Add Connector**
2. Configure:
   - **Name**: `Maverick MCP` (or any name you prefer)
   - **Description** (optional): `Stock analysis and technical indicators`
   - **MCP Server URL**: `https://your-tunnel-url.trycloudflare.com/mcp/`
   - **Authentication**: `No authentication`

!!! danger "Critical: Include Trailing Slash"
    The URL **must** end with `/mcp/` (including the trailing slash). Wrong: `https://example.com/mcp` ✗ Correct: `https://example.com/mcp/` ✓

3. Acknowledge security warning:
   - Check "I understand and want to continue"
   - Read the security implications
4. Click **Create**

### Verify Connection

ChatGPT will attempt to connect to the server. Check your Docker logs:

```bash
docker logs -f maverick-mcp-backend-1
```

You should see POST requests from ChatGPT:

```
INFO:     172.19.0.1:xxxxx - "POST /mcp/ HTTP/1.1" 200 OK
DEBUG    Handler called: list_tools
```

## Step 4: Using MCP Tools in ChatGPT

### Explicit Connector Reference

ChatGPT may not automatically use custom connectors. **Mention the connector explicitly**:

```
"Using the Maverick MCP connector, show me technical analysis for AAPL"

"Use Maverick MCP to get bullish stock recommendations"

"Through the MCP connector, analyze portfolio risk for MSFT, GOOGL, AAPL"
```

### Example Queries

Try these to test your integration:

**Stock Analysis**:
```
Using Maverick MCP connector, get real-time data for AAPL with RSI and MACD indicators
```

**Screening**:
```
Use Maverick MCP to show me top 10 momentum stocks from S&P 500
```

**Portfolio Analysis**:
```
Through Maverick MCP, calculate correlation matrix for MSFT, GOOGL, AMZN
```

**Indian Market**:
```
Using Maverick MCP, get bullish screening recommendations for NSE stocks
```

### Available Tools

When connected, you have access to 35+ MCP tools including:

- **Stock Data**: Historical prices, company info, real-time quotes
- **Technical Analysis**: RSI, MACD, Bollinger Bands, moving averages
- **Screening**: Maverick Bullish/Bearish, breakout patterns
- **Portfolio**: Optimization, risk analysis, correlation
- **Indian Market**: NSE/BSE screening, economic indicators
- **Research**: AI-powered company research, sentiment analysis
- **Backtesting**: Strategy testing with 15+ algorithms

See [MCP Tools Reference](../user-guide/mcp-tools-reference.md) for complete list.

## Known Issues & Limitations

### Current Limitations (November 2025)

!!! bug "Beta Compatibility Issues"
    ChatGPT's MCP support is in beta and may have intermittent connection issues:

    - **400 Bad Request errors** - ChatGPT's client may not send required headers
    - **Connector disappears** - May need to re-add after ChatGPT updates
    - **Inconsistent tool discovery** - Sometimes requires explicit connector mention
    - **No streaming support** - Large responses may timeout

### Common Errors

#### "400 Bad Request"

**Symptom**: ChatGPT shows "400: Client error" when calling tools

**Cause**: ChatGPT's MCP client not sending required `text/event-stream` Accept header

**Solution**:
- Verify server is using `streamable-http` transport (not `sse`)
- Check Docker logs for detailed error messages
- This is a known beta compatibility issue with ChatGPT

**Temporary Workaround**: Use [Claude Desktop](claude-desktop-setup.md) which has full MCP support

#### "Connection Failed"

**Symptom**: Connector creation fails or shows connection error

**Causes & Solutions**:

1. **Tunnel not running**: Start cloudflared tunnel
2. **Wrong URL**: Ensure URL ends with `/mcp/` (trailing slash required)
3. **Server not ready**: Check `docker ps` - backend should be "Up"
4. **Port mismatch**: Verify tunnel points to `localhost:8003` (not 8000)

#### "libta-lib.so.0: cannot open shared object file"

**Symptom**: Technical analysis tools fail with library error

**Cause**: TA-Lib libraries not properly copied in Docker build

**Solution**: Rebuild Docker image (this is fixed in latest Dockerfile):

```bash
docker-compose build backend --no-cache
docker-compose up -d backend
```

## Troubleshooting

### Check Docker Container Status

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

All three containers should be "Up":
- `maverick-mcp-backend-1` - Main MCP server
- `maverick-mcp-postgres-1` - Database
- `maverick-mcp-redis-1` - Cache

### Check Backend Logs

```bash
# Real-time logs
docker logs -f maverick-mcp-backend-1

# Check for errors
docker logs maverick-mcp-backend-1 | grep -i error

# Verify transport
docker logs maverick-mcp-backend-1 | grep "Transport"
```

### Verify TA-Lib Libraries

```bash
# Check if TA-Lib is installed
docker exec maverick-mcp-backend-1 ls -la /usr/local/lib/ | grep -i ta

# Should show:
# libta-lib.so
# libta-lib.so.0
# libta-lib.so.0.0.0
```

### Test Endpoint Directly

```bash
# Test local endpoint
curl -X POST http://localhost:8003/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"ping","id":1}'

# Test through tunnel
curl -X POST https://your-tunnel-url.trycloudflare.com/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"ping","id":1}'
```

Both should return success (not 404 or 400).

### Restart Everything

If all else fails, full restart:

```bash
# Stop containers
docker-compose down

# Rebuild backend with fixed dependencies
docker-compose build backend --no-cache

# Start fresh
docker-compose up -d

# Restart tunnel
./cloudflared tunnel --url http://localhost:8003

# Update ChatGPT connector with new tunnel URL
```

## Production Considerations

### Security

!!! danger "Security Warning"
    Quick tunnels expose your local server to the internet without authentication. For production:

    - Use **named tunnels** with Cloudflare accounts
    - Enable **authentication** (API keys, OAuth)
    - Implement **rate limiting**
    - Monitor **access logs**
    - Use **environment-specific configs**

### Monitoring

Track connector usage:

```bash
# Monitor requests
docker logs -f maverick-mcp-backend-1 | grep "POST /mcp"

# Watch for errors
docker logs -f maverick-mcp-backend-1 | grep -i error

# Check tunnel status
# Tunnel logs show request counts and errors
```

### Cost Optimization

- **Cloudflare Tunnel**: Free (but no uptime guarantee for quick tunnels)
- **ChatGPT Plus**: $20/month (required for connectors)
- **API Keys**: Tiingo free tier includes 500 requests/day
- **Server Hosting**: Free if running locally

## Alternative: Claude Desktop

If you encounter persistent issues with ChatGPT integration, **Claude Desktop** provides better MCP support:

**Advantages**:
- ✅ Full MCP protocol support
- ✅ No public HTTPS endpoint required
- ✅ Direct STDIO connection (faster)
- ✅ More stable and mature
- ✅ Better error messages

**Setup**: See [Claude Desktop Setup Guide](claude-desktop-setup.md)

## Getting Help

If issues persist:

1. **Check logs**: Docker backend logs show detailed error messages
2. **GitHub Issues**: [Report bugs](https://github.com/arunbcodes/maverick-mcp/issues)
3. **Documentation**: [Troubleshooting Guide](../user-guide/troubleshooting.md)
4. **Alternative**: Try [Claude Desktop](claude-desktop-setup.md) for production use

## Next Steps

- [MCP Tools Reference](../user-guide/mcp-tools-reference.md) - Complete list of available tools
- [Examples](../user-guide/examples.md) - Sample queries and use cases
- [Best Practices](../user-guide/best-practices.md) - Optimization tips
- [Troubleshooting](../user-guide/troubleshooting.md) - Common issues and solutions
