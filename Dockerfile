# Dockerfile for Maverick-MCP
# Multi-stage build for optimized production images
# Supports AMD64 and ARM64 architectures
#
# Architecture:
#   packages/
#     maverick-core     - Pure domain logic, interfaces
#     maverick-data     - Data providers, caching, persistence
#     maverick-backtest - Backtesting engine and strategies
#     maverick-agents   - AI/LLM agents and workflows
#     maverick-india    - Indian market specific features
#     maverick-server   - MCP server (main entry point)

# ============================================================================
# Stage 1: Builder - Compile dependencies and TA-Lib
# ============================================================================
FROM python:3.12-slim AS builder

# Build arguments for flexibility
ARG TALIB_VERSION=0.6.4

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -yqq \
    build-essential \
    python3-dev \
    libpq-dev \
    wget \
    curl \
    git \
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

# Copy root dependency files first (for layer caching)
COPY pyproject.toml uv.lock README.md ./

# Copy all packages (needed for workspace install)
COPY packages/ ./packages/

# Install all packages in the workspace
# This installs maverick-core, maverick-data, maverick-backtest, 
# maverick-agents, maverick-india, maverick-server with all dependencies
RUN uv sync --frozen --no-dev

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:3.12-slim AS runtime

# Metadata labels
LABEL maintainer="Maverick MCP <noreply@maverick-mcp.dev>"
LABEL description="Maverick MCP - Personal stock analysis MCP server"
LABEL version="0.1.0"

# Build arguments
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

# Copy TA-Lib from builder (both libraries and headers)
COPY --from=builder /usr/local/ /usr/local/
RUN ldconfig

# Copy Python virtual environment from builder
COPY --from=builder /build/.venv /app/.venv

# Install uv in runtime (needed for "uv run")
RUN pip install --no-cache-dir uv

# Copy packages source code (needed for editable installs to work)
COPY packages/ ./packages/

# Copy application configuration and scripts
COPY alembic ./alembic
COPY scripts ./scripts
COPY alembic.ini pyproject.toml uv.lock README.md ./

# Copy legacy maverick_mcp if it exists (for backwards compatibility)
# This can be removed once migration is complete
COPY maverick_mcp ./maverick_mcp

# Make entrypoint executable
RUN chmod +x /app/scripts/docker-entrypoint.sh

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

# Health check - verify server is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -s http://localhost:8000/ 2>&1 | grep -q "Not Found\|jsonrpc\|Method Not Allowed" || exit 1

# Set entrypoint to handle auto-seeding
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]

# Default command: Start MCP server
# Can be overridden for different services (e.g., worker, scheduler)
CMD ["uv", "run", "python", "-m", "maverick_mcp.api.server", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
