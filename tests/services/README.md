# Service Tests

This directory contains unit tests for the refactored service layer.

## Test Files

- `test_market_calendar_service.py` - Tests for MarketCalendarService (trading days, holidays, multi-market support)
- `test_stock_cache_manager.py` - Tests for StockCacheManager (coming soon)
- `test_stock_data_fetcher.py` - Tests for StockDataFetcher (coming soon)
- `test_screening_service.py` - Tests for ScreeningService (coming soon)

## Running Tests

### Option 1: Using Make (Recommended)

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific service tests
pytest tests/services/test_market_calendar_service.py -v
```

### Option 2: Using Docker

```bash
# Run tests in Docker environment
docker-compose exec backend pytest tests/services/ -v
```

### Option 3: Direct pytest

```bash
# Activate virtual environment first
source .venv/bin/activate  # or: uv sync

# Run tests
pytest tests/services/ -v

# Run with coverage
pytest tests/services/ --cov=maverick_mcp.services --cov-report=html
```

## Test Requirements

Tests require the following dependencies (included in `pyproject.toml`):
- `pytest>=8.4.0`
- `pytest-asyncio>=1.1.0`
- `pytest-cov>=6.2.1`
- `pandas-market-calendars>=5.1.0`

Install with:
```bash
uv sync  # or: pip install -e ".[dev]"
```

## Test Structure

Each service test file follows this structure:

1. **Initialization Tests** - Test service creation and setup
2. **Core Functionality Tests** - Test main service methods
3. **Edge Cases Tests** - Test error handling and boundaries
4. **Performance Tests** - Test caching and efficiency
5. **Integration Tests** - Test interaction with dependencies

## Coverage Goals

Target: 70%+ coverage for each service

Current status will be shown when running `make test-cov`.

