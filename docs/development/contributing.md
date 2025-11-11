# Contributing to Maverick MCP

Thank you for your interest in contributing to Maverick MCP!

## Quick Links

- **Root Contributing Guide**: See [CONTRIBUTING.md](../../CONTRIBUTING.md) in the project root for complete guidelines
- **Code of Conduct**: Be respectful, inclusive, and constructive
- **License**: Apache 2.0 - see [LICENSE](../../LICENSE)

## For New Contributors

### Getting Started

**1. Fork and Clone**
```bash
# Fork on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/maverick-mcp.git
cd maverick-mcp
```

**2. Set Up Development Environment**
```bash
# Install dependencies
uv sync --extra dev

# Configure environment
cp .env.example .env
# Add your TIINGO_API_KEY

# Start development server
make dev
```

**3. Create a Branch**
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### Development Workflow

**Quick Commands**:
```bash
make dev           # Start development server
make test          # Run tests (5-10 seconds)
make lint          # Check code quality
make format        # Auto-format code
make typecheck     # Type checking
make check         # Run all checks
```

**Development Loop**:
1. Make changes to code
2. Run `make test` to verify
3. Run `make format` to format
4. Run `make check` to validate
5. Commit changes
6. Push and create PR

### What to Contribute

#### 🐛 Bug Fixes
- Check [GitHub Issues](https://github.com/arunbcodes/maverick-mcp/issues)
- Comment on issue before starting work
- Include test case that reproduces the bug
- Reference issue number in commit/PR

#### ✨ New Features
- Open issue to discuss before implementing
- Follow existing patterns and architecture
- Add comprehensive tests
- Update documentation

#### 📚 Documentation
- Fix typos and improve clarity
- Add examples and use cases
- Update outdated information
- Add diagrams where helpful

#### 🧪 Tests
- Increase test coverage
- Add integration tests
- Add edge case tests
- Improve test performance

#### 🎨 Code Quality
- Refactoring for clarity
- Performance improvements
- Type hint additions
- Code simplification

### Not Accepting

❌ **We generally don't accept**:
- Breaking changes without discussion
- Large refactors without prior agreement
- Features that duplicate existing functionality
- Changes without tests
- PRs that fail CI checks

**Before spending time on large changes**, open an issue to discuss!

## Commit Guidelines

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding/updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

**Examples**:
```
feat(research): Add parallel agent orchestration

Implement multi-agent research system with 6 parallel agents
for faster comprehensive stock analysis. Achieves 7-256x speedup
over sequential execution.

Closes #42
```

```
fix(cache): Prevent Redis connection leak

Add connection pooling and proper cleanup to prevent
memory leaks in long-running processes.

Fixes #128
```

```
docs(deployment): Add Rancher Desktop guide

Comprehensive guide for running Maverick MCP with Rancher Desktop
including configuration, troubleshooting, and best practices.
```

### Commit Best Practices

✅ **Good Commits**:
- Atomic (one logical change)
- Descriptive subject line (< 72 chars)
- Explain "why" in body, not "what"
- Reference issues/PRs

❌ **Avoid**:
- "Fix stuff" or "WIP"
- Mixing multiple unrelated changes
- Committing commented-out code
- Committing secrets or API keys

## Pull Request Process

### Before Submitting

**Checklist**:
- [ ] Code follows project style guide
- [ ] Tests pass locally (`make test`)
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages follow guidelines
- [ ] No merge conflicts with main
- [ ] PR description is clear and complete

### PR Title Format

Same as commit messages:
```
feat(concall): Add sentiment analysis tool
fix(providers): Handle API rate limiting
docs(api): Document portfolio optimization
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Related Issues
Closes #123
Relates to #456

## Screenshots (if applicable)
```

### Review Process

1. **Automated Checks**: Must pass CI/CD
2. **Code Review**: At least one maintainer approval
3. **Testing**: Reviewer tests changes locally
4. **Discussion**: Address review comments
5. **Merge**: Squash and merge to main

**Review Timeline**:
- Small fixes: 1-2 days
- Features: 3-7 days
- Large changes: 1-2 weeks

## Development Best Practices

### Code Quality

**Follow the Style Guide**:
- See [Code Style Guide](code-style.md)
- Use `make format` to auto-format
- Use `make lint` to check
- Use `make typecheck` for types

**Write Clean Code**:
- Self-documenting names
- Single Responsibility Principle
- DRY (Don't Repeat Yourself)
- SOLID principles
- Appropriate comments

**Type Hints**:
```python
# Good
def calculate_rsi(
    data: pd.DataFrame,
    period: int = 14,
    price_col: str = "Close"
) -> pd.DataFrame:
    """Calculate RSI indicator."""
    ...

# Bad
def calculate_rsi(data, period=14, price_col="Close"):
    ...
```

### Testing

**Write Tests First (TDD)**:
1. Write failing test
2. Write minimum code to pass
3. Refactor

**Test Coverage**:
- Aim for 80%+ coverage
- Test happy path
- Test edge cases
- Test error handling

**Test Types**:
```python
# Unit test
def test_calculate_rsi():
    data = create_sample_data()
    result = calculate_rsi(data, period=14)
    assert 'RSI' in result.columns
    assert result['RSI'].iloc[-1] > 0

# Integration test
@pytest.mark.integration
def test_research_tool_end_to_end():
    tool = ResearchTool()
    result = tool.research_comprehensive("AAPL")
    assert result['company_name'] == "Apple Inc."
```

### Documentation

**Docstring Format** (Google style):
```python
def optimize_portfolio(
    tickers: list[str],
    target_return: float | None = None
) -> dict:
    """Optimize portfolio using Modern Portfolio Theory.
    
    Args:
        tickers: List of stock symbols to include
        target_return: Target annual return (optional)
    
    Returns:
        Dictionary containing:
            - optimal_weights: Asset allocation percentages
            - expected_return: Projected annual return
            - sharpe_ratio: Risk-adjusted return metric
    
    Raises:
        ValueError: If tickers list is empty
        APIError: If stock data cannot be fetched
    
    Example:
        >>> result = optimize_portfolio(["AAPL", "MSFT", "GOOGL"])
        >>> print(result['sharpe_ratio'])
        1.85
    """
    ...
```

**Update Documentation**:
- Update relevant .md files
- Add examples
- Keep docs in sync with code
- Test code examples

## Financial Domain Guidelines

### Data Accuracy

**Critical**: Financial data must be accurate!

- Always validate data sources
- Handle missing data appropriately
- Document data limitations
- Test with real market data
- Be transparent about approximations

### Calculation Correctness

**Follow Standards**:
- Use established formulas (RSI, MACD, etc.)
- Reference sources in comments
- Test against known examples
- Validate edge cases

**Example**:
```python
def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.03
) -> float:
    """Calculate Sharpe Ratio.
    
    Formula: (Portfolio Return - Risk-Free Rate) / Portfolio Volatility
    Reference: https://en.wikipedia.org/wiki/Sharpe_ratio
    
    Note: Risk-free rate should be annualized. Returns are assumed
    to be daily and will be annualized internally.
    """
    ...
```

### Compliance and Disclaimers

**Important**:
- Not financial advice
- For educational/personal use
- No guarantees on accuracy
- Users responsible for own decisions

**Add Disclaimers**:
```python
# In documentation
"""
DISCLAIMER: This tool is for educational and informational purposes only.
It does not constitute financial advice. Always do your own research and
consult with qualified financial advisors before making investment decisions.
"""
```

## Community

### Getting Help

- **Documentation**: https://arunbcodes.github.io/maverick-mcp/
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community chat
- **Code Review**: Learn from PR comments

### Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes for significant contributions
- GitHub contributor graph

## Additional Resources

- [Architecture Guide](architecture.md) - System design and patterns
- [Testing Guide](testing.md) - Comprehensive testing guide
- [Code Style Guide](code-style.md) - Style and conventions
- [Docker Deployment](../deployment/docker.md) - Container deployment
- [API Reference](../api-reference/core.md) - Complete API docs

## Questions?

If you have questions:
1. Check existing documentation
2. Search GitHub Issues
3. Ask in GitHub Discussions
4. Open a new issue with "question" label

Thank you for contributing to Maverick MCP! 🚀
