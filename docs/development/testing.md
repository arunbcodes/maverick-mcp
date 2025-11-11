# Testing Guide

Comprehensive guide to testing Maverick MCP.

## Philosophy

Maverick MCP follows a rigorous testing approach:

- **Test-Driven Development (TDD)**: Write tests before implementation
- **High Coverage Target**: 80%+ overall, 90%+ for critical paths
- **Fast Feedback**: Unit tests complete in 5-10 seconds
- **Layered Testing**: Unit → Integration → End-to-End → Performance
- **Financial Accuracy**: Extra scrutiny for financial calculations
- **Regression Protection**: All bugs get a test case

## Test Structure

```
tests/
├── conftest.py                 # Global fixtures
├── core/                       # Core financial calculations
│   └── test_technical_analysis.py
├── domain/                     # Business logic tests
│   ├── conftest.py
│   └── test_technical_analysis_service.py
├── services/                   # Service layer tests
│   ├── conftest.py
│   ├── test_screening_service.py
│   ├── test_stock_cache_manager.py
│   ├── test_stock_data_fetcher.py
│   └── test_market_calendar_service.py
├── providers/                  # External API integration
│   └── test_stock_data_simple.py
├── data/                       # Database models
│   └── test_portfolio_models.py
├── strategies/                 # Trading strategies
│   └── test_market_strategy.py
├── concall/                    # Conference call system
│   ├── models/
│   ├── providers/
│   └── utils/
├── integration/                # Integration tests
│   ├── base.py
│   ├── test_api_technical.py
│   ├── test_mcp_tools.py
│   ├── test_redis_cache.py
│   ├── test_full_backtest_workflow.py
│   └── test_orchestration_complete.py
└── performance/                # Performance tests
    ├── test_benchmarks.py
    ├── test_load.py
    ├── test_profiling.py
    └── test_stress.py
```

## Running Tests

### Quick Commands

```bash
# Unit tests only (5-10 seconds)
make test

# Specific test file
make test-specific TEST=test_screening_service

# Watch mode (auto-rerun on changes)
make test-watch

# With coverage report
make test-cov

# All tests (including integration)
make test-all

# Integration tests only
make test-integration

# Performance tests
make test-performance
```

### Using uv (Recommended)

```bash
# Unit tests (fast, no external dependencies)
uv run pytest

# With coverage
uv run pytest --cov=maverick_mcp --cov-report=html

# Integration tests (requires PostgreSQL/Redis)
uv run pytest -m integration

# Specific markers
uv run pytest -m "not slow"
uv run pytest -m "unit"
uv run pytest -m "database"

# Parallel execution (faster)
uv run pytest -n auto

# Show slowest tests
uv run pytest --durations=10
```

### Direct pytest

```bash
# If in activated venv
pytest                                    # Unit tests
pytest -m integration                     # Integration tests
pytest -k "test_screening"                # Match pattern
pytest tests/services/                    # Specific directory
pytest --lf                               # Last failed
pytest --ff                               # Failed first
```

## Test Categories

### Markers

Tests are categorized using pytest markers:

```python
@pytest.mark.unit           # Unit tests (default)
@pytest.mark.integration    # Integration tests
@pytest.mark.slow           # Slow tests (>1s)
@pytest.mark.external       # Requires external APIs
@pytest.mark.database       # Requires database
@pytest.mark.redis          # Requires Redis
```

**Usage:**
```bash
# Run only unit tests
pytest -m unit

# Exclude slow tests
pytest -m "not slow"

# Integration + database tests
pytest -m "integration and database"

# Everything except external API tests
pytest -m "not external"
```

### Test Types

#### 1. Unit Tests (Default)

**Purpose**: Test individual functions/classes in isolation

**Characteristics**:
- No external dependencies
- Uses mocks/stubs
- Fast (<100ms per test)
- High coverage target (90%+)

