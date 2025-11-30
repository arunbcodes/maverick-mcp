# maverick-crypto

Cryptocurrency data, analysis, and trading tools for Maverick MCP.

## Overview

`maverick-crypto` is a standalone package that adds comprehensive cryptocurrency support to Maverick MCP. It provides:

- **Data Providers**: CoinGecko API integration with yfinance fallback
- **24/7 Market Support**: Crypto markets never close
- **Technical Analysis**: All TA indicators work with crypto data
- **Backtesting**: 6 crypto-specific strategies using VectorBT
- **Portfolio Optimization**: Mixed stock/crypto portfolio support
- **DeFi Metrics**: DefiLlama and GeckoTerminal integration
- **News & Sentiment**: Crypto news aggregation with sentiment analysis

## Installation

```bash
# Install from workspace
pip install ./packages/crypto

# Or with all dependencies
pip install ./packages/crypto[all]
```

## Features

### Data Providers

#### CoinGecko Provider (Primary)

```python
from maverick_crypto.providers import CoinGeckoProvider

# Initialize (no API key required for basic use)
provider = CoinGeckoProvider()

# Get trending coins
trending = await provider.get_trending()

# Get global market data
global_data = await provider.get_global()

# Get top 100 coins by market cap
top_coins = await provider.get_top_coins(limit=100)

# Get OHLC data
ohlc = await provider.get_ohlc("bitcoin", days=90)
```

**Rate Limits**: Free tier allows 10-30 calls/minute.

#### yfinance Provider (Fallback)

```python
from maverick_crypto.providers import CryptoDataProvider

provider = CryptoDataProvider()

# Symbols are auto-normalized: BTC → BTC-USD
data = provider.get_stock_data("BTC", start_date="2024-01-01")
```

### 24/7 Market Support

```python
from maverick_crypto.calendar import CryptoCalendarService

calendar = CryptoCalendarService()

# Always returns True for crypto
calendar.is_market_open("BTC")  # True (24/7)

# Returns all days in range
trading_days = calendar.get_trading_days("2024-01-01", "2024-01-31")
```

### Backtesting

6 crypto-optimized strategies with adjusted parameters for higher volatility:

| Strategy | Description | Default Params |
|----------|-------------|----------------|
| `momentum` | Multi-timeframe momentum | lookback=20, threshold=0.02 |
| `mean_reversion` | Statistical mean reversion | period=20, z_threshold=2.0 |
| `breakout` | Volatility breakout | period=20, factor=2.0 |
| `rsi` | RSI oversold/overbought | period=14, oversold=25, overbought=75 |
| `macd` | MACD crossover | fast=12, slow=26, signal=9 |
| `bollinger` | Bollinger Bands mean reversion | period=20, std=2.5 |

```python
from maverick_crypto.backtesting import CryptoBacktestEngine

engine = CryptoBacktestEngine()

# Run backtest
results = await engine.run_backtest(
    symbol="BTC-USD",
    strategy="momentum",
    start_date="2023-01-01",
    initial_capital=10000,
)

print(f"Total Return: {results['total_return']}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']}")
```

### Portfolio Optimization

Mixed stock + crypto portfolio support:

```python
from maverick_crypto.portfolio import (
    MixedPortfolioService,
    CorrelationAnalyzer,
    PortfolioOptimizer,
)

# Create mixed portfolio
portfolio = MixedPortfolioService()
portfolio.add_asset("AAPL", asset_type="stock")
portfolio.add_asset("BTC", asset_type="crypto")
portfolio.add_asset("ETH", asset_type="crypto")

# Analyze correlation
analyzer = CorrelationAnalyzer()
correlation = analyzer.calculate_correlation_matrix(portfolio)

# Optimize allocation
optimizer = PortfolioOptimizer()
weights = optimizer.optimize(
    portfolio,
    objective="max_sharpe",  # or "min_volatility", "max_return"
)
```

### DeFi Metrics

#### DefiLlama (TVL, Yields)

