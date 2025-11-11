# Conference Call Services

Business logic and AI services for conference call analysis.

## Module: maverick_mcp.concall.services.transcript_service

### TranscriptService

Core service for transcript management.

**Class**: `TranscriptService`

**Methods**:

#### get_transcript()

Get or fetch transcript.

**Signature**:
```python
def get_transcript(
    self,
    ticker: str,
    quarter: str,
    fiscal_year: int,
    force_refresh: bool = False
) -> dict
```

**Parameters**:
- `ticker` (str): Stock symbol
- `quarter` (str): Quarter ("Q1", "Q2", "Q3", "Q4")
- `fiscal_year` (int): Fiscal year
- `force_refresh` (bool, optional): Bypass cache. Default: False

**Returns**:
- dict: Transcript data with metadata

**Cache Behavior**:
- Checks database first (7-day TTL)
- Falls back to providers if not cached
- Stores result in database and Redis

**Example**:
```python
from maverick_mcp.concall.services.transcript_service import TranscriptService

service = TranscriptService()

# Get cached or fetch
transcript = service.get_transcript("AAPL", "Q4", 2024)
print(transcript['transcript_text'][:500])

# Force refresh
transcript = service.get_transcript("AAPL", "Q4", 2024, force_refresh=True)
```

---

#### save_transcript()

Save transcript to database.

**Signature**:
```python
def save_transcript(
    self,
    ticker: str,
    quarter: str,
    fiscal_year: int,
    transcript_text: str,
    source: str,
    source_url: str,
    metadata: dict | None = None
) -> int
```

**Parameters**:
- `ticker` (str): Stock symbol
- `quarter` (str): Quarter
- `fiscal_year` (int): Year
- `transcript_text` (str): Full transcript
- `source` (str): Source identifier
- `source_url` (str): Original URL
- `metadata` (dict, optional): Additional data

**Returns**:
- int: Transcript ID

---

## Module: maverick_mcp.concall.services.summarization_service

### SummarizationService

AI-powered transcript summarization.

**Class**: `SummarizationService`

**Methods**:

#### summarize()

Generate AI summary of transcript.

**Signature**:
```python
def summarize(
    self,
    transcript_id: int,
    mode: str = "standard",
    force_regenerate: bool = False
) -> dict
```

**Parameters**:
- `transcript_id` (int): Transcript database ID
- `mode` (str, optional): Detail level ("concise", "standard", "detailed"). Default: "standard"
- `force_regenerate` (bool, optional): Regenerate if exists. Default: False

**Returns**:
- dict: Summary with structure:
  - `executive_summary` (str): High-level overview
  - `key_metrics` (dict): Important financial metrics
  - `revenue_analysis` (str): Revenue discussion
  - `guidance` (str): Management guidance
  - `risks` (list): Risk factors
  - `growth_drivers` (list): Growth initiatives
  - `model_used` (str): AI model name

**Detail Levels**:

#### Concise Mode
- **Length**: 2-3 paragraphs (~200-300 words)
- **Read Time**: ~30 seconds
- **Use Case**: Quick overview before meeting
- **Content**: Key highlights, major metrics, overall tone

#### Standard Mode (Default)
- **Length**: 1-2 pages (~500-800 words)
- **Read Time**: 2-3 minutes
- **Use Case**: General analysis and research
- **Content**: Executive summary, financial performance, key initiatives, risks

#### Detailed Mode
- **Length**: 3-5 pages (~1500-2500 words)
- **Read Time**: 5-10 minutes
- **Use Case**: Deep analysis and investment decisions
- **Content**: Comprehensive analysis, segment details, management quotes, detailed metrics

**Example**:
```python
from maverick_mcp.concall.services.summarization_service import SummarizationService

service = SummarizationService()

# Standard summary
summary = service.summarize(transcript_id=123, mode="standard")
print(summary['executive_summary'])
print(f"Key Metrics: {summary['key_metrics']}")

# Detailed analysis
detailed = service.summarize(transcript_id=123, mode="detailed")
print(detailed['revenue_analysis'])
```

