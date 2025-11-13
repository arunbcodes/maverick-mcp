# Docker Deployment Guide

Complete guide for running Maverick MCP in Docker containers.

## Overview

Maverick MCP provides a production-ready Docker setup with:

- **Multi-stage Dockerfile** with optimized builder and runtime stages (50%+ smaller images)
- **Multi-container architecture** (Backend, PostgreSQL, Redis)
- **Production Docker Compose** with health checks, resource limits, and PostgreSQL tuning
- **Development tools stack** (pgAdmin, Redis Commander, Prometheus, Grafana, Portainer)
- **Environment-specific configurations** (.env files for development, production, testing)
- **CI/CD pipeline** with automated testing, multi-arch builds, and security scanning
- **Persistent volumes** for data retention
- **Non-root user** for security
- **Custom ports** to avoid conflicts
- **Health checks** for all services
- **Resource limits** to prevent overconsumption

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Docker Compose Stack                                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────┐        │
│  │  Maverick MCP Backend                      │        │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │        │
│  │  • Python 3.12-slim base image             │        │
│  │  • FastMCP 2.0 with SSE transport          │        │
│  │  • TA-Lib compiled from source             │        │
│  │  • uv for fast package management          │        │
│  │  • Port: 8003 (host) → 8000 (container)   │        │
│  │  • Non-root user (maverick:1000)           │        │
│  │  • Volume mounts for live development      │        │
│  └────────────────────────────────────────────┘        │
│              ↓ depends_on ↓                             │
│                                                          │
│  ┌──────────────────────┐  ┌──────────────────────┐   │
│  │  PostgreSQL 15       │  │  Redis 7              │   │
│  │  ━━━━━━━━━━━━━━━━  │  │  ━━━━━━━━━━━━━━━━━  │   │
│  │  • Alpine Linux      │  │  • Alpine Linux       │   │
│  │  • Port: 55432       │  │  • Port: 56379        │   │
│  │  • Persistent volume │  │  • Persistent volume  │   │
│  │    (postgres-data)   │  │    (redis-data)       │   │
│  └──────────────────────┘  └──────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Service Details

| Service | Image | Port (Host:Container) | Purpose | Volume |
|---------|-------|----------------------|---------|--------|
| **backend** | Custom (Python 3.12) | 8003:8000 | MCP Server | Code mounts |
| **postgres** | postgres:15-alpine | 55432:55432 | Database | postgres-data |
| **redis** | redis:7-alpine | 56379:56379 | Cache | redis-data |

## Prerequisites

### Required Software

