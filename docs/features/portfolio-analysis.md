# Portfolio Analysis

Modern Portfolio Theory (MPT) and optimization tools.

## Features

### Portfolio Optimization
Build efficient portfolios using MPT:
- **Efficient Frontier**: Risk-return tradeoff curve
- **Optimal Weights**: Asset allocation percentages
- **Sharpe Ratio Maximization**: Best risk-adjusted return
- **Minimum Variance**: Lowest risk portfolio

### Risk Analysis
Comprehensive risk metrics:
- **Volatility**: Standard deviation of returns
- **Value at Risk (VaR)**: Potential loss estimates
- **Conditional VaR**: Expected loss beyond VaR
- **Maximum Drawdown**: Peak-to-trough decline
- **Beta**: Market sensitivity
- **Alpha**: Excess returns

### Correlation Analysis
Understand portfolio relationships:
- **Correlation Matrix**: Pairwise correlations
- **Diversification Score**: How well-diversified
- **Sector Exposure**: Concentration risk
- **Factor Analysis**: Common risk factors

## Usage Examples

### Build Portfolio
```
Create a portfolio with AAPL 10 shares at $150, MSFT 5 shares at $380
```

### Optimize Portfolio
```
Optimize portfolio weights for maximum Sharpe ratio: AAPL, MSFT, GOOGL
```

### Risk Analysis
```
Calculate portfolio risk metrics and correlation matrix
```

### Performance Tracking
```
Show portfolio performance over last 6 months
```

## Portfolio Optimization

### Efficient Frontier
Find optimal risk-return combinations:

**Inputs**:
- List of stocks/assets
- Historical returns (1-5 years)
- Target return or risk tolerance

**Outputs**:
- Optimal weight allocation
- Expected return
- Expected volatility
- Sharpe ratio
- Efficient frontier curve

**Example**:
```
Optimize portfolio: AAPL, MSFT, GOOGL, AMZN
Target return: 15% annually
```

### Constraints
Support for realistic constraints:
- Minimum/maximum position sizes
- Sector limits
- Long-only vs long-short
- Transaction costs
- Rebalancing frequency

## Risk Metrics

### Sharpe Ratio
**Formula**: (Portfolio Return - Risk-Free Rate) / Portfolio Volatility
- **Interpretation**: Return per unit of risk
- **Good**: > 1.0
- **Excellent**: > 2.0

### Sortino Ratio
**Formula**: (Portfolio Return - Target) / Downside Deviation
- **Focus**: Only penalizes downside volatility
- **Better Than Sharpe**: For asymmetric returns

### Maximum Drawdown
**Definition**: Largest peak-to-trough decline
- **Risk Measure**: Worst-case historical loss
- **Recovery Time**: How long to recover

### Beta
**Definition**: Sensitivity to market movements
- **Beta = 1**: Moves with market
- **Beta > 1**: More volatile than market
- **Beta < 1**: Less volatile than market

## Correlation Analysis

### Benefits of Diversification
Low correlation assets reduce portfolio risk:
- **Correlation = 1**: No diversification benefit
- **Correlation = 0**: Partial diversification
- **Correlation = -1**: Maximum diversification

### Correlation Matrix
See relationships between all assets:
```
Calculate correlation matrix for AAPL, MSFT, GOOGL, GLD, TLT
```

Helps identify:
- Similar-moving assets
- Diversification opportunities
- Hedging candidates
- Sector concentration

## Backtesting Integration

Test portfolio strategies historically:
```
Backtest 60/40 stock/bond portfolio over 10 years
```

Compare strategies:
- Buy and hold vs rebalancing
- Equal weight vs optimized
- Sector rotation vs static
- Different rebalancing frequencies

## Performance Attribution

Understand where returns come from:
- **Asset Selection**: Stock-picking skill
- **Sector Allocation**: Sector timing
- **Market Timing**: Entry/exit timing
- **Diversification**: Risk reduction benefit

## Rebalancing

Automatic rebalancing recommendations:
- **Threshold-Based**: Rebalance when drift > X%
- **Calendar-Based**: Monthly, quarterly, annually
- **Optimization-Based**: When Sharpe ratio declines

## API Reference

See [Portfolio Tools](../user-guide/mcp-tools.md#portfolio) for complete API documentation.

## Example Portfolios

### Conservative
- 60% bonds
- 30% large-cap stocks
- 10% cash/gold

### Balanced
- 40% US stocks
- 20% International stocks
- 30% bonds
- 10% alternatives

### Aggressive
- 80% stocks (mix of cap sizes)
- 15% alternatives
- 5% cash

### Indian Market
- 50% Nifty 50 stocks
- 30% Mid-cap stocks
- 20% bonds/gold
