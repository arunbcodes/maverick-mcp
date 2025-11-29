# Conference Call Utilities

Utility functions for conference call processing.

## Module: maverick_mcp.concall.utils.text_processing

### chunk_text()

Split text into manageable chunks for processing.

**Signature**:
```python
def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200
) -> list[str]
```

**Parameters**:
- `text` (str): Text to split
- `chunk_size` (int, optional): Target chunk size in tokens. Default: 1000
- `overlap` (int, optional): Overlap between chunks. Default: 200

**Returns**:
- list[str]: Text chunks

**Purpose**: 
- Maintains context between chunks with overlap
- Ensures chunks fit within AI model token limits
- Preserves sentence boundaries

**Example**:
```python
from maverick_india.concall.utils.text_processing import chunk_text

transcript = "Very long transcript text..."
chunks = chunk_text(transcript, chunk_size=800, overlap=150)

print(f"Created {len(chunks)} chunks")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i}: {len(chunk)} characters")
```

---

### extract_speakers()

Extract speaker names from transcript.

**Signature**:
```python
def extract_speakers(text: str) -> list[str]
```

**Parameters**:
- `text` (str): Transcript text

**Returns**:
- list[str]: Unique speaker names

**Example**:
```python
from maverick_india.concall.utils.text_processing import extract_speakers

speakers = extract_speakers(transcript_text)
print(f"Speakers: {', '.join(speakers)}")
# Output: "Speakers: Tim Cook, Luca Maestri, Analyst 1"
```

---

### clean_transcript()

Clean and normalize transcript text.

**Signature**:
```python
def clean_transcript(text: str) -> str
```

**Parameters**:
- `text` (str): Raw transcript text

**Returns**:
- str: Cleaned transcript

**Cleaning Steps**:
- Remove HTML tags and entities
- Normalize whitespace
- Fix common OCR errors
- Remove timestamps and metadata
- Standardize speaker labels

**Example**:
```python
from maverick_india.concall.utils.text_processing import clean_transcript

raw_text = "<p>Tim Cook:&nbsp;&nbsp;Good morning...</p>"
cleaned = clean_transcript(raw_text)
print(cleaned)
# Output: "Tim Cook: Good morning..."
```

---

## Module: maverick_mcp.concall.utils.validation

### validate_quarter()

Validate quarter string.

**Signature**:
```python
def validate_quarter(quarter: str) -> str
```

**Parameters**:
- `quarter` (str): Quarter string (e.g., "Q1", "q2", "1")

**Returns**:
- str: Normalized quarter ("Q1", "Q2", "Q3", "Q4")

**Raises**:
- ValueError: Invalid quarter

**Accepted Formats**:
- "Q1", "Q2", "Q3", "Q4" (case insensitive)
- "1", "2", "3", "4"
- "FY Q1", "FY Q2", etc.

**Example**:
```python
from maverick_india.concall.utils.validation import validate_quarter

quarter = validate_quarter("q1")  # Returns "Q1"
quarter = validate_quarter("2")   # Returns "Q2"
quarter = validate_quarter("Q3")  # Returns "Q3"
```

---

### validate_fiscal_year()

Validate fiscal year.

**Signature**:
```python
def validate_fiscal_year(year: int) -> int
```

**Parameters**:
- `year` (int): Fiscal year

**Returns**:
- int: Validated year

**Raises**:
- ValueError: Invalid year (before 2000 or in future)

**Example**:
```python
from maverick_india.concall.utils.validation import validate_fiscal_year

year = validate_fiscal_year(2024)  # OK
year = validate_fiscal_year(1999)  # Raises ValueError
year = validate_fiscal_year(2030)  # Raises ValueError (future)
```

---

### validate_ticker_for_concall()

Validate ticker for conference call access.

**Signature**:
```python
def validate_ticker_for_concall(ticker: str) -> str
```

**Parameters**:
- `ticker` (str): Stock symbol

**Returns**:
- str: Validated and normalized ticker

**Raises**:
- ValueError: Invalid ticker format

**Supported Formats**:
- US stocks: "AAPL", "MSFT", "GOOGL"
- Indian NSE: "RELIANCE.NS", "TCS.NS"
- Indian BSE: "INFY.BO", "WIPRO.BO"

---

## Module: maverick_mcp.concall.utils.date_helpers

### get_quarter_dates()

Get start and end dates for a quarter.

**Signature**:
```python
def get_quarter_dates(
    quarter: str,
    fiscal_year: int
) -> tuple[date, date]
```

**Parameters**:
- `quarter` (str): Quarter ("Q1", "Q2", "Q3", "Q4")
- `fiscal_year` (int): Fiscal year

**Returns**:
- tuple[date, date]: (start_date, end_date)

**Example**:
```python
from maverick_india.concall.utils.date_helpers import get_quarter_dates

start, end = get_quarter_dates("Q1", 2024)
print(f"Q1 2024: {start} to {end}")
# Output: "Q1 2024: 2024-01-01 to 2024-03-31"
```

---

### get_previous_quarter()

Get previous quarter.

**Signature**:
```python
def get_previous_quarter(
    quarter: str,
    fiscal_year: int
) -> tuple[str, int]
```

**Parameters**:
- `quarter` (str): Current quarter
- `fiscal_year` (int): Current fiscal year

**Returns**:
- tuple[str, int]: (previous_quarter, year)

**Example**:
```python
from maverick_india.concall.utils.date_helpers import get_previous_quarter

prev_q, prev_y = get_previous_quarter("Q1", 2024)
print(f"Previous: {prev_q} {prev_y}")
# Output: "Previous: Q4 2023"

prev_q, prev_y = get_previous_quarter("Q2", 2024)
# Output: Q1 2024
```

