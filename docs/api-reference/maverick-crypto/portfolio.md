# Portfolio

Mixed stock and cryptocurrency portfolio management.

## MixedPortfolioService

Manage portfolios containing both stocks and cryptocurrencies.

::: maverick_crypto.portfolio.MixedPortfolioService
    options:
      show_root_heading: true
      members:
        - add_asset
        - get_performance
        - get_returns

### Example Usage

```python
from maverick_crypto.portfolio import MixedPortfolioService

portfolio = MixedPortfolioService()

# Add assets
portfolio.add_asset("AAPL", asset_type="stock", weight=0.3)
portfolio.add_asset("MSFT", asset_type="stock", weight=0.2)
portfolio.add_asset("BTC", asset_type="crypto", weight=0.3)
portfolio.add_asset("ETH", asset_type="crypto", weight=0.2)

# Get performance
performance = await portfolio.get_performance(
    start_date="2024-01-01",
    end_date="2024-12-31"
)

print(f"Total Return: {performance['total_return']}%")
print(f"Volatility: {performance['volatility']}%")
print(f"Sharpe Ratio: {performance['sharpe_ratio']}")
```

## CorrelationAnalyzer

Calculate correlation between assets.

::: maverick_crypto.portfolio.CorrelationAnalyzer
    options:
      show_root_heading: true
      members:
        - calculate_correlation_matrix
        - get_diversification_score
        - find_uncorrelated_pairs

### Example Usage

```python
from maverick_crypto.portfolio import CorrelationAnalyzer

analyzer = CorrelationAnalyzer()

# Get correlation matrix
correlation = await analyzer.calculate_correlation_matrix(
    assets=["AAPL", "BTC", "ETH", "SPY"],
    days=252
)

# Diversification score (0-10)
score = analyzer.get_diversification_score(correlation)
print(f"Diversification Score: {score}/10")

# Find uncorrelated pairs
pairs = analyzer.find_uncorrelated_pairs(correlation, threshold=0.3)
```

### Correlation Interpretation

| Value | Interpretation |
|-------|----------------|
| 1.0 | Perfect positive |
| 0.5-0.9 | Strongly correlated |
| 0.2-0.5 | Moderately correlated |
| -0.2 to 0.2 | Uncorrelated |
| -0.5 to -0.2 | Moderate inverse |
| -1.0 to -0.5 | Strong inverse |

## PortfolioOptimizer

Mean-variance portfolio optimization.

::: maverick_crypto.portfolio.PortfolioOptimizer
    options:
      show_root_heading: true
      members:
        - optimize
        - efficient_frontier
        - get_optimal_weights

### Optimization Objectives

| Objective | Description |
|-----------|-------------|
| `max_sharpe` | Maximize risk-adjusted return |
| `min_volatility` | Minimize portfolio volatility |
| `max_return` | Maximize expected return |
| `risk_parity` | Equal risk contribution |

### Example Usage

```python
from maverick_crypto.portfolio import PortfolioOptimizer

optimizer = PortfolioOptimizer()

# Optimize for max Sharpe ratio
weights = await optimizer.optimize(
    assets=["AAPL", "MSFT", "BTC", "ETH"],
    objective="max_sharpe",
    constraints={
        "max_position": 0.4,  # Max 40% in any asset
        "min_position": 0.05,  # Min 5% in any asset
    }
)

print("Optimal Weights:")
for asset, weight in weights.items():
    print(f"  {asset}: {weight:.1%}")

# Get efficient frontier
frontier = await optimizer.efficient_frontier(
    assets=["AAPL", "MSFT", "BTC", "ETH"],
    points=20
)
```

### Constraints

| Constraint | Description |
|------------|-------------|
| `max_position` | Maximum weight per asset |
| `min_position` | Minimum weight per asset |
| `max_crypto` | Maximum total crypto allocation |
| `max_volatility` | Maximum portfolio volatility |

### Output Metrics

```python
result = await optimizer.optimize(...)

# Result structure
{
    "weights": {"AAPL": 0.25, "BTC": 0.35, ...},
    "expected_return": 0.15,  # 15%
    "volatility": 0.20,  # 20%
    "sharpe_ratio": 0.75,
    "diversification_ratio": 1.2,
}
```

## Asset Class Comparison

Compare performance between asset classes.

```python
from maverick_crypto.portfolio import MixedPortfolioService

portfolio = MixedPortfolioService()

# Compare stocks vs crypto
comparison = await portfolio.compare_asset_classes(
    stocks=["AAPL", "MSFT", "GOOGL"],
    crypto=["BTC", "ETH", "SOL"],
    period="1y"
)

print(f"Stock Returns: {comparison['stocks']['return']}%")
print(f"Crypto Returns: {comparison['crypto']['return']}%")
print(f"Correlation: {comparison['correlation']}")
```

## Best Practices

### Position Sizing

Due to crypto volatility, consider:

- **Max crypto allocation**: 10-30% of total portfolio
- **Individual position**: 2-5% per crypto asset
- **Rebalancing**: Quarterly or on significant moves

### Risk Management

```python
# Example with risk constraints
weights = await optimizer.optimize(
    assets=["AAPL", "MSFT", "GOOGL", "BTC", "ETH"],
    objective="max_sharpe",
    constraints={
        "max_crypto": 0.30,  # Max 30% in crypto
        "max_position": 0.25,  # Max 25% per asset
        "max_volatility": 0.25,  # Max 25% portfolio vol
    }
)
```

