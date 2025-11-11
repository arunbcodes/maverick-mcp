# Backtesting

VectorBT-powered strategy testing and optimization.

## Features

### Strategy Testing
Test trading strategies on historical data:
- **VectorBT Engine**: Vectorized high-performance
- **15+ Built-in Strategies**: Ready to use
- **Custom Strategies**: Define your own logic
- **Multi-Timeframe**: 1min to monthly data

### Performance Metrics
Comprehensive strategy evaluation:
- **Returns**: Total, annualized, CAGR
- **Risk Metrics**: Sharpe, Sortino, Calmar ratios
- **Drawdowns**: Maximum, average, recovery time
- **Win Rate**: % of profitable trades
- **Profit Factor**: Gross profit / gross loss

### Optimization
Parameter tuning and walk-forward analysis:
- **Grid Search**: Test parameter combinations
- **Walk-Forward**: Out-of-sample validation
- **Monte Carlo**: Robustness testing
- **Cross-Validation**: Avoid overfitting

## Built-in Strategies

### Momentum Strategies
1. **RSI Strategy**: Buy oversold, sell overbought
2. **MACD Strategy**: Crossover signals
3. **Moving Average**: SMA/EMA crossovers
4. **Breakout**: New highs/lows

### Mean Reversion
5. **Bollinger Band**: Band touch reversions
6. **Mean Reversion**: Distance from average
7. **Pairs Trading**: Relative value

### ML-Powered
8. **Adaptive ML**: Machine learning signals
9. **Ensemble**: Multiple model combination
10. **Regime-Aware**: Market condition adaptation

### Advanced
11. **Portfolio Rebalancing**: Multi-asset
12. **Sector Rotation**: Momentum sectors
13. **Factor Investing**: Value, momentum, quality
14. **Options Strategies**: Covered calls, spreads
15. **Risk Parity**: Volatility-weighted

## Usage Examples

### Basic Backtest
```
Backtest RSI strategy on AAPL from 2023 to 2024
```

### Strategy Comparison
```
Compare RSI vs MACD strategies on SPY
```

### Parameter Optimization
```
Optimize RSI period and thresholds for best Sharpe ratio
```

### Multi-Asset
```
Backtest momentum strategy on AAPL, MSFT, GOOGL
```

## Backtesting Process

### 1. Data Preparation
- Fetch historical OHLCV data
- Handle missing data
- Adjust for splits and dividends
- Align timestamps

### 2. Strategy Definition
Define entry and exit rules:
```python
# Example RSI Strategy
Entry: RSI < 30 (oversold)
Exit: RSI > 70 (overbought)
```

### 3. Execution Simulation
- Apply strategy to historical data
- Account for slippage and commissions
- Track position sizes
- Calculate P&L

### 4. Performance Analysis
- Calculate all metrics
- Generate equity curve
- Identify drawdown periods
- Analyze trade distribution

## Performance Metrics

### Returns
- **Total Return**: Overall profit/loss %
- **Annualized Return**: Yearly equivalent
- **CAGR**: Compound annual growth rate
- **Monthly/Daily Returns**: Distribution

### Risk-Adjusted Returns
- **Sharpe Ratio**: Return per unit of volatility
  - Good: > 1.0
  - Excellent: > 2.0
- **Sortino Ratio**: Return per unit of downside risk
- **Calmar Ratio**: Return / max drawdown

### Drawdown Analysis
- **Maximum Drawdown**: Worst peak-to-trough decline
- **Average Drawdown**: Typical decline size
- **Drawdown Duration**: Time underwater
- **Recovery Time**: Time to new high

### Trade Statistics
- **Win Rate**: % profitable trades
- **Profit Factor**: Gross profit / gross loss
- **Average Win/Loss**: Trade sizing
- **Expectancy**: Average profit per trade

## Walk-Forward Optimization

Avoid overfitting with out-of-sample testing:

### Process
1. **Training Window**: Optimize on historical data
2. **Testing Window**: Test on unseen future data
3. **Roll Forward**: Move windows forward
4. **Aggregate Results**: Overall performance

### Benefits
- Realistic performance estimates
- Identify robust parameters
- Detect overfitting
- Validate strategy logic

## Monte Carlo Simulation

Test strategy robustness:
- **Random Entry**: Shuffle entry dates
- **Random Exits**: Shuffle exit dates
- **Parameter Variation**: Test parameter ranges
- **Confidence Intervals**: Expected performance range

## Optimization Techniques

### Grid Search
Test all parameter combinations:
```
Optimize RSI:
- Period: 10, 12, 14, 16, 18, 20
- Oversold: 20, 25, 30, 35
- Overbought: 65, 70, 75, 80
```

### Genetic Algorithm
Evolutionary optimization:
- Faster than grid search
- Finds local optima
- Good for many parameters

### Bayesian Optimization
Smart parameter selection:
- Learn from previous tests
- Focus on promising areas
- Fewer iterations needed

## Reporting

### HTML Reports
Interactive visualizations:
- Equity curve
- Drawdown chart
- Monthly returns heatmap
- Trade analysis
- Performance metrics table

### Export Options
- CSV: Trade log
- JSON: All metrics
- PDF: Summary report
- Excel: Detailed analysis

## API Reference

See [Backtesting Tools](../user-guide/mcp-tools.md#backtesting) for complete API documentation.

## Best Practices

### Data Quality
- Use adjusted prices
- Check for data gaps
- Validate against known events
- Handle corporate actions

### Realistic Assumptions
- Include commissions (e.g., $0.005/share)
- Add slippage (e.g., 0.05%)
- Account for market impact
- Consider liquidity

### Avoid Overfitting
- Use walk-forward analysis
- Test on multiple assets
- Validate on different time periods
- Keep strategies simple

### Risk Management
- Test position sizing
- Set stop losses
- Limit max drawdown
- Diversify across strategies