---

### estimate_earnings_date()

Estimate earnings call date for a quarter.

**Signature**:
```python
def estimate_earnings_date(
    quarter: str,
    fiscal_year: int
) -> date
```

**Parameters**:
- `quarter` (str): Quarter
- `fiscal_year` (int): Fiscal year

**Returns**:
- date: Estimated earnings date

**Logic**: Typically 2-4 weeks after quarter end

---

## Module: maverick_mcp.concall.utils.caching

### get_concall_cache_key()

Generate cache key for conference call data.

**Signature**:
```python
def get_concall_cache_key(
    ticker: str,
    quarter: str,
    fiscal_year: int,
    data_type: str
) -> str
```

**Parameters**:
- `ticker` (str): Stock symbol
- `quarter` (str): Quarter
- `fiscal_year` (int): Year
- `data_type` (str): Type ("transcript", "summary", "sentiment", "rag")

**Returns**:
- str: Cache key

**Example**:
```python
from maverick_india.concall.utils.caching import get_concall_cache_key

# Transcript cache key
key = get_concall_cache_key("AAPL", "Q4", 2024, "transcript")
print(key)  # "concall:transcript:AAPL:Q4:2024"

# Summary cache key
key = get_concall_cache_key("AAPL", "Q4", 2024, "summary")
print(key)  # "concall:summary:AAPL:Q4:2024"
```

---

### cache_concall_data()

Cache conference call data.

**Signature**:
```python
def cache_concall_data(
    ticker: str,
    quarter: str,
    fiscal_year: int,
    data_type: str,
    data: Any
) -> bool
```

**Parameters**:
- `ticker` (str): Stock symbol
- `quarter` (str): Quarter
- `fiscal_year` (int): Year
- `data_type` (str): Type
- `data` (Any): Data to cache

**Returns**:
- bool: True if cached successfully

**TTL**: 7 days for all conference call data

---

### get_cached_concall_data()

Retrieve cached conference call data.

**Signature**:
```python
def get_cached_concall_data(
    ticker: str,
    quarter: str,
    fiscal_year: int,
    data_type: str
) -> Any | None
```

**Returns**:
- Any | None: Cached data or None

---

## Module: maverick_mcp.concall.utils.metrics

### calculate_sentiment_change()

Calculate sentiment change between quarters.

**Signature**:
```python
def calculate_sentiment_change(
    current_sentiment: float,
    previous_sentiment: float
) -> dict
```

**Parameters**:
- `current_sentiment` (float): Current quarter sentiment (1-5)
- `previous_sentiment` (float): Previous quarter sentiment (1-5)

**Returns**:
- dict: Contains:
  - `change` (float): Absolute change
  - `change_percent` (float): Percentage change
  - `direction` (str): "improving", "declining", or "stable"

**Example**:
```python
from maverick_india.concall.utils.metrics import calculate_sentiment_change

change = calculate_sentiment_change(4.2, 3.8)
print(f"Change: {change['change']}")  # 0.4
print(f"Direction: {change['direction']}")  # "improving"
```

---

### aggregate_sentiment_trend()

Calculate trend across multiple quarters.

**Signature**:
```python
def aggregate_sentiment_trend(
    sentiments: list[float]
) -> dict
```

**Parameters**:
- `sentiments` (list[float]): List of sentiment scores in chronological order

**Returns**:
- dict: Contains:
  - `average` (float): Average sentiment
  - `trend` (str): "improving", "declining", or "stable"
  - `volatility` (float): Sentiment volatility

---

## Best Practices

### Text Processing

```python
from maverick_india.concall.utils.text_processing import clean_transcript, chunk_text

# Always clean before processing
raw_text = fetch_transcript(...)
cleaned = clean_transcript(raw_text)

# Use appropriate chunk size for your model
chunks = chunk_text(cleaned, chunk_size=1000)
```

### Validation

```python
from maverick_india.concall.utils.validation import (
    validate_quarter,
    validate_fiscal_year,
    validate_ticker_for_concall
)

# Validate all inputs
try:
    ticker = validate_ticker_for_concall(user_ticker)
    quarter = validate_quarter(user_quarter)
    year = validate_fiscal_year(user_year)
except ValueError as e:
    return {"error": str(e)}
```

### Caching

```python
from maverick_india.concall.utils.caching import (
    get_cached_concall_data,
    cache_concall_data
)

# Always check cache first
cached = get_cached_concall_data(ticker, quarter, year, "summary")
if cached:
    return cached

# Generate and cache
summary = generate_summary(...)
cache_concall_data(ticker, quarter, year, "summary", summary)
```

### Date Helpers

```python
from maverick_india.concall.utils.date_helpers import (
    get_quarter_dates,
    get_previous_quarter
)

# Get quarter date range
start, end = get_quarter_dates("Q1", 2024)

# Compare with previous quarter
prev_q, prev_y = get_previous_quarter("Q1", 2024)
```

### Metrics

```python
from maverick_india.concall.utils.metrics import (
    calculate_sentiment_change,
    aggregate_sentiment_trend
)

# Track sentiment changes
change = calculate_sentiment_change(current, previous)
if change['direction'] == "declining":
    print("⚠️ Sentiment deteriorating")

# Analyze long-term trend
trend = aggregate_sentiment_trend([3.5, 3.7, 4.0, 4.2])
print(f"Trend: {trend['trend']}")  # "improving"
```
