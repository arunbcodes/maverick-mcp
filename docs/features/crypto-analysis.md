# Cryptocurrency Analysis

Maverick MCP provides comprehensive cryptocurrency analysis with 35+ MCP tools.

## Overview

The crypto module adds support for:

- **6,000+ cryptocurrencies** via CoinGecko
- **24/7 market analysis** (no market hours restrictions)
- **6 backtesting strategies** optimized for crypto volatility
- **DeFi metrics** from DefiLlama and GeckoTerminal
- **News sentiment analysis** with 130+ crypto-specific keywords

## Quick Start

### Get Current Prices

```
User: "What's the price of Bitcoin?"

→ Maverick returns:
  - Current price: $98,500
  - 24h change: +2.3%
  - Market cap: $1.9T
  - 24h volume: $45B
```

### Technical Analysis

```
User: "Analyze ETH with RSI and MACD"

→ Maverick returns:
  - RSI(14): 65 (neutral-bullish)
  - MACD: Bullish crossover
  - Trend: Uptrend
  - Support: $3,200
  - Resistance: $3,800
```

### Market Sentiment

```
User: "What's the crypto fear and greed index?"

→ Maverick returns:
  - Index: 75 (Greed)
  - Classification: Greed
  - Trend: Rising from 68 yesterday
```

## Data Sources

### CoinGecko (Primary)

- **Free tier**: 10-30 calls/minute
- **Coverage**: 6,000+ coins
- **Data**: Prices, market cap, volume, trending, OHLC
- **No API key required** for basic endpoints

### yfinance (Fallback)

- **Symbols**: BTC-USD, ETH-USD format
- **Data**: OHLCV historical data
- **Unlimited**: No rate limits

### DefiLlama

- **Free**: No API key required
- **Data**: TVL, yields, stablecoin metrics
- **Coverage**: 3,000+ DeFi protocols

## Crypto-Specific Considerations

### Higher Volatility

Crypto is 3-5x more volatile than stocks. Maverick adjusts:

| Parameter | Stocks | Crypto |
|-----------|--------|--------|
| RSI Oversold | 30 | 25 |
| RSI Overbought | 70 | 75 |
| Bollinger Bands | 2.0 std | 2.5 std |
| Stop Loss | 2-3% | 5-10% |
| Position Size | Standard | Reduced |

### 24/7 Markets

Unlike stocks, crypto never closes:

- No market hours checks needed
- No weekend gaps
- Continuous backtesting data
- Real-time analysis anytime

### No Circuit Breakers

Crypto can move 20-50% in a day:

- Wider stop losses
- Smaller position sizes
- Higher volatility parameters

## Backtesting Strategies

### 1. Momentum Strategy

Best for trending markets (bull runs).

```
User: "Backtest momentum strategy on BTC for 2024"

→ Parameters:
  - Lookback: 20 days
  - Threshold: 2% return
  
→ Results:
  - Total Return: 45%
  - Sharpe Ratio: 1.8
  - Max Drawdown: -18%
```

### 2. Mean Reversion

Best for range-bound markets.

```
User: "Test mean reversion on ETH"

→ Parameters:
  - Period: 20 days
  - Z-score threshold: 2.0
  
→ Results:
  - Total Return: 28%
  - Win Rate: 62%
```

### 3. RSI Strategy

Classic overbought/oversold signals.

```
User: "Backtest RSI strategy on SOL"

→ Parameters:
  - RSI Period: 14
  - Buy below: 25
  - Sell above: 75
```

### 4. MACD Crossover

Trend-following with confirmation.

### 5. Bollinger Bands

Mean reversion with volatility bands.

### 6. Breakout Strategy

Volatility expansion breakouts.

## Portfolio Optimization

### Mixed Stock + Crypto

```
User: "Optimize portfolio: 60% stocks, 40% crypto"

→ Maverick calculates:
  - Optimal weights
  - Expected return
  - Portfolio volatility
  - Sharpe ratio
  
→ Example output:
  Stocks (60%):
    AAPL: 25%
    MSFT: 20%
    GOOGL: 15%
  Crypto (40%):
    BTC: 25%
    ETH: 15%
```

