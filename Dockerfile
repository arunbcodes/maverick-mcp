# Dockerfile for Maverick-MCP
# Multi-stage build for optimized production images
# Supports AMD64 and ARM64 architectures

# ============================================================================
# Stage 1: Builder - Compile dependencies and TA-Lib
# ============================================================================
FROM python:3.12-slim AS builder

# Build arguments for flexibility
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
# Copy all files from /usr/local to ensure we get TA-Lib libraries and headers
COPY --from=builder /usr/local/ /usr/local/
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

# Health check - verify server is listening on port 8000
# Note: /health endpoint may not be accessible depending on transport mode
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ 2>&1 | grep -q "Not Found\|jsonrpc\|Method Not Allowed" || exit 1

# Start MCP server (can be overridden)
CMD ["uv", "run", "python", "-m", "maverick_mcp.api.server", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