**Option 1: Docker Desktop**
- macOS: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
- Windows: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
- Linux: [Install Docker Engine](https://docs.docker.com/engine/install/)

**Option 2: Rancher Desktop (Recommended for macOS)**
- [Download Rancher Desktop](https://rancherdesktop.io/)
- Free and open source
- Lighter than Docker Desktop
- See [Rancher Desktop Guide](rancher-desktop.md) for setup

### Verify Installation

```bash
# Check Docker is installed
docker --version
# Output: Docker version 24.0.x, build ...

# Check docker-compose is installed
docker-compose --version
# Output: Docker Compose version v2.x.x

# Test Docker is running
docker ps
# Should show empty table (no error)
```

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/arunbcodes/maverick-mcp.git
cd maverick-mcp
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your API keys
nano .env  # or vim, code, etc.
```

**Required Configuration (`.env`):**
```bash
# Required - Stock data provider
TIINGO_API_KEY=your-tiingo-api-key-here

# Optional - Enhanced features
OPENROUTER_API_KEY=your-openrouter-key  # AI research
EXA_API_KEY=your-exa-key                # Web search
OPENAI_API_KEY=your-openai-key          # RAG embeddings
FRED_API_KEY=your-fred-key              # Macro data

# Auto-configured by docker-compose (don't change)
DATABASE_URL=postgresql://postgres:postgres@postgres:55432/maverick_mcp
REDIS_HOST=redis
REDIS_PORT=56379
```

### 3. Start Services

**Method 1: Using Makefile (Recommended)**
```bash
# Start all services
make docker-up

# View logs
make docker-logs

# Stop all services
make docker-down
```

**Method 2: Direct docker-compose**
```bash
# Start in background
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Verify Services

```bash
# Check all containers are running
docker ps

# Expected output:
# CONTAINER ID   IMAGE                    STATUS         PORTS
# xxxx          maverick-mcp-backend-1   Up 30 seconds  0.0.0.0:8003->8000/tcp
# yyyy          postgres:15-alpine       Up 30 seconds  0.0.0.0:55432->55432/tcp
# zzzz          redis:7-alpine           Up 30 seconds  0.0.0.0:56379->56379/tcp

# Test MCP server is responding
curl http://localhost:8003/sse/
# Should return SSE connection or JSON response

# Test health endpoint (if implemented)
curl http://localhost:8003/health
```

### 5. Connect Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

**Important**: Note the trailing slash in `/sse/` - this is required to prevent redirect issues!

Restart Claude Desktop and test:
```
Show me technical analysis for AAPL
```

## MCP Transport Configuration

Maverick MCP supports multiple transport protocols for different MCP clients:

### Transport Options

| Transport | MCP Client | Use Case | Endpoint |
|-----------|-----------|----------|----------|
| **SSE** (Server-Sent Events) | Claude Desktop, Cursor IDE | Direct SSE connections | `/sse/` |
| **Streamable-HTTP** | ChatGPT, Claude Code CLI | HTTP-based with SSE support | `/mcp/` |
| **STDIO** | Local clients | Process-based communication | N/A |

### Default Configuration

The default `docker-compose.yml` uses **Streamable-HTTP transport** for broad compatibility:

```yaml
services:
  backend:
    command: ["uv", "run", "python", "-m", "maverick_mcp.api.server", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
```

This configuration:
- ✅ Works with ChatGPT custom connectors
- ✅ Compatible with Claude Desktop (via mcp-remote bridge)
- ✅ Supports Claude Code CLI
- ✅ Enables HTTP-based MCP protocol

### Switching to SSE Transport

For direct SSE connections (Claude Desktop without mcp-remote), override the command in `docker-compose.override.yml`:

```yaml
services:
  backend:
    command: ["uv", "run", "python", "-m", "maverick_mcp.api.server", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
```

**When to use SSE**:
- Direct connections from Claude Desktop, Cursor IDE
- Lower latency for local clients
- Simpler architecture without HTTP overhead

**When to use Streamable-HTTP**:
- ChatGPT integration via Cloudflare Tunnel
- Remote access requirements
- Need both HTTP and SSE support
- Multiple client types

### Verifying Transport Configuration

Check which transport is running:

```bash
docker logs maverick-mcp-backend-1 | grep "Transport"
```

**SSE Transport**:
```
📦 Transport:       SSE
🔗 Server URL:      http://0.0.0.0:8000/sse
```

**Streamable-HTTP Transport**:
```
📦 Transport:       Streamable-HTTP
🔗 Server URL:      http://0.0.0.0:8000/mcp/
```

### ChatGPT Integration Notes

For ChatGPT custom connectors, **Streamable-HTTP is required**. See [ChatGPT Setup Guide](../getting-started/chatgpt-setup.md) for complete configuration instructions including:

- Docker transport configuration
- Cloudflare Tunnel setup
- Custom connector configuration
- Troubleshooting common issues

## Development Workflow

### Development Mode with Hot Reload

**1. Create Override File**
```bash
cp docker-compose.override.yml.example docker-compose.override.yml
```

**2. Edit Override Configuration**
```yaml
# docker-compose.override.yml
services:
  backend:
    # Enable hot reload (using streamable-http for compatibility)
    command: uv run python -m maverick_mcp.api.server --transport streamable-http --host 0.0.0.0 --port 8000 --reload

    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=debug
      - API_DEBUG=true

    # Interactive debugging
    stdin_open: true
    tty: true
```

!!! tip "SSE Transport for Development"
    If you're only using Claude Desktop locally, you can use `--transport sse` for slightly lower latency. However, `streamable-http` is recommended as the default for compatibility with all clients.

**3. Restart with Development Config**
```bash
docker-compose up --build
# Now code changes will auto-reload the server
```

### Common Development Tasks

**View Logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f redis

# Last 100 lines
docker-compose logs --tail=100 backend
```

**Execute Commands in Container**
```bash
# Access backend shell
docker-compose exec backend /bin/sh

# Run Python commands
docker-compose exec backend python -c "print('Hello')"

# Run tests
docker-compose exec backend uv run pytest

# Database migrations
docker-compose exec backend uv run alembic upgrade head
```

**Database Access**
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d maverick_mcp

# Run SQL query
docker-compose exec postgres psql -U postgres -d maverick_mcp -c "SELECT * FROM stocks LIMIT 5;"

# Dump database
docker-compose exec postgres pg_dump -U postgres maverick_mcp > backup.sql
```

**Redis Access**
```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli -p 56379

# Check cache keys
docker-compose exec redis redis-cli -p 56379 KEYS "*"

# Get cache statistics
docker-compose exec redis redis-cli -p 56379 INFO stats
```

**Restart Single Service**
```bash
# Restart backend only
docker-compose restart backend

# Rebuild and restart
docker-compose up --build -d backend
```

## Configuration Options

### Environment Variables

All environment variables can be configured in `.env` file:

**Server Configuration:**
```bash
API_HOST=0.0.0.0              # Bind address
API_PORT=8000                 # Container port (mapped to 8003)
LOG_LEVEL=info                # debug, info, warning, error
ENVIRONMENT=production        # development or production
```

**Database Configuration:**
```bash
DATABASE_URL=postgresql://postgres:postgres@postgres:55432/maverick_mcp
# Auto-configured by docker-compose - don't change unless needed
```

**Cache Configuration:**
```bash
REDIS_HOST=redis              # Redis container hostname
REDIS_PORT=56379              # Redis port
CACHE_TTL_SECONDS=3600        # Default cache TTL (1 hour)
```

**Research Agent Configuration:**
```bash
RESEARCH_TIMEOUT_SECONDS=120  # Research timeout
PARALLEL_AGENTS_MAX=6         # Max parallel agents
CONFIDENCE_THRESHOLD=0.85     # Confidence threshold
```

### Port Customization

Ports are defined in `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8003:8000"  # Change 8003 to your preferred host port

  postgres:
    ports:
      - "55432:55432"  # Custom port to avoid conflicts

  redis:
    ports:
      - "56379:56379"  # Custom port to avoid conflicts
```

**Why Custom Ports?**
- **8003** instead of 8000: Avoids conflicts with other services
- **55432** instead of 5432: Avoids conflicts with system PostgreSQL
- **56379** instead of 6379: Avoids conflicts with system Redis

### Volume Mounts

**Development Volumes (Live Code)**
```yaml
volumes:
  - ./maverick_mcp:/app/maverick_mcp  # Live code reload
  - ./alembic:/app/alembic            # Database migrations
  - ./tests:/app/tests                # Tests
  - ./.env:/app/.env                  # Environment config
```

**Persistent Data Volumes**
```yaml
volumes:
  postgres-data:  # Database persists across container restarts
  redis-data:     # Cache persists across container restarts
```

## Multi-Stage Dockerfile

### Overview

The Dockerfile uses a **multi-stage build** to create optimized production images that are **50%+ smaller** than single-stage builds.

**Benefits:**
- **Smaller Images**: Only runtime dependencies in final image (~300MB vs ~600MB)
- **Faster Deployments**: Less data to transfer and pull
- **Better Security**: Fewer packages = smaller attack surface
- **Multi-Architecture**: Supports both AMD64 and ARM64 (Apple Silicon, AWS Graviton)

### Build Stages

#### Stage 1: Builder (Compilation)

```dockerfile
FROM python:3.12-slim AS builder

ARG TALIB_VERSION=0.6.4
ARG UV_VERSION=latest

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -yqq \
    build-essential \
    python3-dev \
    libpq-dev \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# Download and compile TA-Lib
ENV TALIB_DIR=/usr/local
RUN wget https://github.com/ta-lib/ta-lib/releases/download/v${TALIB_VERSION}/ta-lib-${TALIB_VERSION}-src.tar.gz \
    && tar -xzf ta-lib-${TALIB_VERSION}-src.tar.gz \
    && cd ta-lib-${TALIB_VERSION}/ \
    && ./configure --prefix=$TALIB_DIR \
    && make -j$(nproc) \
    && make install \
    && cd .. \
    && rm -rf ta-lib-${TALIB_VERSION}-src.tar.gz ta-lib-${TALIB_VERSION}/

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Install Python dependencies in virtual environment
RUN uv sync --frozen --no-dev
```

**Key Points:**
- Uses Python 3.12-slim as base (smaller than regular Python image)
- Installs build tools (gcc, make, etc.) for compiling TA-Lib
- Compiles TA-Lib with parallel jobs `make -j$(nproc)` for speed
- Installs Python dependencies with `uv sync --frozen --no-dev` (no dev dependencies in production)
- Cleans up build artifacts to save space

#### Stage 2: Runtime (Production)

```dockerfile
FROM python:3.12-slim AS runtime

LABEL maintainer="Maverick MCP <noreply@maverick-mcp.dev>"
LABEL description="Maverick MCP - Personal stock analysis MCP server"
LABEL version="0.1.0"

ARG APP_USER=maverick
ARG APP_UID=1000
ARG APP_GID=1000

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -yqq \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy TA-Lib from builder
COPY --from=builder /usr/local/lib/libta_lib.* /usr/local/lib/
COPY --from=builder /usr/local/include/ta-lib/ /usr/local/include/ta-lib/
RUN ldconfig

# Copy Python dependencies from builder
COPY --from=builder /build/.venv /app/.venv

# Install uv in runtime (needed for "uv run")
RUN pip install --no-cache-dir uv

# Copy application code
COPY maverick_mcp ./maverick_mcp
COPY alembic ./alembic
COPY alembic.ini setup.py pyproject.toml uv.lock README.md ./

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

# Create non-root user
RUN groupadd -g ${APP_GID} ${APP_USER} && \
    useradd -u ${APP_UID} -g ${APP_USER} -s /bin/sh -m ${APP_USER} && \
    chown -R ${APP_USER}:${APP_USER} /app

USER ${APP_USER}

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start MCP server (default to SSE, can be overridden by docker-compose.yml)
CMD ["uv", "run", "python", "-m", "maverick_mcp.api.server", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
```

!!! note "Transport Configuration"
    The Dockerfile defaults to `sse` transport for direct connections. However, `docker-compose.yml` overrides this with `streamable-http` for broader compatibility (ChatGPT, Claude Code CLI). See [MCP Transport Configuration](#mcp-transport-configuration) section above for details.

**Key Optimizations:**
1. **Layer Caching**: Dependencies installed before code copy for faster rebuilds
2. **Multi-Architecture Support**: Works on AMD64 (Intel/AMD) and ARM64 (Apple Silicon, AWS Graviton)
3. **Security**: Runs as non-root user (maverick:1000)
4. **Health Checks**: Built-in health endpoint monitoring
5. **Clean Image**: Only runtime dependencies (libpq5, curl), no build tools
6. **Environment Variables**: Configured for production Python execution

### Image Size Comparison

| Build Type | Image Size | Layers | Build Time |
|------------|-----------|--------|------------|
| **Single-stage** | ~600MB | 15+ | 3-4 min |
| **Multi-stage** | ~300MB | 8 | 3-4 min |
| **Savings** | **50%+** | **47% fewer** | **Same** |

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker-compose logs backend
```

**Common issues:**
- **Port conflict**: Change port in docker-compose.yml
- **Missing .env**: Copy from .env.example
- **Invalid API keys**: Check .env file

### Database Connection Errors

**Test database connectivity:**
```bash
# From host
docker-compose exec postgres psql -U postgres -c "SELECT 1;"

# Check backend can connect
docker-compose exec backend python -c "from maverick_mcp.data.session_management import get_session; print(get_session())"
```

**Common issues:**
- **Wrong DATABASE_URL**: Should use `postgres` as hostname (service name)
- **Database not ready**: Wait 10-15 seconds after `docker-compose up`

### Redis Connection Errors

**Test Redis connectivity:**
```bash
# From host
docker-compose exec redis redis-cli -p 56379 PING
# Should return: PONG

# Check backend can connect
docker-compose exec backend python -c "import redis; r = redis.Redis(host='redis', port=56379); print(r.ping())"
```

### Permission Errors

**Fix volume permissions:**
```bash
# Backend runs as maverick:1000
# If permission errors occur:
sudo chown -R 1000:1000 ./maverick_mcp
```

### Build Errors

**Clean build:**
```bash
# Remove all containers and volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

### TA-Lib Compilation Fails

**Manually debug:**
```bash
# Build with verbose output
docker-compose build --progress=plain backend

# Check TA-Lib installation
docker-compose run --rm backend python -c "import talib; print(talib.__version__)"
```

## Production Deployment

### Production Docker Compose

For production deployments, use `docker-compose.prod.yml` which includes:

- **Health checks** for all services
- **Resource limits** to prevent overconsumption
- **Optimized PostgreSQL** with 100 connections and tuned parameters
- **Redis persistence** with LRU eviction policy
- **Restart policies** for automatic recovery
- **Logging configuration** with rotation
- **Custom network** for service isolation

**Start production stack:**
```bash
# Using production compose file
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

**Key Production Features:**

#### 1. Backend Service with Health Checks
```yaml
backend:
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        cpus: '0.5'
        memory: 512M
```

#### 2. Optimized PostgreSQL
```yaml
postgres:
  image: postgres:15-alpine
  command:
    - "postgres"
    - "-c" "max_connections=100"
    - "-c" "shared_buffers=256MB"
    - "-c" "effective_cache_size=1GB"
    - "-c" "maintenance_work_mem=64MB"
    - "-c" "checkpoint_completion_target=0.9"
    - "-c" "wal_buffers=16MB"
    - "-c" "default_statistics_target=100"
    - "-c" "random_page_cost=1.1"
    - "-c" "effective_io_concurrency=200"
    - "-c" "work_mem=2621kB"
    - "-c" "min_wal_size=1GB"
    - "-c" "max_wal_size=4GB"
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 1G
```

#### 3. Redis with Persistence
```yaml
redis:
  command:
    - redis-server
    - --maxmemory 512mb
    - --maxmemory-policy allkeys-lru
    - --save 900 1
    - --save 300 10
    - --save 60 10000
    - --appendonly yes
    - --appendfsync everysec
  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
```

### Environment-Specific Configurations

The project includes three environment configuration templates:

#### Development (.env.development.example)

Optimized for local development with hot reload:

```bash
# Copy for development
cp .env.development.example .env

# Key settings
ENVIRONMENT=development
LOG_LEVEL=debug
HOT_RELOAD=true
DATABASE_URL=sqlite:///maverick_mcp_dev.db  # Simple SQLite
```

**Features:**
- SQLite database (no setup required)
- Hot reload enabled
- Debug logging
- Reduced connection limits for faster startup

#### Production (.env.production.example)

Optimized for production deployment:

```bash
# Copy for production (NEVER commit with real values!)
cp .env.production.example .env.production

# Key settings
ENVIRONMENT=production
LOG_LEVEL=info
DATABASE_URL=postgresql://maverick_user:secure_password@postgres:5432/maverick_mcp
REDIS_HOST=redis
REDIS_PORT=6379
```

**Features:**
- PostgreSQL required
- Redis required
- Security hardening
- Production checklists
- Monitoring configuration

**Production Checklist (from .env.production.example):**
- [ ] All default passwords changed
- [ ] SECRET_KEY is randomly generated (32+ characters)
- [ ] API keys are production-tier with appropriate limits
- [ ] TLS/SSL certificates are valid and up-to-date
- [ ] CORS origins restricted to actual domains
- [ ] Database and Redis access restricted by IP
- [ ] Sentry or monitoring configured
- [ ] Automated backups running daily

#### Testing (.env.testing.example)

Optimized for automated testing (CI/CD):

```bash
# Copy for testing
cp .env.testing.example .env.test

# Key settings
ENVIRONMENT=testing
DATABASE_URL=sqlite:///:memory:  # In-memory for speed
MOCK_EXTERNAL_APIS=true
VCR_RECORD_MODE=once
```

**Features:**
- In-memory SQLite (ephemeral, fast)
- Mocked external APIs
- VCR cassettes for recorded API responses
- Parallel testing support

### Security Checklist

- [ ] Use environment-specific `.env` files (`.env.production`)
- [ ] Never commit API keys to git
- [ ] Use secrets management (Docker secrets, AWS Secrets Manager)
- [ ] Change default PostgreSQL password
- [ ] Enable SSL/TLS for external connections
- [ ] Limit container resources (CPU, memory)
- [ ] Run containers as non-root users
- [ ] Scan images for vulnerabilities (Trivy, Snyk)
- [ ] Use multi-stage builds to reduce attack surface
- [ ] Enable health checks for all services
- [ ] Configure logging with rotation to prevent disk fill

## Development Tools Stack

Maverick MCP includes a comprehensive development tools stack via `docker-compose.tools.yml`:

- **pgAdmin** - PostgreSQL GUI (port 5050)
- **Redis Commander** - Redis GUI (port 8081)
- **Prometheus** - Metrics collection (port 9090)
- **Grafana** - Metrics visualization (port 3000)
- **Portainer** - Docker container management (port 9443)

### Starting Development Tools

**With development compose:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.tools.yml up -d
```

**With production compose:**
```bash
docker-compose -f docker-compose.prod.yml -f docker-compose.tools.yml up -d
```

### Tool Details

#### 1. pgAdmin - PostgreSQL Management

**Access:** http://localhost:5050

**Default Credentials:**
- Email: `admin@maverick-mcp.dev`
- Password: `admin`

**Pre-configured Server:**
- Name: Maverick MCP PostgreSQL
- Host: `postgres`
- Port: `5432`
- Database: `maverick_mcp`

**Features:**
- Query editor with syntax highlighting
- Visual schema designer
- Export/import data
- Performance monitoring
- Backup and restore tools

#### 2. Redis Commander - Redis Management

**Access:** http://localhost:8081

**Default Credentials:**
- Username: `admin`
- Password: `admin`

**Features:**
- Browse all Redis keys
- View key values and TTL
- Execute Redis commands
- Real-time statistics
- Key search and filtering

**Common Use Cases:**
```bash
# View all cache keys
# Navigate to http://localhost:8081 and browse keys

# Check cache hit rate
# View statistics in the web interface

# Clear specific cache
# Select keys and delete via GUI
```

#### 3. Prometheus - Metrics Collection

**Access:** http://localhost:9090

**Configuration:** Auto-configured to scrape:
- Backend metrics (port 9090)
- PostgreSQL exporter
- Redis exporter
- Prometheus self-monitoring

**Query Examples:**
```promql
# Request rate
rate(http_requests_total[5m])

# Response time (95th percentile)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Cache hit rate
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

**Data Retention:** 30 days (configurable)

#### 4. Grafana - Metrics Visualization

**Access:** http://localhost:3000

**Default Credentials:**
- Username: `admin`
- Password: `admin`

**Pre-configured Datasources:**
- Prometheus (http://prometheus:9090)
- PostgreSQL (postgres:5432)

**Pre-configured Dashboards:**
- **Maverick MCP Overview**: API requests, response times, error rates
- **Cache Performance**: Hit rates, memory usage
- **Database Monitoring**: Connections, query performance
- **System Resources**: CPU, memory, disk usage

**Custom Dashboard Creation:**
```bash
# Dashboards auto-loaded from
./tools/grafana/dashboards/

# Edit provisioning
./tools/grafana/provisioning/dashboards/dashboard.yml
./tools/grafana/provisioning/datasources/prometheus.yml
```

#### 5. Portainer - Container Management

**Access:** https://localhost:9443

**Features:**
- Visual container management
- View logs and stats in real-time
- Access container console
- Manage networks and volumes
- Stack management (compose files)
- Resource usage monitoring

**Quick Actions:**
```bash
# All available in web interface:
# - Start/stop/restart containers
# - View container logs
# - Execute commands in containers
# - Monitor resource usage
# - Manage volumes and networks
```

### Resource Usage

All tools are configured with resource limits:

| Tool | CPU Limit | Memory Limit | Storage |
|------|-----------|-------------|---------|
| pgAdmin | 0.5 cores | 512MB | Volume |
| Redis Commander | 0.25 cores | 256MB | None |
| Prometheus | 1.0 core | 1GB | 30-day data |
| Grafana | 1.0 core | 512MB | Volume |
| Portainer | 0.5 cores | 256MB | Volume |
| **Total** | **3.25 cores** | **2.5GB** | ~5GB |

### Disabling Tools

**Run without tools:**
```bash
docker-compose up -d  # Standard compose only
```

**Stop tools only:**
```bash
docker-compose -f docker-compose.tools.yml down
```

## CI/CD Pipeline

Maverick MCP includes a complete GitHub Actions CI/CD pipeline that:

- ✅ Runs tests before building images
- ✅ Builds multi-architecture images (AMD64 + ARM64)
- ✅ Pushes to GitHub Container Registry
- ✅ Performs security scanning with Trivy
- ✅ Runs smoke tests on built images
- ✅ Uploads coverage reports to Codecov

### Pipeline Overview

**Workflow File:** `.github/workflows/docker-build.yml`

**Triggered on:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Git tags (v*)
- Manual workflow dispatch

### Pipeline Stages

#### 1. Test Stage

Runs before any images are built:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
      redis:
        image: redis:7-alpine
    steps:
      - Run unit tests (pytest -m "not integration")
      - Run integration tests (pytest -m integration)
      - Upload coverage to Codecov
```

**What it does:**
- Sets up Python 3.12 with uv
- Installs dependencies
- Runs unit tests with in-memory SQLite
- Runs integration tests with PostgreSQL + Redis
- Generates and uploads coverage reports

#### 2. Build and Push Stage

Builds images for multiple architectures:

```yaml
jobs:
  build-and-push:
    needs: test
    strategy:
      matrix:
        platform:
          - linux/amd64   # Intel/AMD
          - linux/arm64   # Apple Silicon, AWS Graviton
    steps:
      - Set up QEMU for cross-platform builds
      - Set up Docker Buildx
      - Build and push multi-arch images
```

**Image Registry:** GitHub Container Registry (ghcr.io)

**Image Tags:**
- `main` → `ghcr.io/arunbcodes/maverick-mcp:latest`
- `develop` → `ghcr.io/arunbcodes/maverick-mcp:develop`
- `v1.2.3` → `ghcr.io/arunbcodes/maverick-mcp:1.2.3`
- PR #123 → `ghcr.io/arunbcodes/maverick-mcp:pr-123`

#### 3. Create Multi-Arch Manifest

Combines AMD64 and ARM64 images:

```yaml
jobs:
  create-manifest:
    needs: build-and-push
    steps:
      - Create manifest combining both architectures
      - Push manifest to registry
```

**Result:** Single image tag works on both Intel and ARM processors.

#### 4. Smoke Test Stage

Tests the built image:

```yaml
jobs:
  test-docker-image:
    needs: build-and-push
    steps:
      - Pull built image
      - Start container with test database
      - Check health endpoint
      - Verify logs
```

**Validates:**
- Image starts successfully
- Health endpoint responds
- Database connection works
- No critical errors in logs

#### 5. Security Scan Stage

Scans for vulnerabilities with Trivy:

```yaml
jobs:
  security-scan:
    needs: build-and-push
    steps:
      - Pull built image
      - Run Trivy vulnerability scanner
      - Upload results to GitHub Security tab
      - Generate human-readable report
```

**Checks for:**
- Known CVEs in packages
- Outdated dependencies
- Critical and high severity issues
- License compliance issues

**Results available:**
- GitHub Security tab (SARIF format)
- Workflow artifacts (text report)

### Using CI/CD Images

**Pull latest image:**
```bash
docker pull ghcr.io/arunbcodes/maverick-mcp:latest
```

**Run pulled image:**
```bash
docker run -d \
  -p 8003:8000 \
  -e TIINGO_API_KEY=your_key \
  -e DATABASE_URL=postgresql://... \
  ghcr.io/arunbcodes/maverick-mcp:latest
```

**Use in docker-compose:**
```yaml
services:
  backend:
    image: ghcr.io/arunbcodes/maverick-mcp:latest
    # ... rest of config
```

### Pipeline Metrics

| Stage | Duration | Success Rate |
|-------|----------|-------------|
| Tests | 3-5 min | >95% |
| Build (AMD64) | 3-4 min | >98% |
| Build (ARM64) | 3-4 min | >98% |
| Security Scan | 1-2 min | N/A |
| **Total** | **10-15 min** | **>95%** |

### Manual Workflow Dispatch

Trigger pipeline manually:

1. Go to GitHub Actions tab
2. Select "Docker Build and Push"
3. Click "Run workflow"
4. Select branch
5. Click "Run workflow"

### Local Testing (Before CI)

Test the workflow locally:

```bash
# Install act (GitHub Actions local runner)
brew install act

# Run workflow locally
act push

# Run specific job
act -j test
```

## Maintenance

### Update Images

```bash
# Pull latest base images
docker-compose pull

# Rebuild services
docker-compose build --pull

# Restart with new images
docker-compose up -d
```

### Backup Data

**PostgreSQL Backup:**
```bash
# Dump database
docker-compose exec postgres pg_dump -U postgres maverick_mcp > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T postgres psql -U postgres maverick_mcp < backup_20241111.sql
```

**Redis Backup:**
```bash
# Save RDB snapshot
docker-compose exec redis redis-cli -p 56379 SAVE

# Copy RDB file
docker cp maverick-mcp-redis-1:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

**Volume Backup:**
```bash
# Backup PostgreSQL volume
docker run --rm -v maverick-mcp_postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_$(date +%Y%m%d).tar.gz /data

# Backup Redis volume
docker run --rm -v maverick-mcp_redis-data:/data -v $(pwd):/backup alpine tar czf /backup/redis_$(date +%Y%m%d).tar.gz /data
```

### Clean Up

```bash
# Stop and remove containers (keeps volumes)
docker-compose down

# Remove containers and volumes (deletes data!)
docker-compose down -v

# Remove unused images
docker image prune -a

# Remove all unused resources
docker system prune -a --volumes
```

## Performance Tuning

### PostgreSQL Optimization

**Edit docker-compose.yml:**
```yaml
services:
  postgres:
    environment:
      - POSTGRES_SHARED_BUFFERS=256MB
      - POSTGRES_WORK_MEM=8MB
      - POSTGRES_MAINTENANCE_WORK_MEM=64MB
    command: >
      -c shared_buffers=256MB
      -c work_mem=8MB
      -c maintenance_work_mem=64MB
      -c effective_cache_size=1GB
```

### Redis Optimization

**Edit docker-compose.yml:**
```yaml
services:
  redis:
    command: >
      redis-server
      --port 56379
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
      --save 60 1000
```

## Quick Reference

### Docker Compose Files

| File | Purpose | Use Case | Command |
|------|---------|----------|---------|
| **docker-compose.yml** | Development | Local development with hot reload | `docker-compose up -d` |
| **docker-compose.prod.yml** | Production | Production deployment with optimizations | `docker-compose -f docker-compose.prod.yml up -d` |
| **docker-compose.tools.yml** | Dev Tools | Add pgAdmin, Grafana, Prometheus, etc. | `docker-compose -f docker-compose.yml -f docker-compose.tools.yml up -d` |

### Environment Files

| File | Purpose | Database | Cache | Hot Reload |
|------|---------|----------|-------|------------|
| **.env.development.example** | Development | SQLite | Optional | Yes |
| **.env.production.example** | Production | PostgreSQL | Redis | No |
| **.env.testing.example** | Testing/CI | In-memory SQLite | Mock | No |

### Service Ports

| Service | Development Port | Production Port | Tool URL |
|---------|-----------------|-----------------|----------|
| **Backend** | 8003 | 8003 | http://localhost:8003/sse/ |
| **PostgreSQL** | 55432 | 5432 | - |
| **Redis** | 56379 | 6379 | - |
| **pgAdmin** | 5050 | 5050 | http://localhost:5050 |
| **Redis Commander** | 8081 | 8081 | http://localhost:8081 |
| **Prometheus** | 9090 | 9090 | http://localhost:9090 |
| **Grafana** | 3000 | 3000 | http://localhost:3000 |
| **Portainer** | 9443 | 9443 | https://localhost:9443 |

### Common Commands

```bash
# Development
make docker-up              # Start development stack
make docker-logs            # View logs
make docker-down            # Stop all services

# Production
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f

# With Tools
docker-compose -f docker-compose.yml -f docker-compose.tools.yml up -d

# Maintenance
docker-compose exec backend uv run pytest        # Run tests
docker-compose exec postgres psql -U postgres    # Access database
docker-compose exec redis redis-cli              # Access Redis
docker-compose restart backend                    # Restart backend only

# Cleanup
docker-compose down -v       # Remove containers and volumes
docker system prune -a       # Clean up all unused resources
```

## Next Steps

- [ ] Review [Rancher Desktop Guide](rancher-desktop.md) for macOS users
- [ ] Set up production environment with `.env.production.example`
- [ ] Configure CI/CD pipeline with GitHub Actions
- [ ] Set up monitoring with Grafana dashboards
- [ ] Configure automated backups (PostgreSQL + Redis)
- [ ] Review security hardening checklist
- [ ] Enable Trivy security scanning in CI/CD
- [ ] Set up alerts for critical metrics
- [ ] Configure log aggregation (optional)
- [ ] Review multi-architecture build support

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [docker-compose Documentation](https://docs.docker.com/compose/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Trivy Security Scanner](https://github.com/aquasecurity/trivy)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Maverick MCP GitHub](https://github.com/arunbcodes/maverick-mcp)
