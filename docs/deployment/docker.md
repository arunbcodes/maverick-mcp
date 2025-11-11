# Docker Deployment Guide

Complete guide for running Maverick MCP in Docker containers.

## Overview

Maverick MCP provides a production-ready Docker setup with:

- **Multi-container architecture** (Backend, PostgreSQL, Redis)
- **Optimized Dockerfile** with layer caching and security best practices
- **docker-compose** orchestration for easy management
- **Development and production** configurations
- **Persistent volumes** for data retention
- **Non-root user** for security
- **Custom ports** to avoid conflicts

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
    # Enable hot reload
    command: uv run python -m maverick_mcp.api.server --transport sse --host 0.0.0.0 --port 8000 --reload

    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=debug
      - API_DEBUG=true

    # Interactive debugging
    stdin_open: true
    tty: true
```

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

## Dockerfile Breakdown

### Multi-Stage Build Process

```dockerfile
# Stage 1: Base Python image
FROM python:3.12-slim

# Stage 2: System dependencies
RUN apt-get update && apt-get install -yqq \
  build-essential \
  python3-dev \
  libpq-dev \
  wget \
  curl

# Stage 3: Install uv package manager
RUN pip install --no-cache-dir uv

# Stage 4: Compile TA-Lib from source
ENV TALIB_DIR=/usr/local
RUN wget https://github.com/ta-lib/ta-lib/releases/download/v0.6.4/ta-lib-0.6.4-src.tar.gz \
  && tar -xzf ta-lib-0.6.4-src.tar.gz \
  && cd ta-lib-0.6.4/ \
  && ./configure --prefix=$TALIB_DIR \
  && make -j$(nproc) \
  && make install

# Stage 5: Copy dependencies (layer caching)
COPY pyproject.toml uv.lock README.md ./

# Stage 6: Install Python dependencies
RUN uv sync --frozen

# Stage 7: Copy application code
COPY maverick_mcp ./maverick_mcp
COPY alembic ./alembic
COPY alembic.ini setup.py ./

# Stage 8: Security - non-root user
RUN groupadd -g 1000 maverick && \
    useradd -u 1000 -g maverick -s /bin/sh -m maverick && \
    chown -R maverick:maverick /app

USER maverick

# Stage 9: Start server
CMD ["uv", "run", "python", "-m", "maverick_mcp.api.server", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
```

**Key Optimizations:**
1. **Layer Caching**: Dependencies installed before code copy
2. **No Cache Flag**: Reduces image size
3. **Multi-core Build**: `make -j$(nproc)` for parallel compilation
4. **Clean Up**: Removes build artifacts after compilation
5. **Frozen Lock**: `uv sync --frozen` ensures reproducible builds

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

### Security Checklist

- [ ] Use environment-specific `.env` files (`.env.production`)
- [ ] Never commit API keys to git
- [ ] Use secrets management (Docker secrets, AWS Secrets Manager)
- [ ] Change default PostgreSQL password
- [ ] Enable SSL/TLS for external connections
- [ ] Limit container resources (CPU, memory)
- [ ] Use read-only root filesystem where possible
- [ ] Scan images for vulnerabilities

### Resource Limits

**Add to docker-compose.yml:**
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Restart Policy

**Add to docker-compose.yml:**
```yaml
services:
  backend:
    restart: unless-stopped  # Auto-restart on failure

  postgres:
    restart: unless-stopped

  redis:
    restart: unless-stopped
```

### Health Checks

**Backend health check (when implemented):**
```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Logging

**Configure logging driver:**
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
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

## Next Steps

- [ ] Review [Rancher Desktop Guide](rancher-desktop.md) for macOS users
- [ ] Explore production deployment options
- [ ] Set up monitoring and alerting
- [ ] Configure automated backups
- [ ] Review security hardening checklist

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [docker-compose Documentation](https://docs.docker.com/compose/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Maverick MCP GitHub](https://github.com/arunbcodes/maverick-mcp)
