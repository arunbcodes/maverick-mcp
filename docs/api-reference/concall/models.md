# Conference Call Models

Data models for conference call analysis.

## Module: maverick_mcp.concall.models

### Transcript

Conference call transcript model.

**Fields**:
- `id` (int): Primary key
- `ticker` (str): Stock symbol (e.g., "AAPL", "RELIANCE.NS")
- `quarter` (str): Quarter ("Q1", "Q2", "Q3", "Q4")
- `fiscal_year` (int): Fiscal year (e.g., 2025)
- `transcript_text` (Text): Full transcript content
- `source` (str): Source ("company_ir", "nse", "screener")
- `source_url` (str): Original transcript URL
- `fetched_at` (datetime): When transcript was fetched
- `metadata` (JSON): Additional data (speakers, duration, etc.)

**Indexes**:
- Composite unique index on (ticker, quarter, fiscal_year)
- Ticker index for company queries
- Fiscal year index for temporal queries

**Example**:
```python
from maverick_mcp.concall.models import Transcript
from maverick_mcp.data.session_management import session_scope

with session_scope() as session:
    transcript = session.query(Transcript).filter_by(
        ticker="RELIANCE.NS",
        quarter="Q1",
        fiscal_year=2025
    ).first()
    
    print(f"Source: {transcript.source}")
    print(f"Length: {len(transcript.transcript_text)} characters")
```

---

### TranscriptSummary

AI-generated transcript summary.

**Fields**:
- `id` (int): Primary key
- `transcript_id` (int): Foreign key to Transcript
- `summary_mode` (str): Mode ("concise", "standard", "detailed")
- `executive_summary` (Text): High-level overview
- `key_metrics` (JSON): Important financial metrics
- `revenue_analysis` (Text): Revenue discussion
- `guidance` (Text): Management guidance
- `risks` (JSON): Risk factors mentioned
- `growth_drivers` (JSON): Growth initiatives
- `generated_at` (datetime): Summary generation time
- `model_used` (str): AI model name

**Relationships**:
- `transcript`: Many-to-one with Transcript

**Example**:
```python
from maverick_mcp.concall.models import TranscriptSummary

summary = session.query(TranscriptSummary).filter_by(
    transcript_id=transcript_id,
    summary_mode="standard"
).first()

print(summary.executive_summary)
print(f"Key Metrics: {summary.key_metrics}")
```

---

### SentimentAnalysis

Sentiment analysis of conference calls.

**Fields**:
- `id` (int): Primary key
- `transcript_id` (int): Foreign key to Transcript
- `overall_sentiment` (float): Score 1-5 (1=Very Bearish, 5=Very Bullish)
- `management_tone` (str): Tone assessment ("confident", "cautious", "defensive")
- `outlook_sentiment` (float): Forward-looking sentiment (1-5)
- `risk_sentiment` (float): Risk discussion sentiment (1-5)
- `confidence_score` (float): Analysis confidence (0-1)
- `key_phrases` (JSON): Important phrases with sentiment
- `analyzed_at` (datetime): Analysis timestamp
- `model_used` (str): AI model name

**Sentiment Scale**:
- **5.0**: Very Bullish - Extremely positive outlook
- **4.0**: Bullish - Generally positive tone
- **3.0**: Neutral - Balanced perspective
- **2.0**: Bearish - Cautious or negative
- **1.0**: Very Bearish - Significantly negative

**Example**:
```python
from maverick_mcp.concall.models import SentimentAnalysis

sentiment = session.query(SentimentAnalysis).filter_by(
    transcript_id=transcript_id
).first()

print(f"Overall: {sentiment.overall_sentiment}/5")
print(f"Tone: {sentiment.management_tone}")
print(f"Confidence: {sentiment.confidence_score}")
```

---

### TranscriptEmbedding

Vector embeddings for RAG (Retrieval-Augmented Generation).

**Fields**:
- `id` (int): Primary key
- `transcript_id` (int): Foreign key to Transcript
- `chunk_index` (int): Chunk sequence number
- `chunk_text` (Text): Text segment
- `embedding` (Vector): Vector embedding
- `metadata` (JSON): Chunk metadata (speaker, topic, timestamp)
- `created_at` (datetime): Embedding creation time

**Chunk Size**: ~500-1000 tokens per chunk

**Embedding Model**: OpenAI text-embedding-3-small (1536 dimensions)

**Example**:
```python
from maverick_mcp.concall.models import TranscriptEmbedding

# Get all embeddings for a transcript
embeddings = session.query(TranscriptEmbedding).filter_by(
    transcript_id=transcript_id
).order_by(TranscriptEmbedding.chunk_index).all()

print(f"Total chunks: {len(embeddings)}")
```

---

## Data Flow

### Transcript Lifecycle

1. **Fetching**: `Transcript` created with raw text
2. **Summarization**: `TranscriptSummary` generated (concise/standard/detailed)
3. **Sentiment Analysis**: `SentimentAnalysis` computed
4. **Embedding**: `TranscriptEmbedding` chunks created for RAG
5. **Caching**: All results cached for 7 days

### Database Relationships

```
Transcript (1) ←→ (Many) TranscriptSummary
           (1) ←→ (Many) SentimentAnalysis
           (1) ←→ (Many) TranscriptEmbedding
```

---

## Best Practices

### Query Optimization

```python
from sqlalchemy.orm import joinedload

# Eager load relationships
transcript = session.query(Transcript).options(
    joinedload(Transcript.summaries),
    joinedload(Transcript.sentiment_analyses)
).filter_by(ticker="AAPL").first()

# Avoid N+1 queries
for summary in transcript.summaries:
    print(summary.executive_summary)
```

### Caching Strategy

```python
from maverick_mcp.data.cache import CacheManager

cache = CacheManager()

def get_cached_transcript(ticker: str, quarter: str, year: int):
    cache_key = f"transcript:{ticker}:{quarter}:{year}"
    
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    with session_scope() as session:
        transcript = session.query(Transcript).filter_by(
            ticker=ticker, quarter=quarter, fiscal_year=year
        ).first()
    
    cache.set(cache_key, transcript, ttl=604800)  # 7 days
    return transcript
```

### Bulk Operations

```python
# Efficient chunk insertion
chunks = [
    TranscriptEmbedding(
        transcript_id=transcript_id,
        chunk_index=i,
        chunk_text=text,
        embedding=vector
    )
    for i, (text, vector) in enumerate(chunks_data)
]

with session_scope() as session:
    session.bulk_save_objects(chunks)
```
