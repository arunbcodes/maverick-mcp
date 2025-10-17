# Phase 3: Indian Market Screening

Quick reference for what we're building in Phase 3.

## Goal
Adapt existing screening strategies for Indian market (NSE/BSE) with proper handling of:
- 10% circuit breakers (vs 7% in US)
- INR prices and Indian numbering (lakhs, crores)
- Nifty sector structure
- Lower volume thresholds (Indian market is smaller)

## What We're Building

### 1. Core Screening Module
`maverick_mcp/application/screening/indian_market.py`

**7 Strategies**:
1. `get_maverick_bullish_india()` - Bullish momentum (adapted thresholds)
2. `get_maverick_bearish_india()` - Bearish/short opportunities
3. `get_nifty50_momentum()` - Momentum plays in Nifty 50
4. `get_nifty_sector_rotation()` - Which sectors are hot right now
5. `get_value_picks_india()` - Value investing (P/E < 20, dividend > 2%)
6. `get_high_dividend_india()` - High yield stocks
7. `get_smallcap_breakouts_india()` - Small-cap opportunities

**Utilities**:
- `calculate_circuit_breaker_limits()` - 10% limits for Indian stocks
- `format_indian_currency()` - Format as ₹X.XX Cr or ₹X.XX L
- `get_nifty_sectors()` - List of Nifty sectors

### 2. MCP Tools
Add to `maverick_mcp/api/server.py`:
- `get_indian_market_recommendations(strategy, limit)` - Main screening tool
- `analyze_nifty_sectors()` - Sector rotation analysis
- `get_indian_market_overview()` - Market status + stats

### 3. Tests
`tests/test_indian_screening.py` - Test all strategies and utilities

## Key Differences from US Market

| Feature | US Market | Indian Market |
|---------|-----------|---------------|
| Circuit Breaker | 7% | 10% |
| Volume Threshold | 1M shares | 500K shares |
| P/E for Value | < 15 | < 20 |
| Settlement | T+2 | T+1 |
| Trading Hours | 9:30-16:00 EST | 9:15-15:30 IST |
| Currency | USD | INR (lakhs/crores) |

## Indian Market Specifics

**Nifty Sectors**:
- Banking & Financial Services
- Information Technology
- Oil & Gas
- Fast Moving Consumer Goods (FMCG)
- Automobile
- Pharmaceuticals
- Metals & Mining
- Infrastructure
- Telecom
- Power

**Market Cap Ranges** (in crores):
- Large Cap: > ₹20,000 Cr
- Mid Cap: ₹5,000 - ₹20,000 Cr
- Small Cap: ₹1,000 - ₹5,000 Cr

## Usage After Phase 3

Claude Desktop commands:
```
"Show me bullish Indian stock recommendations"
"Which Nifty sectors are performing well?"
"Find high dividend Indian stocks"
"Give me momentum plays in Nifty 50"
"Find small-cap breakouts in India"
```

## Implementation Checklist
- [ ] Create `indian_market.py` with 7 strategies
- [ ] Add 3 MCP tools to `server.py`
- [ ] Create test file `test_indian_screening.py`
- [ ] Test locally with direct Python
- [ ] Test with Claude Desktop
- [ ] Update CLAUDE.md
- [ ] Commit and push

