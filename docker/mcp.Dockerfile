# MCP Server for Claude/Cursor Integration
# Provides MCP protocol over SSE transport
#
# Build: docker build -f docker/mcp.Dockerfile -t maverick-mcp:latest .
# Run:   docker run -p 8003:8000 maverick-mcp:latest
#        (maps host 8003 to container 8000)
#
# Uses base.Dockerfile for shared Python dependencies and TA-Lib

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

# Copy source code
COPY packages/ ./packages/
COPY maverick_mcp/ ./maverick_mcp/
COPY alembic/ ./alembic/
COPY scripts/ ./scripts/
COPY alembic.ini pyproject.toml uv.lock README.md ./

# Make entrypoint executable (if it exists)
RUN if [ -f /app/scripts/docker-entrypoint.sh ]; then chmod +x /app/scripts/docker-entrypoint.sh; fi

# Environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/packages/schemas/src:/app/packages/core/src:/app/packages/data/src:/app/packages/services/src:/app/packages/capabilities/src:/app/packages/api/src:/app/packages/server/src:/app/packages/backtest/src:/app/packages/india/src:/app/packages/agents/src:/app/packages/crypto/src:/app"

# Create non-root user
RUN groupadd -g ${APP_GID} ${APP_USER} \
    && useradd -u ${APP_UID} -g ${APP_USER} -s /bin/sh -m ${APP_USER} \
    && chown -R ${APP_USER}:${APP_USER} /app

USER ${APP_USER}

# Container listens on port 8000 internally
# Map to any host port (e.g., 8003:8000 for MCP)
EXPOSE 8000

# Health check - verify server is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://localhost:8000/health || exit 1

# Start MCP server with SSE transport
CMD ["/app/.venv/bin/python", "-m", "maverick_server", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
