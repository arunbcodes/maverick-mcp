# Maverick-MCP Makefile
# Central command interface for agent-friendly development

.PHONY: help dev dev-sse dev-http dev-stdio stop test test-all test-watch test-specific test-parallel test-cov test-speed test-speed-quick test-speed-emergency test-speed-comparison test-strategies lint format typecheck clean tail-log backend check migrate setup redis-start redis-stop experiment experiment-once benchmark-parallel benchmark-speed docker-up docker-down docker-logs security-audit security-install setup-hooks api api-docker api-docker-down api-test api-test-cov generate-api-client docker-full docker-full-build docker-full-up docker-full-down docker-full-logs docker-backend docker-web docker-prod docker-clean

# Default target
help:
	@echo "Maverick-MCP Development Commands:"
	@echo ""
	@echo "  make dev          - Start development environment (SSE transport, default)"
	@echo "  make dev-sse      - Start with SSE transport (same as dev)"
	@echo "  make dev-http     - Start with Streamable-HTTP transport (for curl/testing)"
	@echo "  make dev-stdio    - Start with STDIO transport (for direct connections)"
	@echo "  make backend      - Start backend MCP server (dev mode)"
	@echo "  make stop         - Stop all services"
	@echo ""
	@echo "  make test         - Run unit tests (fast)"
	@echo "  make test-all     - Run all tests including integration"
	@echo "  make test-watch   - Auto-run tests on file changes"
	@echo "  make test-specific TEST=name - Run specific test"
	@echo "  make test-parallel - Run tests in parallel"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo "  make test-fixes   - Validate MCP tool fixes are working"
	@echo "  make test-speed   - Run speed optimization validation tests"
	@echo "  make test-speed-quick - Quick speed validation for CI"
	@echo "  make test-speed-emergency - Emergency mode speed tests"
	@echo "  make test-speed-comparison - Before/after performance comparison"
	@echo "  make test-strategies - Validate ALL backtesting strategies"
	@echo ""
	@echo "  make lint         - Run code quality checks"
	@echo "  make format       - Auto-format code"
	@echo "  make typecheck    - Run type checking"
	@echo "  make check        - Run all checks (lint + type check)"
	@echo ""
	@echo "  make security-audit    - Run security audit (safety, bandit)"
	@echo "  make security-install  - Install security tools (safety, bandit)"
	@echo "  make setup-hooks       - Install git pre-push hooks"
	@echo ""
	@echo "  make tail-log     - Follow backend logs"
	@echo ""
	@echo "  make experiment   - Watch and auto-run .py files"
	@echo "  make benchmark-parallel - Test parallel screening"
	@echo "  make benchmark-speed - Run comprehensive speed benchmark"
	@echo "  make migrate      - Run database migrations"
	@echo "  make setup        - Initial project setup"
	@echo "  make clean        - Clean up generated files"
	@echo ""
	@echo "  make docker-up    - Start MCP server with Docker (legacy)"
	@echo "  make docker-down  - Stop Docker services (legacy)"
	@echo "  make docker-logs  - View Docker logs (legacy)"
	@echo ""
	@echo "Full Stack Docker Commands:"
	@echo "  make docker-full       - Start all services (web + api + mcp + db)"
	@echo "  make docker-full-build - Build all Docker images"
	@echo "  make docker-full-up    - Start all containers (detached)"
	@echo "  make docker-full-down  - Stop all containers"
	@echo "  make docker-full-logs  - Follow logs from all services"
	@echo "  make docker-backend    - Start only backend (api + mcp + db)"
	@echo "  make docker-web        - Start web UI only (requires backend)"
	@echo "  make docker-prod       - Start in production mode"
	@echo "  make docker-clean      - Remove all containers and volumes"
	@echo ""
	@echo "  make api          - Start REST API server (dev mode)"
	@echo "  make api-docker   - Start REST API with Docker"
	@echo "  make api-test     - Run API tests"
	@echo "  make api-test-cov - Run API tests with coverage"

# Development commands
dev:
	@echo "Starting Maverick-MCP development environment (SSE transport)..."
	@./scripts/dev.sh