**Example:**
```python
"""tests/services/test_screening_service.py"""

import pytest
from unittest.mock import Mock, patch

from maverick_mcp.services.screening_service import ScreeningService


class TestScreeningServiceInitialization:
    """Test initialization and configuration."""

    def test_initializes_without_session(self):
        """Test initialization without provided session."""
        service = ScreeningService()
        assert service._db_session is None

    def test_initializes_with_session(self):
        """Test initialization with injected session."""
        mock_session = Mock(spec=Session)
        service = ScreeningService(db_session=mock_session)
        assert service._db_session == mock_session


class TestGetMaverickRecommendations:
    """Test Maverick bullish recommendations."""

    @patch('maverick_mcp.services.screening_service.SessionLocal')
    def test_returns_recommendations_successfully(self, mock_session_local):
        """Test successful retrieval of bullish recommendations."""
        mock_stock = Mock()
        mock_stock.combined_score = 95
        mock_query = Mock()
        mock_query.all.return_value = [mock_stock]

        mock_session = Mock()
        mock_session.query.return_value = mock_query
        mock_session_local.return_value = mock_session

        service = ScreeningService()
        results = service.get_maverick_recommendations(limit=10)

        assert len(results) == 1
        assert results[0]["ticker_symbol"] == "AAPL"
```

#### 2. Integration Tests

**Purpose**: Test component interactions

**Characteristics**:
- Real database/Redis connections
- May call external APIs (with VCR recording)
- Slower (100ms-5s per test)
- Tests full workflows

**Example:**
```python
"""tests/integration/test_mcp_tools.py"""

import pytest
from fastmcp.testutils import client_for

from maverick_mcp.api.server import mcp


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_stock_data_integration():
    """Test get_stock_data tool end-to-end."""
    async with client_for(mcp) as client:
        # Call MCP tool
        result = await client.call_tool(
            "get_stock_data",
            arguments={
                "ticker": "AAPL",
                "period": "1mo"
            }
        )

        # Verify response structure
        assert result["status"] == "success"
        assert "data" in result
        assert len(result["data"]) > 0

        # Verify data quality
        first_row = result["data"][0]
        assert "Date" in first_row
        assert "Close" in first_row
        assert first_row["Close"] > 0
```

#### 3. End-to-End Tests

**Purpose**: Test full user workflows

**Characteristics**:
- Simulates real user scenarios
- Multiple components involved
- Slowest (5-30s per test)
- Critical path testing

**Example:**
```python
"""tests/integration/test_full_backtest_workflow.py"""

@pytest.mark.integration
@pytest.mark.slow
async def test_complete_backtest_workflow():
    """Test complete backtest from strategy to report."""
    async with client_for(mcp) as client:
        # Step 1: Fetch stock data
        data_result = await client.call_tool(
            "get_stock_data",
            arguments={"ticker": "SPY", "period": "1y"}
        )
        assert data_result["status"] == "success"

        # Step 2: Run backtest
        backtest_result = await client.call_tool(
            "run_backtest",
            arguments={
                "ticker": "SPY",
                "strategy": "momentum",
                "start_date": "2024-01-01"
            }
        )
        assert backtest_result["metrics"]["sharpe_ratio"] > 0

        # Step 3: Generate report
        report_result = await client.call_tool(
            "get_backtest_report",
            arguments={"backtest_id": backtest_result["id"]}
        )
        assert "html" in report_result
```

#### 4. Performance Tests

**Purpose**: Ensure system meets performance targets

**Characteristics**:
- Measures latency, throughput
- Resource usage monitoring
- Stress testing
- Regression detection

**Example:**
```python
"""tests/performance/test_benchmarks.py"""

import time
import pytest

from maverick_mcp.services.screening_service import ScreeningService


@pytest.mark.performance
def test_screening_performance(benchmark):
    """Test screening completes in under 500ms."""
    service = ScreeningService()

    result = benchmark(
        service.get_maverick_recommendations,
        limit=100
    )

    # Performance assertions
    assert benchmark.stats.mean < 0.5  # 500ms
    assert len(result) == 100


@pytest.mark.performance
@pytest.mark.slow
def test_parallel_agent_speedup():
    """Test parallel research achieves 7x+ speedup."""
    from maverick_mcp.domain.research.agents import ParallelResearchOrchestrator

    orchestrator = ParallelResearchOrchestrator(num_agents=6)

    start = time.time()
    results = orchestrator.research_comprehensive("AAPL")
    elapsed = time.time() - start

    # Should complete in 30s with 6 agents vs 180s sequential
    assert elapsed < 30
    assert results["speedup_factor"] >= 7
```

## Writing Tests

### Test Structure (AAA Pattern)

Follow **Arrange-Act-Assert** pattern:

```python
def test_calculate_rsi():
    """Test RSI calculation for sample data."""
    # Arrange - Set up test data
    data = create_sample_ohlcv_data()
    expected_rsi = 65.5

    # Act - Execute function under test
    result = calculate_rsi(data, period=14)

    # Assert - Verify results
    assert "RSI" in result.columns
    assert abs(result["RSI"].iloc[-1] - expected_rsi) < 0.1
```

