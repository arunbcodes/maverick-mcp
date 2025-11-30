# maverick-india

Indian market support for Maverick MCP.

## Overview

`maverick-india` provides:

- **NSE/BSE Support**: National Stock Exchange and Bombay Stock Exchange
- **Indian Market Data**: Nifty 50, Sensex, sector indices
- **Conference Call Analysis**: Earnings call transcripts and AI analysis
- **RBI Data**: Economic indicators and policy rates
- **Currency Conversion**: USD/INR and other currencies
- **Circuit Breaker Tracking**: 10% circuit limits

## Installation

```bash
pip install maverick-india
```

## Quick Start

```python
from maverick_india import (
    # Market data
    get_indian_market_recommendations,
    analyze_nifty_sectors,
    get_indian_market_overview,
    
    # Conference calls
    fetch_transcript,
    summarize_transcript,
    analyze_sentiment,
)

# Get bullish recommendations
stocks = get_indian_market_recommendations(strategy="bullish", limit=10)

# Analyze earnings call
summary = summarize_transcript("RELIANCE.NS", "Q3", 2025)
```

## Market Support

### Symbol Formats

| Exchange | Suffix | Example |
|----------|--------|---------|
| NSE | `.NS` | `RELIANCE.NS`, `TCS.NS` |
| BSE | `.BO` | `RELIANCE.BO`, `TCS.BO` |

### Market Hours

| Market | Hours (IST) | Pre-market | Post-market |
|--------|-------------|------------|-------------|
| NSE | 9:15 - 15:30 | 9:00 - 9:15 | 15:40 - 16:00 |
| BSE | 9:15 - 15:30 | 9:00 - 9:15 | 15:40 - 16:00 |

### Circuit Breakers

Indian markets have 10% circuit breakers (vs 5% in US):

```python
from maverick_india.market import check_circuit_status

status = check_circuit_status("RELIANCE.NS")
print(f"Upper Circuit: {status['upper_circuit']}")
print(f"Lower Circuit: {status['lower_circuit']}")
print(f"Current: {status['current_price']}")
```

## Market Data

### Market Overview

```python
from maverick_india import get_indian_market_overview

overview = get_indian_market_overview()

print(f"Market Status: {overview['status']}")
print(f"Nifty 50: {overview['nifty_50']}")
print(f"Sensex: {overview['sensex']}")
print(f"Total NSE Stocks: {overview['nse_stocks']}")
print(f"Total BSE Stocks: {overview['bse_stocks']}")
```

### Stock Recommendations

```python
from maverick_india import get_indian_market_recommendations

# Bullish picks (adapted for 10% circuit breakers)
bullish = get_indian_market_recommendations(
    strategy="bullish",
    limit=20
)

# Other strategies
bearish = get_indian_market_recommendations(strategy="bearish")
momentum = get_indian_market_recommendations(strategy="momentum")  # Nifty 50
value = get_indian_market_recommendations(strategy="value")       # P/E < 20
dividend = get_indian_market_recommendations(strategy="dividend") # Div > 2%
smallcap = get_indian_market_recommendations(strategy="smallcap")
sector = get_indian_market_recommendations(strategy="sector_rotation")
```

### Sector Analysis

```python
from maverick_india import analyze_nifty_sectors

sectors = analyze_nifty_sectors()

for sector in sectors['rankings']:
    print(f"{sector['name']}: {sector['return_90d']:.2%}")
    print(f"  Top stocks: {', '.join(sector['top_stocks'][:3])}")
```

### Stock News

```python
from maverick_india import get_indian_stock_news

news = get_indian_stock_news("RELIANCE.NS", limit=10)

for article in news['articles']:
    print(f"[{article['sentiment']}] {article['title']}")
    print(f"  Source: {article['source']}")
```

## Economic Indicators

### RBI Policy Rates

```python
from maverick_india import get_indian_economic_indicators

indicators = get_indian_economic_indicators()

print("RBI Policy Rates:")
print(f"  Repo Rate: {indicators['repo_rate']}%")
print(f"  Reverse Repo: {indicators['reverse_repo_rate']}%")
print(f"  CRR: {indicators['crr']}%")
print(f"  SLR: {indicators['slr']}%")

print(f"\nGDP Growth: {indicators['gdp_growth']}%")
print(f"Forex Reserves: ${indicators['forex_reserves']} B")
```

### Economic Calendar

```python
events = indicators['upcoming_events']

for event in events:
    print(f"{event['date']}: {event['event']}")
```

## Currency Conversion

### Basic Conversion

```python
from maverick_india import convert_currency

# USD to INR
result = convert_currency(
    amount=1000,
    from_currency="USD",
    to_currency="INR"
)
print(f"1000 USD = {result['converted_amount']:.2f} INR")
print(f"Rate: {result['rate']}")
print(f"Source: {result['source']}")
```

### Compare Companies Across Markets

```python
from maverick_india import compare_similar_companies

comparison = compare_similar_companies(
    us_symbol="MSFT",
    indian_symbol="TCS.NS",
    currency="USD"
)

print(f"Microsoft vs TCS (in USD):")
print(f"  Market Cap: ${comparison['msft']['market_cap']:,.0f} vs ${comparison['tcs']['market_cap']:,.0f}")
print(f"  P/E Ratio: {comparison['msft']['pe_ratio']:.2f} vs {comparison['tcs']['pe_ratio']:.2f}")
print(f"  1Y Return: {comparison['msft']['return_1y']:.2%} vs {comparison['tcs']['return_1y']:.2%}")
```

### US vs India Market Comparison