### Correlation Analysis

```
User: "Show correlation between my stocks and crypto"

→ Maverick returns:
  - BTC-SPY correlation: 0.35
  - ETH-QQQ correlation: 0.42
  - Diversification score: 7.5/10
```

## DeFi Analysis

### Protocol TVL

```
User: "What are the top DeFi protocols by TVL?"

→ Top 5:
  1. Lido: $28B (Liquid Staking)
  2. AAVE: $12B (Lending)
  3. Uniswap: $6B (DEX)
  4. Maker: $5B (CDP)
  5. Eigenlayer: $4.5B (Restaking)
```

### Yield Opportunities

```
User: "Best stablecoin yields right now?"

→ Top yields:
  - USDC on Aave: 4.5% APY
  - USDT on Compound: 4.2% APY
  - DAI on Spark: 5.0% APY
```

### Chain Analysis

```
User: "Compare Ethereum vs Solana TVL"

→ Results:
  - Ethereum: $50B TVL (60% market share)
  - Solana: $8B TVL (10% market share)
  - Arbitrum: $3B TVL
```

## News & Sentiment

### Real-time News

```
User: "Latest Bitcoin news"

→ Returns 20 recent articles:
  - Source, title, sentiment, URL
  - Community votes (bullish/bearish)
```

### Sentiment Analysis

```
User: "Is the news bullish for crypto?"

→ Analysis:
  - Overall: Bullish
  - Breakdown:
    - Bullish articles: 12
    - Bearish articles: 4
    - Neutral: 14
  - Top keywords: "rally", "adoption", "ETF"
```

### Headline Analysis

```
User: "Analyze: SEC approves spot Ethereum ETF"

→ Result:
  - Sentiment: Very Bullish (5/5)
  - Confidence: 0.85
  - Keywords: "approved", "ETF"
```

## Example Queries

### Price & Data

- "What's Bitcoin's price?"
- "Show me ETH market data"
- "Get Solana's 90-day OHLC"
- "What are the trending cryptos?"

### Analysis

- "Analyze BTC with RSI"
- "Technical analysis of ETH"
- "Compare BTC vs ETH performance"
- "Support and resistance for SOL"

### Backtesting

- "Backtest momentum strategy on BTC"
- "Compare all strategies for ETH"
- "Optimize RSI parameters for SOL"

### Portfolio

- "Optimize my crypto portfolio"
- "Show correlation: AAPL, MSFT, BTC, ETH"
- "Compare stock vs crypto returns"

### DeFi

- "Top DeFi protocols"
- "Best yield opportunities"
- "Ethereum vs Solana TVL"

### News

- "Crypto news today"
- "Is Bitcoin news bullish?"
- "Analyze this headline: ..."

## API Keys

Most features work without API keys:

| Source | API Key | Free Limits |
|--------|---------|-------------|
| CoinGecko | Optional | 10-30/min |
| yfinance | Not needed | Unlimited |
| DefiLlama | Not needed | Unlimited |
| GeckoTerminal | **Required** | With key |
| CryptoPanic | Optional | Limited |

### Getting CoinGecko API Key

1. Go to [coingecko.com/api](https://www.coingecko.com/en/api)
2. Sign up for free Demo account
3. Get API key
4. Set: `COINGECKO_API_KEY=your-key`

## Best Practices

### Position Sizing

Due to crypto volatility:

- Limit crypto to 10-30% of total portfolio
- Use smaller position sizes (2-5% per trade)
- Set wider stop losses (5-10%)

### Diversification

- Don't put all funds in one coin
- Mix large caps (BTC, ETH) with alts
- Consider stablecoins for yield
- Balance with traditional assets

### Risk Management

- Never invest more than you can afford to lose
- Use dollar-cost averaging (DCA)
- Avoid leverage in volatile markets
- Monitor Fear & Greed Index

## Next Steps

- [Backtesting Guide](backtesting.md) - Learn strategy testing
- [Portfolio Analysis](portfolio-analysis.md) - Optimize allocations
- [maverick-crypto Package](../packages/maverick-crypto.md) - Technical details