dev-sse:
	@echo "Starting Maverick-MCP development environment (SSE transport)..."
	@./scripts/dev.sh

dev-http:
	@echo "Starting Maverick-MCP development environment (Streamable-HTTP transport)..."
	@MAVERICK_TRANSPORT=streamable-http ./scripts/dev.sh

dev-stdio:
	@echo "Starting Maverick-MCP development environment (STDIO transport)..."
	@MAVERICK_TRANSPORT=stdio ./scripts/dev.sh

backend:
	@echo "Starting backend in development mode..."
	@uv run python -m maverick_server --transport sse --host 0.0.0.0 --port 8003

stop:
	@echo "Stopping all services..."
	@pkill -f "maverick_server" || true
	@echo "All services stopped."

# Testing commands
test:
	@echo "Running unit tests..."
	@uv run pytest -v

test-all:
	@echo "Running all tests (including integration)..."
	@uv run pytest -v -m ""

test-watch:
	@echo "Starting test watcher..."
	@if ! uv pip show pytest-watch > /dev/null 2>&1; then \
		echo "Installing pytest-watch..."; \
		uv pip install pytest-watch; \
	fi
	@uv run ptw -- -v

test-specific:
	@if [ -z "$(TEST)" ]; then \
		echo "Usage: make test-specific TEST=test_name"; \
		exit 1; \
	fi
	@echo "Running specific test: $(TEST)"
	@uv run pytest -v -k "$(TEST)"

test-parallel:
	@echo "Running tests in parallel..."
	@if ! uv pip show pytest-xdist > /dev/null 2>&1; then \
		echo "Installing pytest-xdist..."; \
		uv pip install pytest-xdist; \
	fi
	@uv run pytest -v -n auto

test-cov:
	@echo "Running tests with coverage..."
	@uv run pytest --cov=packages --cov-report=html --cov-report=term

# Speed optimization testing commands
test-speed:
	@echo "Running speed optimization validation tests..."
	@uv run pytest -v tests/test_speed_optimization_validation.py

test-speed-quick:
	@echo "Running quick speed validation for CI..."
	@uv run python scripts/speed_benchmark.py --mode quick

test-speed-emergency:
	@echo "Running emergency mode speed tests..."
	@uv run python scripts/speed_benchmark.py --mode emergency

test-speed-comparison:
	@echo "Running before/after performance comparison..."
	@uv run python scripts/speed_benchmark.py --mode comparison

test-strategies:
	@echo "Validating ALL backtesting strategies with real market data..."
	@uv run python scripts/test_all_strategies.py

# Code quality commands
lint:
	@echo "Running linter..."
	@uv run ruff check .

format:
	@echo "Formatting code..."
	@uv run ruff format .
	@uv run ruff check . --fix

typecheck:
	@echo "Running type checker..."
	@uv run pyright

check: lint typecheck
	@echo "All checks passed!"

# Utility commands
tail-log:
	@echo "Following backend logs (Ctrl+C to stop)..."
	@tail -f backend.log

experiment:
	@echo "Starting experiment harness..."
	@python tools/experiment.py

experiment-once:
	@echo "Running experiments once..."
	@python tools/experiment.py --once

migrate:
	@echo "Running database migrations..."
	@./scripts/run-migrations.sh upgrade

seed-demo:
	@echo "Seeding demo user and portfolio data..."
	@uv run python scripts/seed_demo_data.py

create-admin:
	@echo "Creating admin user..."
	@uv run python scripts/create_admin.py $(ARGS)

reset-db:
	@echo "⚠️  WARNING: This will reset the database!"
	@read -p "Are you sure? (y/N) " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "Resetting database..."
	@./scripts/run-migrations.sh downgrade base
	@./scripts/run-migrations.sh upgrade
	@echo "Database reset complete."

backup-db:
	@echo "Creating database backup..."
	@mkdir -p backups
	@pg_dump -U postgres -h localhost maverick > backups/maverick_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup saved to backups/"

setup:
	@echo "Setting up Maverick-MCP..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file - please update with your configuration"; \
	fi
	@uv sync
	@echo "Setup complete! Run 'make dev' to start development."

