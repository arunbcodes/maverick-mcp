# MCP Server for Claude/Cursor Integration
# Provides MCP protocol over SSE transport
#
# Build: docker build -f docker/mcp.Dockerfile -t maverick-mcp:latest .
# Run:   docker run -p 8003:8000 maverick-mcp:latest

# --- Build stage ---
FROM python:3.12-slim AS builder

ARG TALIB_VERSION=0.6.4

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpq-dev \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /build

# Build TA-Lib
ENV TALIB_DIR=/usr/local
RUN wget -q https://github.com/ta-lib/ta-lib/releases/download/v${TALIB_VERSION}/ta-lib-${TALIB_VERSION}-src.tar.gz \
    && tar -xzf ta-lib-${TALIB_VERSION}-src.tar.gz \
    && cd ta-lib-${TALIB_VERSION}/ \
    && ./configure --prefix=$TALIB_DIR --quiet \
    && make -j$(nproc) > /dev/null \
    && make install > /dev/null \
    && cd .. \
    && rm -rf ta-lib-${TALIB_VERSION}-src.tar.gz ta-lib-${TALIB_VERSION}/ \
    && ldconfig

# Copy and install dependencies
COPY pyproject.toml uv.lock README.md ./
COPY packages/ ./packages/
RUN uv sync --frozen --no-dev

# --- Runtime stage ---
FROM python:3.12-slim AS runtime

LABEL maintainer="Maverick MCP"
LABEL description="Maverick MCP Server for AI Assistants"

ARG APP_USER=maverick
ARG APP_UID=1000
ARG APP_GID=1000

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy TA-Lib
COPY --from=builder /usr/local/lib/libta_lib* /usr/local/lib/
RUN ldconfig

WORKDIR /app

# Copy virtual environment
COPY --from=builder /build/.venv /app/.venv

# Install uv for runtime (needed for "uv run")
RUN pip install --no-cache-dir uv

# Copy source code
COPY packages/ ./packages/
COPY maverick_mcp/ ./maverick_mcp/
COPY alembic/ ./alembic/
COPY scripts/ ./scripts/
COPY alembic.ini pyproject.toml uv.lock README.md ./

# Make entrypoint executable
RUN chmod +x /app/scripts/docker-entrypoint.sh 2>/dev/null || true

# Environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/packages/schemas/src:/app/packages/core/src:/app/packages/data/src:/app/packages/services/src:/app/packages/api/src:/app/packages/server/src:/app/packages/backtest/src:/app/packages/india/src:/app/packages/agents/src:/app/packages/crypto/src:/app"

# Create non-root user
RUN groupadd -g ${APP_GID} ${APP_USER} \
    && useradd -u ${APP_UID} -g ${APP_USER} -s /bin/sh -m ${APP_USER} \
    && chown -R ${APP_USER}:${APP_USER} /app

USER ${APP_USER}

EXPOSE 8000

# Health check - MCP server responds differently
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -s http://localhost:8000/ 2>&1 | grep -q "Not Found\|jsonrpc\|Method Not Allowed" || exit 1

# Start MCP server with SSE transport
CMD ["uv", "run", "python", "-m", "maverick_mcp.api.server", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]

