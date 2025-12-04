# Docker Deployment Guide

Complete guide for running Maverick as a full-stack application with Docker containers.

## Overview

Maverick provides a production-ready Docker setup with:

- **5-Service Architecture**: Web UI, REST API, MCP Server, PostgreSQL, Redis
- **Multi-stage Dockerfiles**: Optimized builder and runtime stages (50%+ smaller images)
- **Development and Production configs**: Separate docker-compose files
- **Health checks**: For all services with proper startup ordering
- **Resource limits**: Prevent container overconsumption
- **Hot reload**: Volume mounts for development

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Maverick Stack                            │
├─────────────┬─────────────┬─────────────┬──────────────┬────────┤
│  Web (3000) │  API (8000) │  MCP (8003) │ PostgreSQL   │ Redis  │
│  Next.js    │  FastAPI    │  MCP Server │ (5432)       │ (6379) │
│  Dashboard  │  REST API   │ Claude/     │              │        │
│             │             │ Cursor      │              │        │
└──────┬──────┴──────┬──────┴──────┬──────┴──────────────┴────────┘
       │             │             │
       └─────────────┼─────────────┘
                     │
              Shared Database & Cache
```

### Service Details

| Service | Image | Port | Purpose | Dependencies |
|---------|-------|------|---------|--------------|
| **web** | Next.js 14 | 3000 | Dashboard UI | api |
| **api** | FastAPI | 8000 | REST endpoints | postgres, redis |
| **mcp** | MCP Server | 8003 | Claude/Cursor integration | postgres, redis |
| **postgres** | PostgreSQL 15 | 5432 | Primary database | - |
| **redis** | Redis 7 | 6379 | Cache, sessions, rate limiting | - |

## Prerequisites

### Required Software

**Option 1: Docker Desktop**

- macOS: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
- Windows: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
- Linux: [Install Docker Engine](https://docs.docker.com/engine/install/)

**Option 2: Rancher Desktop (Recommended for macOS)**

- [Download Rancher Desktop](https://rancherdesktop.io/)
- Free and open source
- See [Rancher Desktop Guide](rancher-desktop.md) for setup

### Verify Installation

```bash
# Check Docker is installed
docker --version
# Output: Docker version 24.0.x, build ...

# Check docker compose is installed
docker compose version
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
# Copy environment template
cp docker/env.example docker/.env

# Edit with your API keys
nano docker/.env
```

**Required Configuration (`docker/.env`):**

```bash
# Required - Stock data provider
TIINGO_API_KEY=your-tiingo-api-key-here

# Optional - Enhanced features
OPENAI_API_KEY=your-openai-key      # AI analysis
ANTHROPIC_API_KEY=your-anthropic-key # Claude integration
OPENROUTER_API_KEY=your-openrouter-key # Multi-model access

# Production (change these!)
JWT_SECRET=change-me-in-production
DB_PASSWORD=postgres
```

### 3. Start Services

**Method 1: Using Makefile (Recommended)**

```bash
# Start all services (detached)
make docker-full-up

# View logs
make docker-full-logs

# Stop all services
make docker-full-down
```

**Method 2: Direct docker compose**

```bash
# Start all services
docker compose -f docker/docker-compose.yml up -d

# View logs
docker compose -f docker/docker-compose.yml logs -f

# Stop services
docker compose -f docker/docker-compose.yml down
```

### 4. Verify Services

```bash
# Check all containers are running
docker ps

# Expected output:
# CONTAINER ID   IMAGE              STATUS         PORTS
# xxxx          maverick-web       Up (healthy)   0.0.0.0:3000->3000/tcp
# yyyy          maverick-api       Up (healthy)   0.0.0.0:8000->8000/tcp
# zzzz          maverick-mcp       Up (healthy)   0.0.0.0:8003->8000/tcp
# aaaa          postgres:15-alpine Up (healthy)   0.0.0.0:5432->5432/tcp
# bbbb          redis:7-alpine     Up (healthy)   0.0.0.0:6379->6379/tcp
```

### 5. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| **Web Dashboard** | http://localhost:3000 | Main user interface |
| **REST API** | http://localhost:8000 | API endpoints |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **MCP Server** | http://localhost:8003 | For Claude/Cursor |

### 6. Connect Claude Desktop

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

!!! warning "Trailing Slash Required"
    The `/sse/` endpoint **must** include the trailing slash!

## Docker Files

### File Structure

```
docker/
├── api.Dockerfile          # FastAPI REST API
├── mcp.Dockerfile          # MCP Server
├── web.Dockerfile          # Next.js Web UI
├── base.Dockerfile         # Shared Python base (optional)
├── docker-compose.yml      # Development config
├── docker-compose.prod.yml # Production overrides
├── env.example             # Environment template
└── README.md               # Docker-specific docs
```

### Dockerfiles

#### api.Dockerfile

Multi-stage build for FastAPI REST API:

- **Builder stage**: Compiles TA-Lib, installs Python dependencies
- **Runtime stage**: Minimal image with only runtime dependencies
- **Security**: Runs as non-root user (maverick:1000)
- **Health check**: `curl -f http://localhost:8000/health`

#### mcp.Dockerfile

Multi-stage build for MCP Server:

- Same builder stage as API (shared dependencies)
- Includes legacy `maverick_mcp` module
- SSE transport for AI assistant communication
- Health check validates MCP response format

#### web.Dockerfile

Multi-stage Next.js build:

