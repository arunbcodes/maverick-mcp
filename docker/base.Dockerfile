# Shared Python base image for API and MCP services
# This provides consistent dependencies across services
#
# Build: docker build -f docker/base.Dockerfile -t maverick-base:latest .

FROM python:3.12-slim AS base

# Build arguments
ARG TALIB_VERSION=0.6.4

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpq-dev \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

WORKDIR /build

# Download and compile TA-Lib (optional, for technical analysis)
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

# Copy dependency files for layer caching
COPY pyproject.toml uv.lock README.md ./

# Copy all packages (needed for workspace install)
COPY packages/ ./packages/

# Install all dependencies
RUN uv sync --frozen --no-dev

# --- Runtime base ---
FROM python:3.12-slim AS runtime-base

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy TA-Lib libraries
COPY --from=base /usr/local/lib/libta_lib* /usr/local/lib/
RUN ldconfig

# Copy virtual environment
COPY --from=base /build/.venv /app/.venv

# Install uv for runtime
RUN pip install --no-cache-dir uv

# Set environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/packages/schemas/src:/app/packages/core/src:/app/packages/data/src:/app/packages/services/src:/app/packages/api/src:/app/packages/server/src:/app/packages/backtest/src:/app/packages/india/src:/app/packages/agents/src:/app/packages/crypto/src:/app"

WORKDIR /app

