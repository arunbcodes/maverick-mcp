# FastAPI REST API Server
# Provides REST endpoints for Web and Mobile clients
#
# Build: docker build -f docker/api.Dockerfile -t maverick-api:latest .
# Run:   docker run -p 8000:8000 maverick-api:latest

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
LABEL description="Maverick REST API Server"

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
COPY alembic/ ./alembic/
COPY alembic.ini ./

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

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start API server
CMD ["uvicorn", "maverick_api:app", "--host", "0.0.0.0", "--port", "8000"]