```python
from maverick_crypto.defi import DefiLlamaProvider

defi = DefiLlamaProvider()

# Top protocols by TVL
protocols = await defi.get_top_protocols(limit=20)

# Top chains by TVL
chains = await defi.get_top_chains(limit=10)

# Yield opportunities
yields = await defi.get_yields(min_apy=5.0, stablecoin_only=True)

# Stablecoin market data
stables = await defi.get_stablecoins()
```

#### GeckoTerminal (DEX Pools)

```python
from maverick_crypto.defi import OnChainProvider

onchain = OnChainProvider(api_key="your-coingecko-api-key")

# Trending pools
trending = await onchain.get_trending_pools(network="eth")

# New pools
new_pools = await onchain.get_new_pools(network="solana")

# Search pools
results = await onchain.search_pools("PEPE")
```

!!! note "API Key Required"
    GeckoTerminal endpoints now require a CoinGecko API key as of late 2024.

### News & Sentiment

```python
from maverick_crypto.news import (
    NewsAggregator,
    CryptoSentimentAnalyzer,
)

# Fetch news
aggregator = NewsAggregator()
news = await aggregator.get_all_news(currencies=["BTC", "ETH"])

# Analyze sentiment
analyzer = CryptoSentimentAnalyzer()
result = analyzer.analyze("Bitcoin surges past $100k")
print(f"Sentiment: {result.score.label}")  # "very bullish"

# Market sentiment summary
summary = await aggregator.get_news_summary(currencies=["BTC"])
print(f"Overall: {summary['overall_sentiment']}")
```

## MCP Tools Reference

### Data Tools (2)

| Tool | Description |
|------|-------------|
| `crypto_fetch_data` | Fetch OHLCV data for any crypto |
| `crypto_get_price` | Get current price |

### Technical Analysis (3)

| Tool | Description |
|------|-------------|
| `crypto_technical_analysis` | RSI, MACD, Bollinger Bands |
| `crypto_compare` | Compare multiple cryptos |
| `crypto_support_resistance` | Key price levels |

### CoinGecko Tools (6)

| Tool | Description |
|------|-------------|
| `crypto_trending` | Top 7 trending coins (24h) |
| `crypto_fear_greed` | Fear & Greed Index (0-100) |
| `crypto_global_data` | Global market statistics |
| `crypto_top_coins` | Top coins by market cap |
| `crypto_coin_info` | Detailed coin information |
| `crypto_ohlc` | Historical OHLC data |

### Backtesting Tools (4)

| Tool | Description |
|------|-------------|
| `crypto_backtest` | Run strategy backtest |
| `crypto_compare_strategies` | Compare all strategies |
| `crypto_list_strategies` | List available strategies |
| `crypto_optimize_strategy` | Optimize parameters |

### Portfolio Tools (5)

| Tool | Description |
|------|-------------|
| `portfolio_mixed_performance` | Stock + crypto performance |
| `portfolio_correlation` | Correlation matrix |
| `portfolio_optimize` | Mean-variance optimization |
| `portfolio_suggest` | Allocation suggestions |
| `portfolio_compare_classes` | Compare asset classes |

### DeFi Tools (9)

| Tool | Description |
|------|-------------|
| `defi_top_protocols` | Top DeFi by TVL |
| `defi_top_chains` | Top chains by TVL |
| `defi_protocol_info` | Protocol details |
| `defi_yields` | Best yield opportunities |
| `defi_stablecoins` | Stablecoin market |
| `defi_summary` | Market overview |
| `onchain_trending_pools` | Hot DEX pools |
| `onchain_new_pools` | New token launches |
| `onchain_search_pools` | Search pools |

### News Tools (6)

| Tool | Description |
|------|-------------|
| `crypto_news` | Latest crypto news |
| `crypto_news_sentiment` | Analyze news sentiment |
| `crypto_trending_news` | Hot stories |
| `crypto_analyze_headline` | Analyze single headline |
| `crypto_bullish_news` | Positive news filter |
| `crypto_bearish_news` | Negative news filter |

