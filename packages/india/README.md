# Maverick India

Indian market-specific functionality for Maverick stock analysis.

## Overview

This package provides:

- **Market Data**: NSE and BSE stock data and screening
- **News**: Indian financial news aggregation with sentiment analysis
- **Economic**: RBI data and Indian economic indicators
- **Conference Calls**: Earnings transcript analysis

## Installation

```bash
pip install maverick-india
```

Or with uv:

```bash
uv add maverick-india
```

## Features

### Market Data
- NSE and BSE stock data with Yahoo Finance (.NS, .BO suffixes)
- 7 screening strategies adapted for Indian market
- Nifty 50 and Sensex constituent tracking
- Market-aware trading calendars (9:15 AM - 3:30 PM IST)
- 10% circuit breaker awareness

### News Aggregation
- MoneyControl, Economic Times integration
- Multi-source news with sentiment analysis
- RSS feed parsing

### Economic Indicators
- RBI policy rates (Repo, Reverse Repo, CRR, SLR)
- GDP growth, inflation, forex reserves
- Economic calendar for upcoming events

### Conference Call Analysis
- Transcript fetching from company IR websites
- AI-powered summarization
- Sentiment analysis of management tone
- RAG-based Q&A over transcripts

## Supported Exchanges

- **NSE (National Stock Exchange)**: `.NS` suffix (e.g., `RELIANCE.NS`)
- **BSE (Bombay Stock Exchange)**: `.BO` suffix (e.g., `TCS.BO`)

## Dependencies

- maverick-core: Core interfaces
- maverick-data: Data fetching
- beautifulsoup4: Web scraping
- feedparser: RSS parsing
- langchain-chroma: Vector search for RAG