clean:
	@echo "Cleaning up..."
	@rm -rf .pytest_cache
	@rm -rf htmlcov
	@rm -rf .coverage
	@rm -rf .ruff_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete."

# Service management
redis-start:
	@echo "Starting Redis..."
	@if command -v brew &> /dev/null; then \
		brew services start redis; \
	else \
		redis-server --daemonize yes; \
	fi

redis-stop:
	@echo "Stopping Redis..."
	@if command -v brew &> /dev/null; then \
		brew services stop redis; \
	else \
		pkill redis-server || true; \
	fi

# Quick shortcuts
d: dev
dh: dev-http
ds: dev-stdio
b: backend
t: test
l: lint
c: check

# Performance testing
benchmark-parallel:
	@echo "Benchmarking parallel screening performance..."
	@python -c "from tools.quick_test import test_parallel_screening; import asyncio; asyncio.run(test_parallel_screening())"

benchmark-speed:
	@echo "Running comprehensive speed benchmark..."
	@uv run python scripts/speed_benchmark.py --mode full


# Docker commands
docker-up:
	@echo "Starting Docker services..."
	@docker-compose up --build -d

docker-down:
	@echo "Stopping Docker services..."
	@docker-compose down

docker-logs:
	@echo "Following Docker logs (Ctrl+C to stop)..."
	@docker-compose logs -f

# API commands (Phase 0+)
api:
	@echo "Starting REST API server..."
	@uv run uvicorn maverick_api:app --host 0.0.0.0 --port 8000 --reload

api-docker:
	@echo "Starting REST API with Docker..."
	@docker-compose -f docker-compose.api.yml up --build

api-docker-down:
	@echo "Stopping REST API Docker services..."
	@docker-compose -f docker-compose.api.yml down

api-test:
	@echo "Running API tests..."
	@uv run pytest packages/api/tests packages/services/tests packages/schemas/tests -v

api-test-cov:
	@echo "Running API tests with coverage..."
	@uv run pytest packages/api/tests packages/services/tests packages/schemas/tests --cov=packages/api/src --cov=packages/services/src --cov=packages/schemas/src --cov-report=html

generate-api-client:
	@echo "Generating TypeScript API client..."
	@./scripts/generate-api-client.sh

# Security commands
security-audit:
	@echo "Running security audit..."
	@./scripts/security_audit.sh

security-install:
	@echo "Installing security tools..."
	@uv pip install safety bandit
	@echo "Security tools installed successfully!"

setup-hooks:
	@echo "Setting up git hooks..."
	@./scripts/setup_git_hooks.sh

# =============================================================================
# Full Stack Docker Commands
# =============================================================================

# Build all Docker images
docker-full-build:
	@echo "Building all Docker images..."
	@docker compose -f docker/docker-compose.yml build

# Start all services (interactive, shows logs)
docker-full:
	@echo "Starting full stack (web + api + mcp + postgres + redis)..."
	@docker compose -f docker/docker-compose.yml up --build

# Start all services (detached)
docker-full-up:
	@echo "Starting full stack (detached)..."
	@docker compose -f docker/docker-compose.yml up -d --build

# Stop all services
docker-full-down:
	@echo "Stopping full stack..."
	@docker compose -f docker/docker-compose.yml down

# Follow logs from all services
docker-full-logs:
	@echo "Following logs (Ctrl+C to stop)..."
	@docker compose -f docker/docker-compose.yml logs -f

# Start only backend services (for local web development)
docker-backend:
	@echo "Starting backend services (api + mcp + postgres + redis)..."
	@docker compose -f docker/docker-compose.yml up -d postgres redis api mcp

# Start web UI only (requires backend running)
docker-web:
	@echo "Starting web UI..."
	@docker compose -f docker/docker-compose.yml up -d web

# Start in production mode
docker-prod:
	@echo "Starting in production mode..."
	@docker compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d

# Remove all containers and volumes
docker-clean:
	@echo "Removing all containers and volumes..."
	@docker compose -f docker/docker-compose.yml down -v --remove-orphans
	@echo "Clean complete."

# Shortcuts for full stack
df: docker-full
dfu: docker-full-up
dfd: docker-full-down
dfl: docker-full-logs
db: docker-backend