## Database Models

```python
from maverick_crypto.models import Crypto, CryptoPriceCache

# Crypto model (like Stock)
class Crypto(CryptoBase):
    coingecko_id: str      # "bitcoin"
    symbol: str            # "BTC"
    name: str              # "Bitcoin"
    market_cap_rank: int   # 1
    current_price: float
    market_cap: float
    
# Price cache model
class CryptoPriceCache(CryptoBase):
    crypto_id: FK[Crypto]
    date: Date
    open, high, low, close, volume: float
```

## Configuration

### Environment Variables

```bash
# CoinGecko API (optional, increases rate limits)
COINGECKO_API_KEY=your-api-key

# CryptoPanic API (for authenticated news)
CRYPTOPANIC_API_KEY=your-api-key

# Database (uses main maverick DB)
DATABASE_URL=postgresql://user:pass@localhost:5432/maverick
```

### Circuit Breaker Configuration

```python
# packages/core/src/maverick_core/resilience/circuit_breaker.py
CIRCUIT_BREAKER_CONFIGS = {
    "coingecko": CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=60,
        half_open_max_calls=2,
    ),
    "fear_greed": CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=120,
        half_open_max_calls=3,
    ),
}
```

## Examples

### Compare Bitcoin to S&P 500

```
User: "Compare Bitcoin performance to SPY over the last year"

→ Uses: portfolio_compare_classes
→ Returns: Returns, volatility, correlation analysis
```

### Optimize Mixed Portfolio

```
User: "Optimize my portfolio: 40% stocks (AAPL, MSFT), 30% crypto (BTC, ETH), 30% bonds"

→ Uses: portfolio_optimize
→ Returns: Optimal weights, expected return, Sharpe ratio
```

### Check DeFi Yields

```
User: "What are the best stablecoin yields right now?"

→ Uses: defi_yields
→ Returns: Top yield opportunities with APY, TVL, risk score
```

### Analyze Crypto News

```
User: "Is the news bullish or bearish for Ethereum?"

→ Uses: crypto_news_sentiment, crypto_news
→ Returns: Sentiment analysis with top headlines
```

## Architecture

```
maverick-crypto/
├── models/           # SQLAlchemy models
│   ├── crypto.py     # Crypto entity
│   └── price_cache.py
├── providers/        # Data providers
│   ├── crypto_provider.py    # yfinance
│   └── coingecko_provider.py # CoinGecko API
├── calendar/         # 24/7 market handling
│   └── service.py
├── backtesting/      # VectorBT integration
│   ├── strategies.py # 6 strategies
│   └── engine.py
├── portfolio/        # Portfolio optimization
│   ├── mixed_portfolio.py
│   ├── correlation.py
│   └── optimizer.py
├── defi/             # DeFi metrics
│   ├── defillama.py
│   └── onchain.py
├── news/             # News & sentiment
│   ├── providers.py
│   └── sentiment.py
└── routers/          # MCP tools
    └── crypto_router.py  # 35 tools
```

## Testing

```bash
# Run all crypto tests
pytest packages/crypto/tests/ -v

# Skip external API tests
pytest packages/crypto/tests/ -v -m "not external"

# Test coverage
pytest packages/crypto/tests/ --cov=maverick_crypto
```

## Standalone Deployment

The package is designed to be independently deployable:

```bash
# Create standalone virtualenv
python -m venv crypto-env
source crypto-env/bin/activate

# Install package
pip install ./packages/crypto

# Run as standalone service
python -m maverick_crypto.server
```

## Related Packages

- **[maverick-core](maverick-core.md)**: Shared configuration, logging, exceptions
- **[maverick-data](maverick-data.md)**: Stock data providers (yfinance, Tiingo)
- **[maverick-backtest](maverick-backtest.md)**: Stock backtesting strategies
- **[maverick-server](maverick-server.md)**: MCP server integration

