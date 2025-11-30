# Maverick Crypto

Cryptocurrency data and analysis package for MaverickMCP.

## Features

- **Multi-Provider Support**: yfinance (default), CoinGecko (optional)
- **24/7 Market Calendar**: Handles crypto's always-open markets
- **Technical Analysis**: RSI, MACD, Bollinger Bands via pandas-ta
- **Database Models**: SQLAlchemy models for crypto data persistence
- **MCP Integration**: Ready-to-use tools for Claude Desktop

## Installation

```bash
# Basic installation (yfinance only)
pip install -e packages/crypto

# With CoinGecko support
pip install -e "packages/crypto[coingecko]"

# Full installation with dev dependencies
pip install -e "packages/crypto[all]"
```

## Quick Start

```python
from maverick_crypto import CryptoDataProvider

# Fetch Bitcoin data
provider = CryptoDataProvider()
btc_data = await provider.get_crypto_data("BTC", days=90)
print(btc_data.tail())

# Get technical analysis
from maverick_crypto import CryptoAnalyzer
analyzer = CryptoAnalyzer()
analysis = await analyzer.get_technical_analysis("ETH")
print(analysis)
```

## Supported Symbols

Any cryptocurrency available on Yahoo Finance:
- `BTC`, `ETH`, `BNB`, `SOL`, `XRP`, `DOGE`, `ADA`, `AVAX`, `DOT`, `MATIC`
- And 100+ more via `-USD` suffix

## Architecture

```
maverick_crypto/
├── models/          # SQLAlchemy database models
├── providers/       # Data providers (yfinance, CoinGecko)
├── services/        # Business logic services
├── calendar/        # 24/7 market calendar
└── routers/         # MCP tool definitions
```

## Standalone Deployment

This package is designed for independent deployment:

```bash
# Can be moved to separate repo
git subtree split -P packages/crypto -b crypto-standalone

# Or installed independently
pip install maverick-crypto
```

## License

MIT License