---

#### get_cached_summary()

Retrieve cached summary if available.

**Signature**:
```python
def get_cached_summary(
    self,
    transcript_id: int,
    mode: str = "standard"
) -> dict | None
```

**Returns**:
- dict | None: Cached summary or None

---

## Module: maverick_mcp.concall.services.sentiment_service

### SentimentService

AI-powered sentiment analysis.

**Class**: `SentimentService`

**Methods**:

#### analyze_sentiment()

Analyze sentiment of conference call.

**Signature**:
```python
def analyze_sentiment(
    self,
    transcript_id: int,
    force_regenerate: bool = False
) -> dict
```

**Parameters**:
- `transcript_id` (int): Transcript database ID
- `force_regenerate` (bool, optional): Regenerate if exists. Default: False

**Returns**:
- dict: Sentiment analysis with:
  - `overall_sentiment` (float): Score 1-5
  - `management_tone` (str): Tone assessment
  - `outlook_sentiment` (float): Forward-looking score
  - `risk_sentiment` (float): Risk discussion score
  - `confidence_score` (float): Analysis confidence 0-1
  - `key_phrases` (list): Important phrases with sentiment
  - `model_used` (str): AI model name

**Sentiment Dimensions**:

#### Overall Sentiment (1-5)
- **5.0**: Very Bullish - Extremely positive, strong confidence
- **4.0**: Bullish - Generally positive, optimistic outlook
- **3.0**: Neutral - Balanced, no clear direction
- **2.0**: Bearish - Cautious, concerns raised
- **1.0**: Very Bearish - Significantly negative, defensive

#### Management Tone
- **Confident**: Strong, assertive, optimistic
- **Cautious**: Measured, careful, hedging
- **Defensive**: Explaining issues, justifying decisions
- **Mixed**: Varying tones throughout

#### Outlook Sentiment
Future-focused sentiment:
- Growth expectations
- Guidance confidence
- Market opportunity optimism

#### Risk Sentiment
How risks are discussed:
- High (5): Risks mentioned but manageable
- Low (1): Significant concerns, uncertainty

**Example**:
```python
from maverick_mcp.concall.services.sentiment_service import SentimentService

service = SentimentService()

sentiment = service.analyze_sentiment(transcript_id=123)

print(f"Overall: {sentiment['overall_sentiment']}/5")
print(f"Management Tone: {sentiment['management_tone']}")
print(f"Outlook: {sentiment['outlook_sentiment']}/5")
print(f"Confidence: {sentiment['confidence_score']}")

# Interpret overall sentiment
if sentiment['overall_sentiment'] >= 4.0:
    print("Strong bullish sentiment")
elif sentiment['overall_sentiment'] >= 3.5:
    print("Moderately bullish")
elif sentiment['overall_sentiment'] >= 2.5:
    print("Neutral to slightly bearish")
else:
    print("Bearish sentiment")
```

---

## Module: maverick_mcp.concall.services.rag_service

### RAGService

Retrieval-Augmented Generation for transcript Q&A.

**Class**: `RAGService`

**Methods**:

#### setup_rag()

Create vector embeddings for transcript.

**Signature**:
```python
def setup_rag(
    self,
    transcript_id: int,
    force_rebuild: bool = False
) -> int
```

**Parameters**:
- `transcript_id` (int): Transcript database ID
- `force_rebuild` (bool, optional): Rebuild if exists. Default: False

**Returns**:
- int: Number of chunks created

**Process**:
1. Split transcript into ~500-1000 token chunks
2. Generate embeddings using OpenAI text-embedding-3-small
3. Store chunks and embeddings in database
4. Index for fast retrieval

**Example**:
```python
from maverick_mcp.concall.services.rag_service import RAGService

service = RAGService()

# Setup RAG for transcript
num_chunks = service.setup_rag(transcript_id=123)
print(f"Created {num_chunks} chunks")
```

---

#### query()

Ask questions about transcript.

