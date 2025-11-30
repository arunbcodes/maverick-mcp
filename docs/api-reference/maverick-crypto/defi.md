# DeFi Metrics

DeFi protocol analysis using DefiLlama and GeckoTerminal.

## DefiLlamaProvider

Free DeFi metrics from DefiLlama API.

::: maverick_crypto.defi.DefiLlamaProvider
    options:
      show_root_heading: true
      members:
        - get_top_protocols
        - get_top_chains
        - get_protocol
        - get_yields
        - get_stablecoins
        - search_protocol
        - get_defi_summary

### Example Usage

```python
from maverick_crypto.defi import DefiLlamaProvider

defi = DefiLlamaProvider()

# Top protocols by TVL
protocols = await defi.get_top_protocols(limit=20)
for p in protocols[:5]:
    print(f"{p['name']}: ${p['tvl']:,.0f}")

# Top chains by TVL
chains = await defi.get_top_chains(limit=10)

# Protocol details
aave = await defi.get_protocol("aave")
print(f"AAVE TVL: ${aave['tvl']:,.0f}")

# Yield opportunities
yields = await defi.get_yields(min_apy=5.0, stablecoin_only=True)

# Stablecoin market
stables = await defi.get_stablecoins()

# Search
results = await defi.search_protocol("uniswap")
```

### Metrics Explained

| Metric | Description |
|--------|-------------|
| **TVL** | Total Value Locked - assets deposited in protocol |
| **APY** | Annual Percentage Yield - yearly return |
| **TVL Change** | 24h/7d TVL change percentage |
| **Chain** | Blockchain where protocol operates |

### Top DeFi Categories

| Category | Examples |
|----------|----------|
| Liquid Staking | Lido, Rocket Pool |
| Lending | AAVE, Compound |
| DEX | Uniswap, Curve |
| CDP | Maker, Liquity |
| Bridge | Across, Stargate |
| Restaking | EigenLayer |

## OnChainProvider

On-chain DEX pool data from GeckoTerminal.

::: maverick_crypto.defi.OnChainProvider
    options:
      show_root_heading: true
      members:
        - get_trending_pools
        - get_new_pools
        - search_pools
        - get_token_price
        - get_networks
        - get_dexes

!!! warning "API Key Required"
    GeckoTerminal endpoints now require a CoinGecko API key.

### Example Usage

```python
from maverick_crypto.defi import OnChainProvider

onchain = OnChainProvider(api_key="your-coingecko-api-key")

# Trending pools (high volume)
trending = await onchain.get_trending_pools(network="eth")

# New pools (recent launches)
new_pools = await onchain.get_new_pools(network="solana")

# Search pools by token
pepe_pools = await onchain.search_pools("PEPE")

# Token price from DEX
price = await onchain.get_token_price(
    network="eth",
    address="0x..."
)

# Available networks
networks = await onchain.get_networks()

# DEXes on a network
dexes = await onchain.get_dexes(network="eth")
```

### Supported Networks

| Network | ID |
|---------|-----|
| Ethereum | `eth` |
| Solana | `solana` |
| Arbitrum | `arbitrum` |
| Base | `base` |
| BNB Chain | `bsc` |
| Polygon | `polygon_pos` |

### Pool Data Structure

```python
{
    "address": "0x...",
    "name": "WETH/USDC",
    "dex": "Uniswap V3",
    "price_usd": 2500.50,
    "volume_24h": 1500000,
    "liquidity": 5000000,
    "price_change_24h": 2.5,
    "created_at": "2024-01-15T..."
}
```

## MCP Tools Reference

### DefiLlama Tools

| Tool | Description |
|------|-------------|
| `defi_top_protocols` | Top DeFi protocols by TVL |
| `defi_top_chains` | Top chains by TVL |
| `defi_protocol_info` | Detailed protocol data |
| `defi_yields` | Best yield opportunities |
| `defi_stablecoins` | Stablecoin market data |
| `defi_summary` | Market overview |

### GeckoTerminal Tools

| Tool | Description |
|------|-------------|
| `onchain_trending_pools` | Hot DEX pools |
| `onchain_new_pools` | Recently created pools |
| `onchain_search_pools` | Search by token |

## Example Queries

### Protocol Analysis

```
User: "What's the TVL of AAVE?"

→ Maverick returns:
  - AAVE TVL: $12.5B
  - 24h Change: +2.3%
  - Chains: Ethereum, Polygon, Arbitrum
```

### Yield Farming

```
User: "Best stablecoin yields?"

→ Returns top yields:
  - USDC/USDT on Curve: 5.2% APY
  - DAI on Spark: 5.0% APY
  - USDC on Aave: 4.5% APY
```

### Chain Comparison

```
User: "Compare Ethereum vs Solana TVL"

→ Returns:
  - Ethereum: $50B (60% market share)
  - Solana: $8B (10% market share)
```

### New Token Discovery

```
User: "Show me new pools on Solana"

→ Returns recently created pools with:
  - Token name
  - Liquidity
  - Volume
  - Age
```

## Risk Considerations

!!! danger "Smart Contract Risk"
    DeFi protocols carry smart contract risks. TVL and APY data does not indicate safety.

### Due Diligence

- Check protocol audit history
- Review TVL history for stability
- Understand impermanent loss for LP positions
- Verify contract addresses
- Consider protocol age and track record

### Yield Warnings

| APY Range | Risk Level |
|-----------|------------|
| 0-5% | Low (stablecoins, major protocols) |
| 5-20% | Medium (blue-chip DeFi) |
| 20-100% | High (new protocols, volatile assets) |
| 100%+ | Very High (likely unsustainable) |

