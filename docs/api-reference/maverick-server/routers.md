# maverick-server: Routers

MCP tool routers that expose functionality to Claude Desktop.

## Overview

Routers define MCP tools that Claude can invoke. Each router handles a specific domain.

---

## Available Routers

| Router | Tools | Description |
|--------|-------|-------------|
| `data` | Stock data, quotes | Fetch historical and real-time data |
| `screening` | Stock recommendations | Maverick bullish/bearish, breakouts |
| `technical` | Technical analysis | RSI, MACD, support/resistance |
| `portfolio` | Portfolio management | Positions, analysis, risk |
| `research` | Deep research | AI-powered financial research |
| `agents` | LangGraph agents | Multi-agent analysis |
| `concall` | Conference calls | Transcript analysis |
| `india` | Indian market | NSE/BSE, RBI data |

---

## Data Router

```python
# MCP Tools
get_stock_data(ticker, period)
get_stock_info(ticker)
get_chart_links(ticker)
get_news_sentiment(ticker, timeframe)
```

**Claude Usage:**
```
"Get AAPL stock data for the last year"
"Show me company info for Microsoft"
"What's the sentiment on Tesla stock?"
```

---

## Screening Router

```python
# MCP Tools
get_maverick_stocks(limit)
get_maverick_bear_stocks(limit)
get_supply_demand_breakouts(limit)
get_all_screening_recommendations()
get_screening_by_criteria(min_momentum_score, sector)
```

**Claude Usage:**
```
"Show me top momentum stocks"
"Find bearish stock opportunities"
"Get technology stocks with momentum score above 80"
```

---

## Technical Router

```python
# MCP Tools
get_rsi_analysis(ticker, period)
get_macd_analysis(ticker)
get_support_resistance(ticker)
get_full_technical_analysis(ticker)
get_stock_chart_analysis(ticker)
```

**Claude Usage:**
```
"What's the RSI for Apple?"
"Show MACD analysis for NVDA"
"Find support and resistance levels for TSLA"
```

---

## Portfolio Router

```python
# MCP Tools
add_position(ticker, shares, purchase_price)
get_my_portfolio()
remove_position(ticker, shares)
risk_adjusted_analysis(ticker, risk_level)
compare_tickers(tickers)
portfolio_correlation_analysis()
```

**Claude Usage:**
```
"Add 10 shares of AAPL at $180"
"Show my portfolio performance"
"Analyze risk for Microsoft at moderate level"
```

---

## Research Router

```python
# MCP Tools
comprehensive_research(query, persona, scope)
company_comprehensive(symbol)
analyze_market_sentiment(topic, timeframe)
```

**Claude Usage:**
```
"Research Apple's competitive position"
"What's the market sentiment on AI stocks?"
"Deep dive into Tesla's financials"
```

---

## Agents Router

LangGraph-powered multi-agent analysis:

```python
# MCP Tools
analyze_market_with_agent(query, persona)
orchestrated_analysis(query, routing_strategy)
deep_research_financial(topic, focus_areas)
compare_personas_analysis(query)
```

**Personas:**
- `conservative`: Lower risk tolerance
- `moderate`: Balanced approach
- `aggressive`: Higher risk tolerance
- `day_trader`: Short-term focus

**Claude Usage:**
```
"Analyze tech stocks with conservative persona"
"Compare analysis across all investor types"
"Research NVIDIA with focus on fundamentals"
```

---

## India Router

```python
# MCP Tools
get_indian_market_recommendations(strategy)
analyze_nifty_sectors()
get_indian_market_overview()
get_indian_economic_indicators()
get_indian_stock_news(symbol)
compare_us_indian_markets(period)
convert_currency(amount, from_currency, to_currency)
```

**Claude Usage:**
```
"Show bullish Indian stocks"
"What are RBI policy rates?"
"Compare S&P 500 with Nifty 50"
"Convert 100000 INR to USD"
```

---

## Concall Router

```python
# MCP Tools
fetch_transcript(ticker, quarter, fiscal_year)
summarize_transcript(ticker, quarter, fiscal_year, mode)
analyze_sentiment(ticker, quarter, fiscal_year)
query_transcript(question, ticker, quarter, fiscal_year)
compare_quarters(ticker, quarters)
```

**Claude Usage:**
```
"Summarize Reliance Q1 2025 earnings call"
"What's the sentiment from TCS earnings?"
"What did management say about margins?"
```

---

## Creating Custom Routers

```python
from fastmcp import FastMCP

mcp = FastMCP("my-router")

@mcp.tool()
def my_custom_tool(param: str) -> dict:
    """Description shown to Claude."""
    return {"result": process(param)}

# Register with server
def register_my_tools(mcp: FastMCP):
    # Tool definitions
    pass
```

---

## Tool Registration

All tools are registered at server startup:

```python
from maverick_server.routers import register_all_tools

# In server initialization
register_all_tools(mcp)
```

