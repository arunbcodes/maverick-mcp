# Testing & Coverage Guide

This document explains how to run tests and generate coverage reports for MaverickMCP.

---

## 🧪 **Running Tests**

### Quick Start

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_stock_data.py

# Run tests matching pattern
pytest -k "test_symbol"

# Run with verbose output
pytest -v
```

###  Using Make Commands

```bash
# Run all tests (fastest)
make test

# Run with coverage (recommended)
make test-cov

# Run specific test file
pytest tests/test_multi_market.py -v
```

---

## 📊 **Test Coverage**

### Configuration

Coverage is configured in `pytest.ini` with the following settings:

- **Minimum Coverage:** 60% (fails below this)
- **Branch Coverage:** Enabled
- **Report Formats:** Terminal, HTML, XML
- **Source:** `maverick_mcp/` package
- **Excluded:** Tests, venv, build files

### Running Coverage

**Option 1: Using Script** (Recommended)
```bash
./scripts/run_coverage.sh
```

**Option 2: Using pytest**
```bash
pytest --cov=maverick_mcp --cov-report=html
```

**Option 3: Using Make**
```bash
make test-cov
```

### Viewing Coverage Reports

**Terminal Report:**
- Automatically displayed after test run
- Shows % coverage and missing lines

**HTML Report:**
```bash
# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html

# Windows
start htmlcov/index.html
```

**XML Report:**
- Generated as `coverage.xml`
- Used by CI/CD tools

---

## 🎯 **Coverage Targets**

### Current Targets

| Module | Target | Status |
|--------|--------|--------|
| **Overall** | 60% | ✅ Enforced |
| **Core Services** | 70%+ | 🎯 Recommended |
| **Providers** | 60%+ | 🎯 Recommended |
| **Utilities** | 80%+ | 🎯 Recommended |
| **Strategies** | 80%+ | 🎯 Recommended |

### Excluded from Coverage

The following are automatically excluded:
- `__repr__` and `__str__` methods
- Abstract methods
- Debug logging statements
- Type checking blocks (`if TYPE_CHECKING:`)
- Defensive `pass` statements
- `if __name__ == "__main__":` blocks

---

## 📝 **Writing Tests**

### Test Structure

```python
"""
Test module docstring.
"""

import pytest
from maverick_mcp.services import SomeService


class TestSomeService:
    """Tests for SomeService."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        service = SomeService()
        result = service.do_something()
        assert result is not None
    
    def test_error_handling(self):
        """Test error handling."""
        service = SomeService()
        with pytest.raises(ValueError):
            service.do_invalid_thing()
```

### Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
def test_with_database(db_session):
    """Test using database fixture."""
    # db_session is automatically provided
    stock = Stock.get_or_create(db_session, "AAPL")
    assert stock is not None
```

### Parametrized Tests

```python
@pytest.mark.parametrize("symbol,expected", [
    ("AAPL", Market.US),
    ("RELIANCE.NS", Market.INDIA_NSE),
    ("TCS.BO", Market.INDIA_BSE),
])
def test_market_detection(symbol, expected):
    """Test market detection for various symbols."""
    market = get_market_from_symbol(symbol)
    assert market == expected
```

---

## 🏗️ **Test Organization**

### Directory Structure

```
tests/
├── conftest.py           # Shared fixtures
├── test_services/        # Service tests
│   ├── test_calendar.py
│   ├── test_cache.py
│   └── test_fetcher.py
├── test_providers/       # Provider tests
│   ├── test_stock_data.py
│   └── test_indian_market.py
├── test_strategies/      # Strategy tests
│   └── test_market_strategy.py
└── test_utils/           # Utility tests
    ├── test_validators.py
    └── test_datetime_utils.py
```

### Test Categories

**Unit Tests:**
- Test individual functions/methods
- No external dependencies
- Fast execution
- Example: `test_validators.py`

**Integration Tests:**
- Test component interactions
- May use database/network
- Slower execution
- Example: `test_stock_data.py`

**End-to-End Tests:**
- Test complete workflows
- Use real services
- Slowest execution
- Example: `test_screening.py`

---

## 🚀 **CI/CD Integration**

### GitHub Actions (Future)

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -e ".[dev]"
      - run: pytest --cov=maverick_mcp --cov-report=xml
      - uses: codecov/codecov-action@v3
```

### Coverage Badges

After CI/CD setup, add badge to README:

```markdown
[![Coverage](https://codecov.io/gh/arunbcodes/maverick-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/arunbcodes/maverick-mcp)
```

---

## 💡 **Best Practices**

### DO:
- ✅ Write tests for new features
- ✅ Test edge cases and error conditions
- ✅ Use descriptive test names
- ✅ Keep tests independent
- ✅ Mock external services
- ✅ Aim for 70%+ coverage on new code

### DON'T:
- ❌ Skip tests for "simple" code
- ❌ Test implementation details
- ❌ Write flaky tests
- ❌ Depend on test execution order
- ❌ Use real API keys in tests
- ❌ Commit coverage reports to git

---

## 🔍 **Improving Coverage**

### Identify Low Coverage Areas

```bash
# Run coverage with missing lines
pytest --cov=maverick_mcp --cov-report=term-missing

# View HTML report for detailed analysis
open htmlcov/index.html
```

### Common Gaps

1. **Error Handling:**
   ```python
   # Add tests for exception paths
   def test_invalid_input():
       with pytest.raises(ValidationError):
           validate_symbol("")
   ```

2. **Edge Cases:**
   ```python
   # Test boundary conditions
   def test_date_range_edge_cases():
       assert validate_date_range("2024-01-01", "2024-01-01")  # Same day
       assert validate_date_range("2024-02-29", "2024-03-01")  # Leap year
   ```

3. **Abstract Methods:**
   ```python
   # Test all concrete implementations
   def test_all_market_strategies():
       for market in [Market.US, Market.INDIA_NSE, Market.INDIA_BSE]:
           strategy = MarketStrategyFactory.get_strategy_by_market(market)
           assert strategy.is_valid_symbol("TEST")
   ```

---

## 📈 **Coverage Goals**

### Short Term (Current)
- ✅ 60% overall coverage enforced
- ✅ All new utilities have 80%+ coverage
- ✅ Critical services have 70%+ coverage

### Medium Term (Next 3 months)
- 🎯 70% overall coverage
- 🎯 All services have 75%+ coverage
- 🎯 All strategies have 90%+ coverage

### Long Term (6 months)
- 🎯 80% overall coverage
- 🎯 All new code requires 80%+ coverage
- 🎯 Automated coverage checks in CI/CD

---

## 🛠️ **Troubleshooting**

### Tests Failing with Docker Error

```bash
# Start Docker Desktop first, or:
pytest tests/test_validators.py  # Run only unit tests
```

### Coverage Report Not Generated

```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Check pytest.ini configuration
cat pytest.ini
```

### Coverage Below Threshold

```bash
# Run with detailed report
pytest --cov=maverick_mcp --cov-report=term-missing

# Identify missing coverage
open htmlcov/index.html
```

---

## 📚 **Resources**

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Happy Testing!** 🧪✨