### Fixtures

**Global fixtures** (`tests/conftest.py`):
```python
"""tests/conftest.py"""

import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from maverick_mcp.data.models import Base


@pytest.fixture
def sample_ohlcv_data():
    """Sample OHLCV data for testing."""
    return pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=100),
        'Open': range(100, 200),
        'High': range(105, 205),
        'Low': range(95, 195),
        'Close': range(100, 200),
        'Volume': [1000000] * 100
    })


@pytest.fixture
def test_db_session():
    """In-memory SQLite session for testing."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    from unittest.mock import Mock

    client = Mock()
    client.get.return_value = None
    client.set.return_value = True

    return client
```

**Service-specific fixtures** (`tests/services/conftest.py`):
```python
"""tests/services/conftest.py"""

import pytest
from maverick_mcp.services.screening_service import ScreeningService


@pytest.fixture
def screening_service(test_db_session):
    """ScreeningService instance with test database."""
    return ScreeningService(db_session=test_db_session)
```

### Mocking

**Use `unittest.mock` for dependencies:**

```python
from unittest.mock import Mock, patch, MagicMock


# Mock external API calls
@patch('maverick_mcp.providers.stock_data.requests.get')
def test_fetch_stock_data(mock_get):
    """Test stock data fetching with mocked API."""
    # Arrange
    mock_response = Mock()
    mock_response.json.return_value = {"close": [100, 101, 102]}
    mock_get.return_value = mock_response

    # Act
    from maverick_mcp.providers.stock_data import fetch_stock_data
    result = fetch_stock_data("AAPL")

    # Assert
    assert result["close"] == [100, 101, 102]
    mock_get.assert_called_once()


# Mock class methods
@patch.object(ScreeningService, '_get_db_session')
def test_screening_with_mock_session(mock_get_session):
    """Test screening with mocked database."""
    mock_session = Mock()
    mock_get_session.return_value = (mock_session, False)

    service = ScreeningService()
    # Test continues...
```

### Async Testing

**Use `pytest-asyncio` for async functions:**

```python
import pytest


@pytest.mark.asyncio
async def test_async_research():
    """Test async research agent."""
    from maverick_mcp.domain.research.agents import ResearchAgent

    agent = ResearchAgent()
    result = await agent.research_company("AAPL")

    assert result["company_name"] == "Apple Inc."
    assert "financials" in result


# Multiple async operations
@pytest.mark.asyncio
async def test_parallel_execution():
    """Test parallel agent execution."""
    import asyncio
    from maverick_mcp.domain.research.agents import create_agents

    agents = create_agents(count=6)

    # Run agents in parallel
    results = await asyncio.gather(*[
        agent.research("AAPL") for agent in agents
    ])

    assert len(results) == 6
    assert all(r["status"] == "success" for r in results)
```

### Testing Exceptions

```python
import pytest


def test_invalid_ticker_raises_error():
    """Test that invalid ticker raises ValueError."""
    from maverick_mcp.providers.stock_data import StockDataProvider

    provider = StockDataProvider()

    with pytest.raises(ValueError, match="Invalid ticker format"):
        provider.get_stock_data("INVALID@TICKER")


def test_api_error_handling():
    """Test graceful handling of API errors."""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException("API unavailable")

        provider = StockDataProvider()
        result = provider.get_stock_data("AAPL")

        # Should return error dict instead of raising
        assert result["status"] == "error"
        assert "API unavailable" in result["message"]
```

## Financial Testing

### Calculation Accuracy

**Test against known values:**

```python
def test_rsi_calculation_accuracy():
    """Test RSI matches established reference values."""
    # Use data from tradingview.com or investing.com
    reference_data = load_reference_data("AAPL_2024-01-01_2024-12-31")

    result = calculate_rsi(reference_data, period=14)

    # RSI should match reference within 0.1%
    expected_rsi = 65.42
    actual_rsi = result["RSI"].iloc[-1]

    tolerance = expected_rsi * 0.001  # 0.1% tolerance
    assert abs(actual_rsi - expected_rsi) < tolerance


def test_sharpe_ratio_calculation():
    """Test Sharpe ratio formula correctness."""
    # Annual returns: 15%, Volatility: 20%, Risk-free: 3%
    returns = pd.Series([0.01] * 12)  # Monthly returns
    risk_free_rate = 0.03

    sharpe = calculate_sharpe_ratio(returns, risk_free_rate)

    # Expected: (15% - 3%) / 20% = 0.6
    assert abs(sharpe - 0.6) < 0.05
```

