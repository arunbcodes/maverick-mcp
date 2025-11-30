# Conference Call Analysis

AI-powered earnings call transcript analysis.

See [Conference Call System](../concall/overview.md) for complete documentation.

## Quick Overview

### Transcript Fetching
Automatic retrieval from multiple sources with cascading fallback:
- Company IR websites (primary)
- NSE exchange filings (fallback 1 - Indian stocks)
- [Screener.in](https://www.screener.in/concalls/) (fallback 2 - consolidated Indian transcripts)

### AI Summarization
Structured summaries with:
- Executive summary
- Key financial metrics
- Revenue and earnings analysis
- Management guidance
- Risk factors and concerns
- Growth drivers

### Sentiment Analysis
Multi-dimensional sentiment scoring:
- Overall sentiment (1-5 scale)
- Management tone (confident/cautious/defensive)
- Forward outlook sentiment
- Risk sentiment
- Confidence scoring

### RAG Q&A
Ask questions about transcripts:
- Vector search for relevant sections
- LLM-powered answers
- Source citations
- Follow-up questions supported

### Comparative Analysis
Compare across quarters:
- Sentiment trends
- Metric changes
- Guidance evolution
- Concern tracking

## Supported Companies

### US Stocks
Most major US companies with:
- Public IR websites
- Regular earnings calls
- Transcript availability

### Indian Stocks
Major NSE/BSE listed companies:
- Nifty 50 constituents
- Large-cap companies
- Midcap-150 stocks

See full list in [Supported Companies](../concall/supported-companies.md).

## Usage Examples

### Fetch Transcript
```
Fetch RELIANCE.NS Q1 2025 earnings call transcript
```

### Summarize
```
Summarize AAPL Q4 2024 earnings call in detail
```

### Analyze Sentiment
```
Analyze sentiment for TCS.NS Q2 2025 call
```

### Ask Questions
```
What did INFY management say about AI initiatives in Q1 2025?
```

### Compare Quarters
```
Compare RELIANCE sentiment across Q4 2024, Q1 2025, Q2 2025
```

## Features

### Multi-Source Fetching
Cascading fallback system:
1. Database cache (checked first)
2. Company IR website (primary)
3. NSE exchange filings (fallback 1)
4. [Screener.in](https://www.screener.in/concalls/) (fallback 2)

### AI Models
- OpenRouter for summarization
- Multiple model support
- Cost-optimized selection
- Quality-first approach

### Caching
Three-tier caching:
- L1: Redis/Memory (milliseconds)
- L2: Database (seconds)
- L3: AI generation (minutes)

Benefits:
- Instant retrieval for cached analyses
- Significant cost savings
- No redundant AI calls

## Detail Levels

### Concise
Quick overview (2-3 paragraphs):
- Key highlights only
- Major metrics
- Overall sentiment
- 30 seconds to read

### Standard (Default)
Balanced analysis (1-2 pages):
- Executive summary
- Financial performance
- Key initiatives
- Risks and concerns
- 2-3 minutes to read

### Detailed
Comprehensive analysis (3-5 pages):
- Full transcript synthesis
- Detailed metrics
- Segment-by-segment analysis
- Management quotes
- 5-10 minutes to read

## Cost & Performance

### API Costs
- Summarization: $0.01-0.05 per transcript
- Sentiment: $0.005-0.01 per transcript
- RAG embeddings: $0.0001 per transcript
- RAG queries: $0.001-0.01 per query

### Performance
- Transcript fetch: 2-10 seconds
- Summarization: 30-60 seconds
- Sentiment analysis: 10-20 seconds
- RAG setup: 20-40 seconds (one-time)
- RAG queries: 3-5 seconds

### Caching Benefits
- Cached retrieval: < 100ms
- Cost savings: 90%+ on repeat access
- No quality degradation

## API Reference

See [Conference Call MCP Tools](../concall/mcp-tools.md) for complete API documentation.

## Configuration

Required:
```ini
# For AI features
OPENROUTER_API_KEY=your-key-here

# For RAG Q&A only
OPENAI_API_KEY=your-key-here
```

Optional:
```ini
# For caching
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Learn More

- [Complete Guide](../concall/overview.md)
- [MCP Tools Reference](../concall/mcp-tools.md)
- [Supported Companies](../concall/supported-companies.md)
- [Architecture](../concall/architecture.md)
