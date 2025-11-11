# MCP Tools Reference

Complete reference for all 40+ MCP tools available in Maverick MCP.

## Tool Categories

- [Stock Data](#stock-data) - Price quotes and historical data
- [Technical Analysis](#technical-analysis) - Indicators and patterns
- [Stock Screening](#stock-screening) - Pre-calculated screening strategies
- [Portfolio](#portfolio) - Portfolio optimization and analysis
- [Market Data](#market-data) - Market overview and indices
- [Research](#research) - AI-powered research and sentiment
- [Backtesting](#backtesting) - Strategy testing and optimization
- [Conference Calls](#conference-calls) - Earnings call analysis

---

## Stock Data

### get_stock_data
Fetch historical OHLCV data for a stock.

**Parameters**:
- `ticker` (string, required): Stock symbol (e.g., "AAPL", "RELIANCE.NS")
- `start_date` (string, optional): Start date (YYYY-MM-DD)
- `end_date` (string, optional): End date (YYYY-MM-DD)
- `period` (string, optional): Quick period ("1d", "5d", "1mo", "3mo", "6mo", "1y", "5y")

**Returns**: DataFrame with Date, Open, High, Low, Close, Volume

**Example**:
```
Get AAPL stock data from 2024-01-01 to 2024-12-31
```

### get_stock_info
Get current price and company information.

**Parameters**:
- `ticker` (string, required): Stock symbol

**Returns**: Dict with price, market_cap, pe_ratio, sector, industry, description

**Example**:
```
Get current info for RELIANCE.NS
```

### get_multiple_stocks_data
Fetch data for multiple stocks efficiently.

**Parameters**:
- `tickers` (list, required): List of stock symbols
- `start_date` (string, optional): Start date
- `end_date` (string, optional): End date

**Returns**: Dict of DataFrames keyed by ticker

**Example**:
```
Get data for AAPL, MSFT, GOOGL from Jan 2024
```

---

## Technical Analysis

### calculate_sma
Calculate Simple Moving Average.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `period` (int, optional): SMA period (default: 20)
- `lookback_days` (int, optional): Historical data range (default: 365)

**Returns**: DataFrame with Date, Close, SMA

**Example**:
```
Calculate 50-day SMA for AAPL
```

### calculate_ema
Calculate Exponential Moving Average.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `period` (int, optional): EMA period (default: 20)
- `lookback_days` (int, optional): Historical data range (default: 365)

**Returns**: DataFrame with Date, Close, EMA

**Example**:
```
Calculate 12-day EMA for TCS.NS
```

### calculate_rsi
Calculate Relative Strength Index.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `period` (int, optional): RSI period (default: 14)
- `lookback_days` (int, optional): Historical data range (default: 365)

**Returns**: DataFrame with Date, Close, RSI

**Interpretation**:
- RSI > 70: Overbought
- RSI < 30: Oversold

**Example**:
```
Calculate RSI for INFY.NS
```

### calculate_macd
Calculate MACD indicator.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `fast_period` (int, optional): Fast EMA period (default: 12)
- `slow_period` (int, optional): Slow EMA period (default: 26)
- `signal_period` (int, optional): Signal line period (default: 9)
- `lookback_days` (int, optional): Historical data range (default: 365)

**Returns**: DataFrame with Date, Close, MACD, Signal, Histogram

**Signals**:
- MACD crosses above Signal: Bullish
- MACD crosses below Signal: Bearish

**Example**:
```
Calculate MACD for MSFT
```

### calculate_bollinger_bands
Calculate Bollinger Bands.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `period` (int, optional): MA period (default: 20)
- `std_dev` (float, optional): Standard deviations (default: 2)
- `lookback_days` (int, optional): Historical data range (default: 365)

**Returns**: DataFrame with Date, Close, Upper_Band, Middle_Band, Lower_Band

**Signals**:
- Price touches upper band: Overbought
- Price touches lower band: Oversold

**Example**:
```
Calculate Bollinger Bands for RELIANCE.NS
```

### get_full_technical_analysis
Get comprehensive technical analysis.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `lookback_days` (int, optional): Historical data range (default: 365)

**Returns**: Dict with all indicators, support/resistance, signals

**Includes**:
- SMA (20, 50, 200)
- EMA (12, 26)
- RSI (14)
- MACD
- Bollinger Bands
- Support/Resistance levels
- Trend direction
- Buy/Sell signals

**Example**:
```
Get full technical analysis for AAPL
```

---

## Stock Screening

### get_maverick_recommendations
Get Maverick bullish momentum stocks.

**Parameters**:
- `limit` (int, optional): Max results (default: 10)
- `min_score` (float, optional): Minimum score 0-100 (default: 70)

**Returns**: List of stocks with scores and signals

**Criteria**:
- RSI 50-70 (strong momentum)
- MACD bullish
- Price above 20 SMA
- Volume above average

**Example**:
```
Show me top 5 Maverick bullish stocks
```

### get_maverick_bear_recommendations
Get Maverick bearish stocks to avoid.

**Parameters**:
- `limit` (int, optional): Max results (default: 10)
- `min_score` (float, optional): Minimum score 0-100 (default: 70)

**Returns**: List of stocks with weakness scores

**Criteria**:
- RSI 30-50 (weak momentum)
- MACD bearish
- Price below 20 SMA
- Volume declining

**Example**:
```
Show me bearish stocks to avoid
```

### get_trending_breakout_recommendations
Get supply/demand breakout candidates.

**Parameters**:
- `limit` (int, optional): Max results (default: 10)
- `min_score` (float, optional): Minimum score 0-100 (default: 75)

**Returns**: List of breakout candidates

**Criteria**:
- Price above all major MAs
- Volume surge
- Near 52-week high
- Strong relative strength

**Example**:
```
Find breakout candidates
```

---

## Portfolio

### optimize_portfolio
Optimize portfolio weights using Modern Portfolio Theory.

**Parameters**:
- `tickers` (list, required): List of stock symbols
- `target_return` (float, optional): Target annual return
- `risk_free_rate` (float, optional): Risk-free rate (default: 0.03)
- `lookback_days` (int, optional): Historical data range (default: 365)

**Returns**: Dict with optimal_weights, expected_return, volatility, sharpe_ratio

**Example**:
```
Optimize portfolio for AAPL, MSFT, GOOGL, AMZN
```

### analyze_portfolio_risk
Analyze portfolio risk metrics.

**Parameters**:
- `holdings` (dict, required): {ticker: shares} pairs
- `purchase_prices` (dict, optional): {ticker: price} pairs
- `lookback_days` (int, optional): Historical data range (default: 365)

**Returns**: Dict with volatility, var, cvar, max_drawdown, beta, alpha

**Example**:
```
Analyze risk for portfolio: AAPL 10 shares, MSFT 5 shares
```

### calculate_correlation_matrix
Calculate asset correlations.

**Parameters**:
- `tickers` (list, required): List of stock symbols
- `lookback_days` (int, optional): Historical data range (default: 365)

**Returns**: Correlation matrix DataFrame

**Example**:
```
Calculate correlation matrix for AAPL, MSFT, GOOGL
```

---

## Market Data

### get_market_overview
Get market indices and sector performance.

**Parameters**: None

**Returns**: Dict with major_indices, sector_performance, market_breadth

**Includes**:
- S&P 500, Nasdaq, Dow Jones
- Sector leaders and laggards
- Advance/decline ratio
- New highs/lows

**Example**:
```
Get market overview
```

### get_watchlist
Get sample portfolio with real-time data.

**Parameters**: None

**Returns**: List of stocks with current prices and changes

**Example**:
```
Show watchlist
```

---

## Research

### research_comprehensive
Comprehensive AI-powered research.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `depth` (string, optional): "quick", "standard", "deep" (default: "standard")
- `include_financials` (bool, optional): Include financial analysis (default: true)

**Returns**: Dict with company_overview, financial_analysis, competitive_position, investment_thesis, risks

**Features**:
- 7-256x parallel speedup
- Multi-agent analysis
- 400+ AI models
- Cost-optimized

**Example**:
```
Research AAPL comprehensively with financials
```

### research_company
Company-specific deep research.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `focus_area` (string, optional): Specific area to focus on

**Returns**: Detailed company analysis

**Example**:
```
Research TCS.NS focusing on IT services
```

### analyze_market_sentiment
Multi-source sentiment analysis.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `timeframe` (string, optional): "24h", "7d", "30d" (default: "7d")

**Returns**: Dict with sentiment_score, confidence, sources, trends

**Sources**:
- News articles
- Social media
- Analyst ratings
- Insider trading

**Example**:
```
Analyze sentiment for RELIANCE.NS
```

---

## Backtesting

### run_backtest
Execute backtest with specified strategy.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `strategy` (string, required): Strategy name ("rsi", "macd", "sma_crossover", etc.)
- `start_date` (string, required): Start date (YYYY-MM-DD)
- `end_date` (string, required): End date (YYYY-MM-DD)
- `parameters` (dict, optional): Strategy-specific parameters
- `initial_capital` (float, optional): Starting capital (default: 10000)

**Returns**: Dict with performance_metrics, trades, equity_curve

**Available Strategies**:
- rsi, macd, sma_crossover, ema_crossover
- bollinger_bands, mean_reversion
- momentum, breakout
- ml_adaptive, ensemble
- And more (15+ total)

**Example**:
```
Backtest RSI strategy on AAPL from 2023-01-01 to 2024-12-31
```

### compare_strategies
Compare multiple strategies.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `strategies` (list, required): List of strategy names
- `start_date` (string, required): Start date
- `end_date` (string, required): End date
- `initial_capital` (float, optional): Starting capital

**Returns**: Comparison DataFrame with metrics for each strategy

**Example**:
```
Compare RSI vs MACD strategies on SPY from 2023 to 2024
```

### optimize_strategy
Optimize strategy parameters.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `strategy` (string, required): Strategy name
- `start_date` (string, required): Start date
- `end_date` (string, required): End date
- `parameter_ranges` (dict, required): Ranges to test
- `metric` (string, optional): Optimization metric (default: "sharpe_ratio")

**Returns**: Dict with best_parameters, performance_metrics, optimization_results

**Example**:
```
Optimize RSI parameters for AAPL: period 10-20, oversold 20-35, overbought 65-80
```

---

## Conference Calls

### concall_fetch_transcript
Fetch earnings call transcript.

**Parameters**:
- `ticker` (string, required): Stock symbol (e.g., "RELIANCE.NS", "AAPL")
- `quarter` (string, required): Quarter ("Q1", "Q2", "Q3", "Q4")
- `fiscal_year` (int, required): Year (e.g., 2025)

**Returns**: Dict with transcript_text, source, source_url, metadata

**Sources**:
1. Company IR website (primary)
2. NSE exchange filings (fallback)

**Example**:
```
Fetch RELIANCE.NS Q1 2025 earnings call transcript
```

### concall_summarize_transcript
Generate AI-powered summary.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `quarter` (string, required): Quarter
- `fiscal_year` (int, required): Year
- `mode` (string, optional): "concise", "standard", "detailed" (default: "standard")

**Returns**: Dict with executive_summary, key_metrics, revenue_analysis, guidance, risks, growth_drivers

**Detail Levels**:
- **Concise**: 2-3 paragraphs (~30 sec read)
- **Standard**: 1-2 pages (~3 min read)
- **Detailed**: 3-5 pages (~10 min read)

**Example**:
```
Summarize AAPL Q4 2024 earnings call in detailed mode
```

### concall_analyze_sentiment
Analyze sentiment and tone.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `quarter` (string, required): Quarter
- `fiscal_year` (int, required): Year

**Returns**: Dict with overall_sentiment (1-5), management_tone, outlook_sentiment, risk_sentiment, confidence_score

**Sentiment Scale**:
- 5: Very Bullish
- 4: Bullish
- 3: Neutral
- 2: Bearish
- 1: Very Bearish

**Example**:
```
Analyze sentiment for TCS.NS Q2 2025 earnings call
```

### concall_query_transcript
Ask questions using RAG.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `quarter` (string, required): Quarter
- `fiscal_year` (int, required): Year
- `query` (string, required): Your question

**Returns**: Dict with answer, sources (with citations), confidence

**Example**:
```
What did INFY management say about AI initiatives in Q1 2025?
```

### concall_compare_quarters
Compare sentiment across quarters.

**Parameters**:
- `ticker` (string, required): Stock symbol
- `quarters` (list, required): List of (quarter, year) tuples

**Returns**: Dict with sentiment_trends, key_changes, progression

**Example**:
```
Compare RELIANCE sentiment across Q4 2024, Q1 2025, Q2 2025
```

---

## Usage Tips

### Natural Language
All tools support natural language commands:
```
Show me technical analysis for AAPL
Get RSI for RELIANCE.NS
Optimize my portfolio with these stocks: AAPL, MSFT, GOOGL
```

### Multiple Parameters
Combine filters and options:
```
Get AAPL data from Jan 2024 to Dec 2024 with technical indicators
Screen for bullish momentum stocks with RSI between 50-70
```

### Caching
Most tools cache results automatically:
- Stock data: 1 hour
- Technical indicators: 1 hour
- Screening: 24 hours
- Research: 24 hours
- Conference calls: 7 days

### Rate Limits
Free tier limits (Tiingo):
- 500 requests/day
- 15-minute delayed quotes
- Historical data only

Upgrade for:
- Real-time data
- Unlimited requests
- Options & futures

## API Keys Required

| Tool Category | Required Keys |
|--------------|---------------|
| Stock Data | TIINGO_API_KEY |
| Technical Analysis | TIINGO_API_KEY |
| Stock Screening | None (pre-seeded) |
| Portfolio | TIINGO_API_KEY |
| Market Data | TIINGO_API_KEY |
| Research | OPENROUTER_API_KEY, EXA_API_KEY (optional) |
| Backtesting | TIINGO_API_KEY |
| Conference Calls | OPENROUTER_API_KEY, OPENAI_API_KEY (for RAG only) |

See [Configuration Guide](../getting-started/configuration.md) for setup instructions.