```python
from maverick_india import compare_us_indian_markets

comparison = compare_us_indian_markets(period="1y")

print(f"S&P 500 vs Nifty 50 (1 Year):")
print(f"  S&P 500 Return: {comparison['sp500_return']:.2%}")
print(f"  Nifty 50 Return: {comparison['nifty_return']:.2%}")
print(f"  Correlation: {comparison['correlation']:.2f}")
print(f"  Volatility (S&P/Nifty): {comparison['sp500_vol']:.2%} / {comparison['nifty_vol']:.2%}")
```

## Conference Call Analysis

### Fetch Transcript

```python
from maverick_india.concall import fetch_transcript

transcript = fetch_transcript(
    ticker="RELIANCE.NS",
    quarter="Q3",
    fiscal_year=2025
)

print(f"Word Count: {transcript['word_count']}")
print(f"Source: {transcript['source']}")
print(f"Transcript: {transcript['transcript_text'][:500]}...")
```

### Transcript Sources

Transcripts are fetched with cascading fallback:

1. **Database Cache** (always checked first)
2. **Company IR Website** (primary)
3. **NSE Exchange Filings** (fallback 1)
4. **[Screener.in](https://www.screener.in/concalls/)** (fallback 2 - consolidated Indian transcripts)

### AI Summarization

```python
from maverick_india.concall import summarize_transcript

summary = summarize_transcript(
    ticker="RELIANCE.NS",
    quarter="Q3",
    fiscal_year=2025,
    mode="standard"  # "concise", "standard", "detailed"
)

print("Executive Summary:")
print(summary['executive_summary'])

print("\nKey Metrics:")
for metric in summary['key_metrics']:
    print(f"  - {metric}")

print("\nBusiness Highlights:")
for highlight in summary['business_highlights']:
    print(f"  - {highlight}")

print(f"\nManagement Guidance: {summary['management_guidance']}")
print(f"Sentiment: {summary['sentiment']}")
```

### Sentiment Analysis

```python
from maverick_india.concall import analyze_sentiment

sentiment = analyze_sentiment(
    ticker="RELIANCE.NS",
    quarter="Q3",
    fiscal_year=2025
)

print(f"Overall Sentiment: {sentiment['overall_sentiment']}")
print(f"Sentiment Score: {sentiment['sentiment_score']}/5")
print(f"Management Tone: {sentiment['management_tone']}")
print(f"Outlook: {sentiment['outlook_sentiment']}")
print(f"Risk Level: {sentiment['risk_sentiment']}")

print("\nPositive Signals:")
for signal in sentiment['key_positive_signals']:
    print(f"  + {signal}")

print("\nNegative Signals:")
for signal in sentiment['key_negative_signals']:
    print(f"  - {signal}")
```

### RAG Q&A

Ask questions about transcripts using RAG.

```python
from maverick_india.concall import query_transcript

answer = query_transcript(
    question="What was the revenue growth?",
    ticker="RELIANCE.NS",
    quarter="Q3",
    fiscal_year=2025,
    top_k=5
)

print(f"Answer: {answer['answer']}")

print("\nSources:")
for source in answer['sources']:
    print(f"  [{source['score']:.2f}] {source['content'][:100]}...")
```

### Compare Quarters

```python
from maverick_india.concall import compare_quarters

comparison = compare_quarters(
    ticker="RELIANCE.NS",
    quarters=[("Q1", 2025), ("Q2", 2025), ("Q3", 2025)]
)

print(f"Sentiment Trend: {comparison['sentiment_trend']}")
print(f"Score Change: {comparison['score_change']:.1f}")

for q in comparison['sentiments']:
    print(f"  {q['quarter']} {q['year']}: {q['sentiment']} ({q['score']}/5)")
```

## IR Mappings

Company IR (Investor Relations) mappings for transcript fetching.

### View Mappings

```python
from maverick_india.concall.models import CompanyIRMapping
from maverick_data import SessionLocal

with SessionLocal() as session:
    mappings = session.query(CompanyIRMapping).filter_by(is_active=True).all()
    
    for m in mappings:
        print(f"{m.ticker_symbol}: {m.ir_url}")
```

### Add Custom Mapping

```python
from maverick_india.concall.models import CompanyIRMapping

mapping = CompanyIRMapping(
    ticker_symbol="INFY.NS",
    company_name="Infosys Limited",
    market="NSE",
    country="IN",
    ir_url="https://www.infosys.com/investors/reports-filings/quarterly-results.html",
    transcript_url_pattern="/results/{year}/q{quarter}",
    transcript_css_selector="div.transcript-content",
    is_active=True
)

session.add(mapping)
session.commit()
```

### JSON Format

```json
{
  "metadata": {
    "version": "1.0",
    "source": "manual_research"
  },
  "companies": [
    {
      "ticker_symbol": "RELIANCE.NS",
      "company_name": "Reliance Industries Limited",
      "market": "NSE",
      "country": "IN",
      "ir_url": "https://www.ril.com/InvestorRelations/FinancialReporting.aspx",
      "transcript_url_pattern": null,
      "transcript_css_selector": null,
      "transcript_xpath": null,
      "is_active": true,
      "notes": "Quarterly results and transcripts available on IR page"
    }
  ]
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NSE_API_KEY` | NSE API key (optional) | None |
| `CONCALL_CACHE_TTL` | Transcript cache TTL | `86400` |

## Testing

```python
import pytest
from maverick_india import get_indian_market_recommendations

def test_indian_recommendations():
    stocks = get_indian_market_recommendations(
        strategy="bullish",
        limit=5
    )
    
    assert len(stocks) <= 5
    for stock in stocks:
        assert stock['ticker_symbol'].endswith('.NS') or stock['ticker_symbol'].endswith('.BO')
```

## API Reference

For detailed API documentation, see:

- [Market Support API](../api-reference/maverick-india/market.md)
- [Conference Call API](../api-reference/maverick-india/concall.md)