### Edge Cases

```python
def test_rsi_with_flat_prices():
    """Test RSI when prices don't change."""
    data = pd.DataFrame({
        'Close': [100] * 50  # Flat prices
    })

    result = calculate_rsi(data, period=14)

    # RSI should be 50 (neutral)
    assert result["RSI"].iloc[-1] == 50.0


def test_portfolio_with_zero_variance():
    """Test portfolio optimization with zero variance asset."""
    # Asset with zero variance should be handled gracefully
    returns = pd.DataFrame({
        'CASH': [0.0] * 100,  # Zero variance
        'SPY': np.random.normal(0.001, 0.02, 100)
    })

    optimizer = PortfolioOptimizer()
    result = optimizer.optimize(returns)

    # Should not crash, should allocate 100% to CASH (min variance)
    assert result["weights"]["CASH"] == 1.0
```

## Coverage Requirements

### Target Coverage

| Component | Target | Critical Path |
|-----------|--------|---------------|
| **Core calculations** | 95%+ | Financial formulas |
| **Services** | 90%+ | Business logic |
| **API/Routers** | 85%+ | MCP tools |
| **Providers** | 80%+ | External integrations |
| **Models** | 70%+ | Data structures |
| **Utils** | 80%+ | Helper functions |

### Running Coverage

```bash
# HTML report (detailed)
make test-cov
open htmlcov/index.html

# Terminal report
uv run pytest --cov=maverick_mcp --cov-report=term-missing

# XML report (for CI/CD)
uv run pytest --cov=maverick_mcp --cov-report=xml

# Fail if coverage below 60%
uv run pytest --cov-fail-under=60
```

### Coverage Configuration

**pytest.ini**:
```ini
[coverage:run]
source = maverick_mcp
omit =
    */tests/*
    */__pycache__/*

[coverage:report]
precision = 2
show_missing = True
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

## VCR for External APIs

Use **VCR.py** to record/replay HTTP requests:

```python
import pytest
import vcr


@pytest.mark.external
@vcr.use_cassette('tests/vcr_cassettes/tiingo_aapl.yaml')
def test_tiingo_api():
    """Test Tiingo API with recorded response."""
    from maverick_mcp.providers.stock_data import StockDataProvider

    provider = StockDataProvider(api_key="test_key")
    result = provider.get_stock_data("AAPL", period="1mo")

    assert len(result) > 0
    assert "Close" in result.columns
```

**Benefits:**
- ✅ Tests run without API keys
- ✅ Consistent test results
- ✅ Fast execution (no network calls)
- ✅ Works offline

**Recording new cassettes:**
```bash
# Delete old cassette
rm tests/vcr_cassettes/tiingo_aapl.yaml

# Run test with real API (records response)
TIINGO_API_KEY=real_key pytest tests/test_stock_data.py
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync --extra dev

      - name: Run unit tests
        run: uv run pytest -m "not integration"

      - name: Run integration tests
        run: uv run pytest -m integration
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/test
          REDIS_HOST: localhost

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Test Data Management

### Sample Data

**Create reusable test data:**

```python
# tests/fixtures/sample_data.py

import pandas as pd
import numpy as np


def create_sample_ohlcv(days=100, start_price=100):
    """Create sample OHLCV data with realistic patterns."""
    dates = pd.date_range('2024-01-01', periods=days)

    # Simulate random walk
    returns = np.random.normal(0.001, 0.02, days)
    close_prices = start_price * (1 + returns).cumprod()

    return pd.DataFrame({
        'Date': dates,
        'Open': close_prices * np.random.uniform(0.99, 1.01, days),
        'High': close_prices * np.random.uniform(1.00, 1.02, days),
        'Low': close_prices * np.random.uniform(0.98, 1.00, days),
        'Close': close_prices,
        'Volume': np.random.randint(1000000, 5000000, days)
    })
```

### Database Seeding

