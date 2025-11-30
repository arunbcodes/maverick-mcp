# Providers

Cryptocurrency data providers.

## CoinGeckoProvider

Primary provider for cryptocurrency data using CoinGecko API.

::: maverick_crypto.providers.CoinGeckoProvider
    options:
      show_root_heading: true
      members:
        - get_trending
        - get_global
        - get_top_coins
        - get_coin_info
        - get_ohlc
        - get_fear_greed

### Example Usage

```python
from maverick_crypto.providers import CoinGeckoProvider

provider = CoinGeckoProvider()

# Get trending coins
trending = await provider.get_trending()

# Get global market data
global_data = await provider.get_global()

# Get top 100 coins
top_coins = await provider.get_top_coins(limit=100)

# Get Bitcoin info
btc = await provider.get_coin_info("bitcoin")

# Get OHLC data
ohlc = await provider.get_ohlc("bitcoin", days=90)

# Get Fear & Greed Index
fgi = await provider.get_fear_greed()
```

### Rate Limiting

- Free tier: 10-30 calls/minute
- With API key: Higher limits
- Circuit breaker: Auto-recovers on rate limits

## CryptoDataProvider

Fallback provider using yfinance for OHLCV data.

::: maverick_crypto.providers.CryptoDataProvider
    options:
      show_root_heading: true
      members:
        - get_stock_data
        - is_crypto_symbol
        - _normalize_symbol

### Symbol Normalization

Automatically converts various formats to yfinance format:

| Input | Output |
|-------|--------|
| `BTC` | `BTC-USD` |
| `eth` | `ETH-USD` |
| `BTCUSDT` | `BTC-USD` |
| `BTC-USD` | `BTC-USD` |

### Example Usage

```python
from maverick_crypto.providers import CryptoDataProvider

provider = CryptoDataProvider()

# Check if symbol is crypto
provider.is_crypto_symbol("BTC")  # True
provider.is_crypto_symbol("AAPL")  # False

# Get OHLCV data (auto-normalizes symbol)
data = provider.get_stock_data(
    "BTC",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

## FearGreedProvider

Fear & Greed Index from Alternative.me API.

::: maverick_crypto.providers.coingecko_provider.FearGreedProvider
    options:
      show_root_heading: true
      members:
        - get_fear_greed_index

### Index Values

| Range | Classification |
|-------|----------------|
| 0-24 | Extreme Fear |
| 25-49 | Fear |
| 50 | Neutral |
| 51-74 | Greed |
| 75-100 | Extreme Greed |

### Example

```python
from maverick_crypto.providers.coingecko_provider import FearGreedProvider

provider = FearGreedProvider()
fgi = await provider.get_fear_greed_index()

print(f"Value: {fgi['value']}")  # e.g., 75
print(f"Classification: {fgi['classification']}")  # "Greed"
```