- **deps stage**: Install npm dependencies
- **builder stage**: Build Next.js with `output: 'standalone'`
- **runner stage**: Minimal runtime with built files only
- Uses Node.js 20 Alpine base

## Development Workflow

### Option A: Full Docker (Recommended for Testing)

Run everything in Docker:

```bash
# Start all services
make docker-full-up

# Make changes, rebuild specific service
docker compose -f docker/docker-compose.yml up -d --build api
```

### Option B: Docker Backend + Local Web (Faster)

Backend in Docker, web with hot-reload locally:

```bash
# Start backend services
make docker-backend

# Run web locally (faster hot-reload)
cd apps/web
npm run dev
```

### Option C: Only Database in Docker (Fastest)

Minimal Docker, everything else local:

```bash
# Start only Postgres and Redis
docker compose -f docker/docker-compose.yml up -d postgres redis

# Run API locally
make api

# Run MCP locally (different terminal)
make dev

# Run web locally (different terminal)
cd apps/web && npm run dev
```

### Development Tasks

**View Logs**

```bash
# All services
make docker-full-logs

# Specific service
docker compose -f docker/docker-compose.yml logs -f api
docker compose -f docker/docker-compose.yml logs -f mcp
docker compose -f docker/docker-compose.yml logs -f web
```

**Execute Commands in Container**

```bash
# Access API shell
docker compose -f docker/docker-compose.yml exec api /bin/sh

# Run database migrations
docker compose -f docker/docker-compose.yml exec api alembic upgrade head

# Run tests
docker compose -f docker/docker-compose.yml exec api pytest
```

**Database Access**

```bash
# Connect to PostgreSQL
docker compose -f docker/docker-compose.yml exec postgres psql -U postgres -d maverick_mcp

# Run SQL query
docker compose -f docker/docker-compose.yml exec postgres psql -U postgres -d maverick_mcp -c "SELECT * FROM users LIMIT 5;"
```

**Redis Access**

```bash
# Connect to Redis CLI
docker compose -f docker/docker-compose.yml exec redis redis-cli

# Check cache keys
docker compose -f docker/docker-compose.yml exec redis redis-cli KEYS "*"
```

## Production Deployment

### Production Compose

Use production overrides for optimized settings:

```bash
# Start in production mode
make docker-prod

# Or manually:
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               up -d
```

### Production Features

The `docker-compose.prod.yml` adds:

- **No volume mounts**: Uses built images only
- **Resource limits**: CPU and memory constraints
- **Multi-worker API**: `uvicorn --workers 4`
- **Optimized PostgreSQL**: Tuned connection and memory settings
- **Redis persistence**: AOF with LRU eviction
- **Required environment variables**: Fails fast on missing config

### Environment Variables

Production requires these variables:

```bash
# Required (will fail without these)
DB_PASSWORD=<secure-password>
JWT_SECRET=<generated-secret>
TIINGO_API_KEY=<your-key>

# Recommended
CORS_ORIGINS=https://yourdomain.com
PUBLIC_API_URL=https://api.yourdomain.com
```

### Resource Limits

| Service | CPU Limit | Memory Limit |
|---------|-----------|--------------|
| web | 1.0 | 512MB |
| api | 2.0 | 2GB |
| mcp | 2.0 | 2GB |
| postgres | 1.0 | 1GB |
| redis | 0.5 | 512MB |

## Build Optimization

### Enable BuildKit

BuildKit provides faster builds with better caching:

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build with cache
docker compose -f docker/docker-compose.yml build
```

### Parallel Builds

```bash
docker compose -f docker/docker-compose.yml build --parallel
```

### Image Sizes

| Image | Size | Description |
|-------|------|-------------|
| maverick-web | ~150MB | Next.js standalone |
| maverick-api | ~300MB | FastAPI + TA-Lib |
| maverick-mcp | ~350MB | MCP + all packages |

## Makefile Commands

```bash
# Full Stack
make docker-full          # Start all (interactive)
make docker-full-up       # Start all (detached)
make docker-full-down     # Stop all
make docker-full-logs     # Follow logs

# Partial Stack
make docker-backend       # Start API + MCP + DB
make docker-web           # Start web only

# Production
make docker-prod          # Start with prod overrides

# Maintenance
make docker-clean         # Remove containers and volumes
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose -f docker/docker-compose.yml logs api

# Common issues:
# - Missing environment variables
# - Port already in use
# - Database not ready
```

### Port Conflicts

```bash
# Check what's using the port
lsof -i :8000
lsof -i :3000

# Stop conflicting process or change ports
```

### Database Connection Errors

```bash
# Verify postgres is healthy
docker compose -f docker/docker-compose.yml ps

# Test connection
docker compose -f docker/docker-compose.yml exec postgres pg_isready
```

### Build Errors

```bash
# Clean rebuild
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml build --no-cache
docker compose -f docker/docker-compose.yml up -d
```

### TA-Lib Compilation Fails

```bash
# Build with verbose output
docker compose -f docker/docker-compose.yml build --progress=plain api

# Check TA-Lib in container
docker compose -f docker/docker-compose.yml run --rm api python -c "import talib; print(talib.__version__)"
```

## Next Steps

- [ ] Set up [Production Environment](production.md)
- [ ] Configure [Monitoring with Grafana](../development/monitoring.md)
- [ ] Review [Security Checklist](#security-checklist)
- [ ] Set up [CI/CD Pipeline](#cicd-pipeline)

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [docker compose Documentation](https://docs.docker.com/compose/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Rancher Desktop Guide](rancher-desktop.md)