```python
# tests/fixtures/db_fixtures.py

@pytest.fixture
def seeded_db(test_db_session):
    """Database with S&P 500 stocks seeded."""
    from maverick_mcp.data.models import Stock, ScreeningScore

    # Add sample stocks
    stocks = [
        Stock(ticker_symbol="AAPL", company_name="Apple Inc."),
        Stock(ticker_symbol="MSFT", company_name="Microsoft Corp."),
        Stock(ticker_symbol="GOOGL", company_name="Alphabet Inc."),
    ]
    test_db_session.add_all(stocks)

    # Add screening scores
    scores = [
        ScreeningScore(
            ticker_symbol="AAPL",
            strategy="maverick_bullish",
            combined_score=95,
            date=datetime.now()
        )
    ]
    test_db_session.add_all(scores)
    test_db_session.commit()

    return test_db_session
```

## Best Practices

### 1. Test Organization

```python
# ✅ Good - Organized by functionality
class TestScreeningServiceInitialization:
    def test_initializes_without_session(self): ...
    def test_initializes_with_session(self): ...

class TestMaverickRecommendations:
    def test_returns_top_stocks(self): ...
    def test_filters_by_score(self): ...
    def test_handles_empty_results(self): ...
```

### 2. Descriptive Test Names

```python
# ✅ Good - Clear intent
def test_rsi_returns_correct_value_for_uptrend(): ...
def test_api_retries_on_timeout(): ...
def test_portfolio_optimization_with_zero_variance_asset(): ...

# ❌ Bad - Unclear
def test_rsi(): ...
def test_api(): ...
def test_portfolio(): ...
```

### 3. Test Independence

```python
# ✅ Good - Each test is independent
def test_screening_returns_results():
    service = ScreeningService()  # Fresh instance
    results = service.get_maverick_recommendations()
    assert len(results) > 0

def test_screening_limits_results():
    service = ScreeningService()  # Fresh instance
    results = service.get_maverick_recommendations(limit=5)
    assert len(results) == 5

# ❌ Bad - Tests depend on shared state
service = ScreeningService()  # Shared instance

def test_screening_returns_results():
    results = service.get_maverick_recommendations()
    assert len(results) > 0

def test_screening_limits_results():
    # Depends on previous test state
    results = service.get_maverick_recommendations(limit=5)
    assert len(results) == 5
```

### 4. Single Assertion per Test

```python
# ✅ Good - One concept per test
def test_rsi_column_exists():
    result = calculate_rsi(data)
    assert "RSI" in result.columns

def test_rsi_range_is_valid():
    result = calculate_rsi(data)
    assert result["RSI"].between(0, 100).all()

# ❌ Bad - Multiple unrelated assertions
def test_rsi():
    result = calculate_rsi(data)
    assert "RSI" in result.columns
    assert result["RSI"].between(0, 100).all()
    assert len(result) == len(data)
    assert result["RSI"].dtype == float
```

### 5. Use Parametrized Tests

```python
import pytest


@pytest.mark.parametrize("ticker,expected_market", [
    ("AAPL", "US"),
    ("RELIANCE.NS", "NSE"),
    ("TCS.BO", "BSE"),
])
def test_market_detection(ticker, expected_market):
    """Test market detection for various ticker formats."""
    market = detect_market(ticker)
    assert market == expected_market


@pytest.mark.parametrize("period,expected_days", [
    ("1d", 1),
    ("1mo", 30),
    ("1y", 365),
])
def test_period_parsing(period, expected_days):
    """Test period string parsing."""
    days = parse_period(period)
    assert days == expected_days
```

## Troubleshooting Tests

### Common Issues

**1. Import errors:**
```bash
# Install package in editable mode
uv pip install -e .

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**2. Database connection errors:**
```bash
# Check PostgreSQL is running
pg_isctl status

# Use in-memory SQLite for unit tests
DATABASE_URL=sqlite:///:memory: pytest
```

**3. Redis connection errors:**
```bash
# Check Redis is running
redis-cli ping

# Skip Redis tests
pytest -m "not redis"
```

**4. Async errors:**
```python
# Ensure pytest-asyncio is configured
# pytest.ini
[pytest]
asyncio_mode = auto
```

**5. VCR cassette errors:**
```bash
# Delete old cassettes
rm tests/vcr_cassettes/*.yaml

# Re-record with real API
TIINGO_API_KEY=real_key pytest
```

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [VCR.py Documentation](https://vcrpy.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

---

**Next Steps:**
- Write tests for new features
- Improve coverage for critical paths
- Add integration tests for workflows
- Set up CI/CD testing pipeline
