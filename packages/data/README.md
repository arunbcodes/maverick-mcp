# Maverick Data

Data access, caching, and persistence for Maverick stock analysis.

## Overview

This package provides:

- **Database Models**: SQLAlchemy models for financial data storage
- **Session Management**: Sync and async database session factories
- **Cache Providers**: Redis and in-memory caching implementations
- **Data Providers**: Stock data fetching from various sources
- **Repositories**: Repository pattern implementations for data access

## Installation

```bash
pip install maverick-data
```

Or with uv:

```bash
uv add maverick-data
```

## Usage

### Session Management

```python
from maverick_data import get_session, get_async_db, init_db

# Initialize database schema
init_db()

# Sync session
session = get_session()
try:
    # Use session
    pass
finally:
    session.close()

# Async session (for FastAPI)
async for session in get_async_db():
    # Use session
    pass
```

### Models

```python
from maverick_data.models import Base, TimestampMixin
```

## Dependencies

- maverick-core: Core interfaces and domain entities
- SQLAlchemy: ORM and database toolkit
- Redis: Optional caching backend
- yfinance: Yahoo Finance data provider
- pandas: Data manipulation

## Configuration

Configure via environment variables:

- `DATABASE_URL`: Database connection string (default: SQLite)
- `DB_POOL_SIZE`: Connection pool size (default: 5)
- `DB_MAX_OVERFLOW`: Max overflow connections (default: 10)
- `DB_POOL_TIMEOUT`: Pool timeout in seconds (default: 30)
- `DB_ECHO`: Enable SQL logging (default: false)
