# maverick-india: Conference Calls

AI-powered conference call analysis for Indian companies.

## Overview

Analyze earnings call transcripts with:
- Transcript fetching with multi-source fallback:
  - Company IR pages (primary)
  - NSE exchange filings (fallback 1)
  - [Screener.in](https://www.screener.in/concalls/) (fallback 2)
- AI-powered summarization
- Sentiment analysis
- RAG-based Q&A

---

## Fetching Transcripts

```python
from maverick_india.concall import TranscriptFetcher

fetcher = TranscriptFetcher()

# Fetch transcript
transcript = fetcher.fetch_transcript(
    ticker="RELIANCE.NS",
    quarter="Q1",
    fiscal_year=2025
)

print(f"Word count: {transcript['word_count']}")
print(f"Source: {transcript['source']}")
```

### Supported Companies

See [IR Mappings Guide](../../concall/ir-mappings-guide.md) for:
- Supported companies
- How to add new companies
- Selector configuration

---

## AI Summarization

```python
from maverick_india.concall import ConcallSummarizer

summarizer = ConcallSummarizer()

summary = summarizer.summarize(
    ticker="RELIANCE.NS",
    quarter="Q1",
    fiscal_year=2025,
    mode="standard"  # concise, standard, detailed
)

print(f"Executive Summary: {summary['executive_summary']}")
print(f"Key Metrics: {summary['key_metrics']}")
print(f"Guidance: {summary['management_guidance']}")
```

### Summary Structure

```python
{
    "executive_summary": "...",
    "key_metrics": {
        "revenue_growth": "12%",
        "margin": "18.5%",
        ...
    },
    "business_highlights": [...],
    "management_guidance": "...",
    "sentiment": "positive",
    "key_risks": [...],
    "opportunities": [...],
    "qa_insights": [...],
    "analyst_focus": [...]
}
```

---

## Sentiment Analysis

```python
from maverick_india.concall import SentimentAnalyzer

analyzer = SentimentAnalyzer()

sentiment = analyzer.analyze(
    ticker="TCS.NS",
    quarter="Q4",
    fiscal_year=2024
)

print(f"Overall: {sentiment['overall_sentiment']}")
print(f"Score: {sentiment['sentiment_score']}/5")
print(f"Confidence: {sentiment['confidence_score']:.0%}")
print(f"Management Tone: {sentiment['management_tone']}")
```

### Sentiment Levels

| Sentiment | Score | Description |
|-----------|-------|-------------|
| very_bullish | 5 | Extremely positive outlook |
| bullish | 4 | Positive indicators |
| neutral | 3 | Balanced view |
| bearish | 2 | Some concerns |
| very_bearish | 1 | Significant concerns |

---

## RAG Q&A

Ask questions about transcripts:

```python
from maverick_india.concall import ConcallRAGEngine

rag = ConcallRAGEngine()

answer = rag.query(
    question="What was the revenue growth?",
    ticker="RELIANCE.NS",
    quarter="Q1",
    fiscal_year=2025,
    top_k=5  # Number of relevant chunks
)

print(f"Answer: {answer['answer']}")
print(f"Sources: {len(answer['sources'])}")
for source in answer['sources']:
    print(f"  - {source['content'][:100]}...")
```

---

## Quarter Comparison

Compare sentiment across quarters:

```python
from maverick_india.concall import compare_quarters

result = compare_quarters(
    ticker="RELIANCE.NS",
    quarters=[("Q4", 2024), ("Q1", 2025)]
)

print(f"Trend: {result['sentiment_trend']}")  # improving, declining, stable
print(f"Score Change: {result['score_change']}")
```

---

## MCP Tools

Available through Claude Desktop:

```
"Summarize the Q1 2025 earnings call for Reliance"
"What's the sentiment from TCS's latest earnings call?"
"What did Infosys management say about margins?"
"Compare HDFC Bank sentiment across last 3 quarters"
```

---

## Database Storage

Transcripts and analysis are cached:

```python
from maverick_india.concall.models import (
    ConferenceCall,
    TranscriptSummary,
    TranscriptSentiment
)

# Query stored transcripts
session.query(ConferenceCall).filter_by(
    ticker="RELIANCE.NS",
    quarter="Q1",
    fiscal_year=2025
).first()
```

---

## Adding New Companies

See [IR Mappings Guide](../../concall/ir-mappings-guide.md) for detailed instructions.

Quick example:

```json
{
    "ticker": "NEWCOMPANY.NS",
    "company_name": "New Company Ltd.",
    "ir_base_url": "https://company.com/investors/",
    "concall_url_pattern": "https://company.com/investors/results",
    "concall_section_xpath": "//a[contains(text(), 'transcript')]",
    "market": "NSE",
    "country": "IN",
    "is_active": true
}
```