**Signature**:
```python
def query(
    self,
    transcript_id: int,
    question: str,
    top_k: int = 5
) -> dict
```

**Parameters**:
- `transcript_id` (int): Transcript database ID
- `question` (str): User question
- `top_k` (int, optional): Number of relevant chunks to retrieve. Default: 5

**Returns**:
- dict: Answer with:
  - `answer` (str): AI-generated answer
  - `sources` (list): Relevant transcript excerpts with citations
  - `confidence` (float): Answer confidence 0-1

**Example**:
```python
# Query transcript
result = service.query(
    transcript_id=123,
    question="What did management say about AI initiatives?"
)

print(result['answer'])
print(f"Confidence: {result['confidence']}")

# Show sources
for i, source in enumerate(result['sources'], 1):
    print(f"\nSource {i}:")
    print(source['text'])
```

---

## Module: maverick_mcp.concall.services.comparison_service

### ComparisonService

Compare sentiment across multiple quarters.

**Class**: `ComparisonService`

**Methods**:

#### compare_quarters()

Compare sentiment trends over time.

**Signature**:
```python
def compare_quarters(
    self,
    ticker: str,
    quarters: list[tuple[str, int]]
) -> dict
```

**Parameters**:
- `ticker` (str): Stock symbol
- `quarters` (list[tuple]): List of (quarter, year) tuples

**Returns**:
- dict: Comparison with:
  - `sentiment_trends` (list): Sentiment progression
  - `key_changes` (list): Major shifts between quarters
  - `progression` (str): Overall trend (improving/declining/stable)

**Example**:
```python
from maverick_mcp.concall.services.comparison_service import ComparisonService

service = ComparisonService()

# Compare 3 quarters
comparison = service.compare_quarters(
    ticker="AAPL",
    quarters=[("Q2", 2024), ("Q3", 2024), ("Q4", 2024)]
)

print(f"Trend: {comparison['progression']}")

for change in comparison['key_changes']:
    print(f"- {change}")
```

---

## Cost & Performance

### API Costs

**Summarization**:
- Concise: $0.005-0.01 per transcript
- Standard: $0.01-0.03 per transcript  
- Detailed: $0.03-0.05 per transcript

**Sentiment Analysis**: $0.005-0.01 per transcript

**RAG Setup**: $0.0001 per transcript (one-time)

**RAG Queries**: $0.001-0.01 per query

### Performance

**Transcript Fetch**: 2-10 seconds (cached: <100ms)

**Summarization**:
- Concise: 10-20 seconds
- Standard: 30-60 seconds
- Detailed: 60-120 seconds

**Sentiment Analysis**: 10-20 seconds

**RAG Setup**: 20-40 seconds (one-time per transcript)

**RAG Queries**: 3-5 seconds

### Caching

All services use multi-tier caching:
- **L1 (Redis)**: < 1ms
- **L2 (Database)**: < 100ms
- **L3 (AI Generation)**: Seconds to minutes

Cache duration: 7 days for all conference call data

---

## Best Practices

### Service Initialization

```python
# Initialize services once, reuse
transcript_service = TranscriptService()
summarization_service = SummarizationService()
sentiment_service = SentimentService()
rag_service = RAGService()
```

### Error Handling

```python
try:
    summary = summarization_service.summarize(transcript_id)
except ValueError as e:
    print(f"Invalid input: {e}")
except AIError as e:
    print(f"AI service error: {e}")
```

### Batch Processing

```python
# Process multiple transcripts
transcript_ids = [101, 102, 103]

for tid in transcript_ids:
    summary = summarization_service.summarize(tid)
    sentiment = sentiment_service.analyze_sentiment(tid)
    rag_service.setup_rag(tid)
```

### Use Appropriate Detail Level

```python
# Quick check - use concise
summary = service.summarize(tid, mode="concise")

# Investment decision - use detailed
summary = service.summarize(tid, mode="detailed")

# General research - use standard
summary = service.summarize(tid, mode="standard")
```
