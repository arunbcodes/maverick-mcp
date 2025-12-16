# Docker Setup

This directory contains the Docker configuration for running Maverick as a full-stack application.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Maverick Stack                            │
├─────────────┬─────────────┬─────────────┬──────────────┬────────┤
│  Web (3000) │  API (8000) │  MCP (8003) │ Postgres     │ Redis  │
│  Next.js    │  FastAPI    │  MCP Server │ (5432)       │ (6379) │
│             │             │ (Claude/    │              │        │
│             │             │  Cursor)    │              │        │
└──────┬──────┴──────┬──────┴──────┬──────┴──────────────┴────────┘
       │             │             │
       └─────────────┼─────────────┘
                     │
              Shared Database
```

## Files

| File | Description |
|------|-------------|
| `api.Dockerfile` | FastAPI REST API server |
| `mcp.Dockerfile` | MCP Server for Claude/Cursor |
| `web.Dockerfile` | Next.js web application |
| `base.Dockerfile` | Shared Python base (optional) |
| `docker-compose.yml` | Development configuration |
| `docker-compose.prod.yml` | Production overrides |
| `env.example` | Environment variables template |

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp docker/env.example docker/.env

# Edit with your API keys
nano docker/.env
```

### 2. Start All Services

```bash
# Build and start everything
make docker-full-up

# Or for interactive mode with logs
make docker-full
```

### 3. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| Web UI | http://localhost:3000 | Maverick Dashboard |
| REST API | http://localhost:8000 | API endpoints |
| API Docs | http://localhost:8000/docs | Swagger UI |
| MCP Server | http://localhost:8003 | For Claude/Cursor |

### 4. Login with Demo Account

For testing, a demo account is available:

| Field | Value |
|-------|-------|
| **Email** | `demo@maverick.example` |
| **Password** | `demo123456` |

Or register a new account at http://localhost:3000/register

## Common Commands

```bash
# Start full stack (detached)
make docker-full-up

# Stop everything
make docker-full-down

# View logs
make docker-full-logs

# Start only backend (for local web dev)
make docker-backend

# Production mode
make docker-prod

# Clean up (remove volumes)
make docker-clean
```

## Development Workflow

### Option A: Full Docker (Recommended for Testing)

```bash
# Start everything in Docker
make docker-full-up

# Make changes, rebuild specific service
docker compose -f docker/docker-compose.yml up -d --build api
```

### Option B: Local Web + Docker Backend

```bash
# Start backend in Docker
make docker-backend

# Run web locally (faster hot-reload)
cd apps/web
npm run dev
```

### Option C: Everything Local (Fastest)

```bash
# Start only database services
docker compose -f docker/docker-compose.yml up -d postgres redis

# Run API locally
make api

# Run MCP locally (different terminal)
make dev

# Run web locally (different terminal)
cd apps/web && npm run dev
```

## Production Deployment

### Build Images

```bash
# Build all images
make docker-full-build

# Tag for registry
docker tag maverick-api:dev your-registry/maverick-api:v1.0.0
docker tag maverick-mcp:dev your-registry/maverick-mcp:v1.0.0
docker tag maverick-web:dev your-registry/maverick-web:v1.0.0
```

### Deploy with Production Config

```bash
# Set production environment
export DB_PASSWORD=<secure-password>
export JWT_SECRET=<generated-secret>
export TIINGO_API_KEY=<your-key>

# Start in production mode
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               up -d
```

## Service Details

### Web (Next.js)

- **Port**: 3000
- **Dependencies**: api (must be healthy)
- **Build**: Multi-stage with standalone output
- **Health Check**: GET /

### API (FastAPI)

- **Port**: 8000
- **Dependencies**: postgres, redis
- **Health Check**: GET /health
- **Features**: REST endpoints, SSE for real-time, JWT auth

### MCP (MCP Server)

- **Port**: 8003
- **Dependencies**: postgres, redis
- **Transport**: SSE (Server-Sent Events)
- **Usage**: Configure in Claude Desktop or Cursor

### PostgreSQL

- **Port**: 5432
- **User**: postgres (configurable)
- **Database**: maverick_mcp
- **Data**: Persisted in `maverick-postgres-data` volume

### Redis

- **Port**: 6379
- **Usage**: Cache, sessions, rate limiting
- **Data**: Persisted in `maverick-redis-data` volume

## Troubleshooting

### Services won't start

```bash
# Check logs
docker compose -f docker/docker-compose.yml logs api
docker compose -f docker/docker-compose.yml logs mcp

# Ensure dependencies are healthy
docker compose -f docker/docker-compose.yml ps
```

### Database connection issues

```bash
# Verify postgres is running
docker compose -f docker/docker-compose.yml exec postgres pg_isready

# Check connection string
docker compose -f docker/docker-compose.yml exec api env | grep DATABASE
```

### Port conflicts

```bash
# Check what's using the port
lsof -i :8000
lsof -i :3000

# Change ports in docker-compose.yml or use environment variables
BACKEND_PORT=8001 make docker-full-up
```

### Clean restart

```bash
# Remove everything and start fresh
make docker-clean
make docker-full-up
```

## Resource Limits (Production)

| Service | CPU Limit | Memory Limit |
|---------|-----------|--------------|
| web | 1.0 | 512MB |
| api | 2.0 | 2GB |
| mcp | 2.0 | 2GB |
| postgres | 1.0 | 1GB |
| redis | 0.5 | 512MB |

## Build Optimization

### Docker BuildKit (Recommended)

Enable BuildKit for faster builds with better caching:

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build with cache
docker compose -f docker/docker-compose.yml build
```

### Parallel Builds

Build all images in parallel:

```bash
docker compose -f docker/docker-compose.yml build --parallel
```

### Build Cache Notes

Both `api.Dockerfile` and `mcp.Dockerfile` compile TA-Lib from source (~2-3 min).
Docker caches this layer, so subsequent builds are fast. To share cache between images:

```bash
# Build API first (caches TA-Lib layer)
docker build -f docker/api.Dockerfile -t maverick-api:latest .

# MCP build will be faster if same base layers cached
docker build -f docker/mcp.Dockerfile -t maverick-mcp:latest .
```

For CI/CD, consider pre-building and pushing a base image:

```bash
# Build and push base image (optional)
docker build -f docker/base.Dockerfile -t your-registry/maverick-base:latest .
docker push your-registry/maverick-base:latest
```

## Security

### Environment Variables

**Never commit API keys!** The repository includes:

- `.gitignore` - Ignores `docker/.env` and other secret files
- `.pre-commit-config.yaml` - Gitleaks hook to catch secrets before commit
- `docker/env.example` - Template with empty values (safe to commit)

### Setup Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install gitleaks (secret scanner)
brew install gitleaks  # macOS
# or: apt install gitleaks  # Linux

# Activate hooks
pre-commit install

# Test (scans all files)
pre-commit run --all-files
```

### API Keys for AI Features

For AI-powered features (natural language search, explanations), set:

```bash
# In docker/.env
OPENROUTER_API_KEY=your-key-here  # Required for AI features
```

Without this key, the app falls back to rule-based parsing (still functional but less accurate).
