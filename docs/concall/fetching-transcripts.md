# Fetching Earnings Call Transcripts

Comprehensive guide to transcript fetching in Maverick MCP.

## Overview

Maverick MCP fetches earnings call transcripts from multiple sources with intelligent cascading fallback to ensure high availability. The system automatically parses various formats (PDF, HTML, TXT) and stores them in a structured database.

## Data Sources

### Primary Source: Company Investor Relations Websites

The system attempts to fetch transcripts directly from company IR websites first.

**Advantages:**
- Most reliable and up-to-date
- Official source with verified content
- Often available immediately after calls
- Complete transcripts with Q&A

**Supported Formats:**
- PDF transcripts
- HTML pages
- Plain text files

### Fallback Source 1: NSE Exchange Filings

For Indian stocks (.NS suffix), transcripts are fetched from NSE regulatory filings.

**Advantages:**
- Mandatory regulatory requirement
- Standardized format
- Historical archive available
- Verified by exchange

**Supported Companies:**
- All NSE-listed companies
- Nifty 50 constituents
- Major BSE stocks

### Fallback Source 2: Screener.in

[Screener.in](https://www.screener.in/concalls/) provides a consolidated repository of Indian company earnings call transcripts.

**Advantages:**
- All Indian companies in one place
- Well-organized by quarter/year
- Often has transcripts when other sources fail
- Popular among Indian investors

**URL:** https://www.screener.in/concalls/

**Supported Companies:**
- All major NSE/BSE listed companies
- Nifty 50, Nifty Next 50
- Mid-cap and small-cap stocks

!!! note "Premium Features"
    Some transcripts on Screener.in may require a premium account. Free accounts have access to recent transcripts.

## Fetching Process

### Step 1: Company Identification

```python
# Example: Fetching RELIANCE.NS Q1 FY2025 transcript
ticker = "RELIANCE.NS"
quarter = "Q1"
fiscal_year = 2025
```

**Market Detection:**
- `.NS` suffix → NSE (India)
- `.BO` suffix → BSE (India)
- No suffix → US market

### Step 2: Source Selection

The system cascades through sources in priority order:

```
1. Company IR Website (Primary - most reliable)
   ├─ Check for transcript section
   ├─ Parse quarter/year from URL patterns
   └─ Download PDF/HTML content

2. NSE Exchange Filings (Fallback 1)
   ├─ Query corporate actions API
   ├─ Filter for earnings announcements
   └─ Download attached transcripts

3. Screener.in (Fallback 2 - consolidated source)
   ├─ Search company concalls page
   ├─ Find quarter-specific transcript
   └─ Download PDF/HTML content

4. Database Cache
   └─ Return previously fetched transcript
```

!!! tip "Why Multiple Sources?"
    Different sources may have transcripts at different times. Company IR is fastest, NSE is most official, and Screener.in is most comprehensive for Indian stocks.

### Step 3: Content Extraction

**PDF Processing:**
```python
# Extract text from PDF
text = extract_pdf_text(pdf_file)

# Clean formatting
text = remove_page_numbers(text)
text = normalize_whitespace(text)
text = fix_line_breaks(text)
```

**HTML Processing:**
```python
# Parse HTML structure
soup = BeautifulSoup(html_content)

# Extract transcript section
transcript = soup.find("div", class_="transcript")

# Clean HTML tags
text = strip_html_tags(transcript)
```

### Step 4: Quality Validation

**Validation Checks:**
- Minimum length (500 words)
- Contains company name
- Has date/quarter information
- Includes management participants
- Contains Q&A section

**Example Validation:**
```python
def validate_transcript(text: str, ticker: str) -> bool:
    """Validate transcript quality."""
    checks = [
        len(text.split()) > 500,  # Minimum word count
        ticker.upper() in text,    # Company mentioned
        "Q" in text and "FY" in text,  # Quarter info
        any(role in text for role in ["CEO", "CFO", "MD"]),  # Management
        "question" in text.lower()  # Q&A section
    ]
    return all(checks)
```

### Step 5: Database Storage

**Storage Schema:**
```sql
CREATE TABLE transcripts (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    company_name VARCHAR(255),
    quarter VARCHAR(10) NOT NULL,
    fiscal_year INTEGER NOT NULL,
    call_date DATE NOT NULL,
    raw_text TEXT NOT NULL,
    source VARCHAR(50),
    fetch_date TIMESTAMP DEFAULT NOW(),
    word_count INTEGER,
    UNIQUE(ticker, quarter, fiscal_year)
);
```

## Using the MCP Tool

### Basic Usage

```
Fetch RELIANCE.NS earnings call transcript for Q1 FY2025
```

**Tool Call:**
```python
concall_fetch_transcript(
    ticker="RELIANCE.NS",
    quarter="Q1",
    fiscal_year=2025
)
```

**Response:**
```json
{
    "status": "success",
    "ticker": "RELIANCE.NS",
    "company_name": "Reliance Industries Limited",
    "quarter": "Q1",
    "fiscal_year": 2025,
    "call_date": "2024-07-19",
    "word_count": 8547,
    "source": "Company IR",
    "transcript_preview": "Good evening and welcome to Reliance Industries..."
}
```

### Advanced Examples

**Fetch with Auto-Detection:**
```
Get the latest earnings call for TCS
```

The system automatically:
- Detects market (NSE)
- Determines current quarter
- Fetches most recent transcript

**Batch Fetching:**
```
Fetch transcripts for all Nifty 50 companies for Q1 2025
```

Processes multiple tickers in parallel with rate limiting.

## Error Handling

### Common Errors

**1. Transcript Not Found**
```json
{
    "status": "error",
    "error": "TranscriptNotFound",
    "message": "No transcript found for INFY Q1 FY2025",
    "suggestions": [
        "Call may not have occurred yet",
        "Transcript not yet published",
        "Try previous quarter"
    ]
}
```

**Solution:**
- Verify call date (usually 2-3 days after earnings release)
- Check quarter and year format
- Try fetching from a different source

**2. Invalid Quarter Format**
```json
{
    "status": "error",
    "error": "InvalidQuarter",
    "message": "Quarter must be Q1, Q2, Q3, or Q4",
    "provided": "Quarter 1"
}
```

**Solution:**
- Use format: Q1, Q2, Q3, Q4 (not "Quarter 1" or "1Q")

**3. Rate Limit Exceeded**
```json
{
    "status": "error",
    "error": "RateLimitExceeded",
    "message": "Too many requests. Please wait 60 seconds.",
    "retry_after": 60
}
```

**Solution:**
- System implements automatic rate limiting
- Wait for specified retry time
- Batch requests are throttled automatically

## Caching Strategy

### Multi-Tier Caching

**L1: Redis Cache (5 minutes)**
- Recent fetches cached for quick access
- Reduces database load
- Automatic expiration

**L2: Database Cache (Permanent)**
- All transcripts stored permanently
- Indexed by ticker + quarter + year
- Never refetched unless explicitly requested

**L3: API Source (Fallback)**
- Fetches from source if not in cache
- Rate limited to respect provider limits
- Stores result in database

### Cache Invalidation

Transcripts are **never** automatically invalidated because:
- Transcripts don't change after publication
- Historical records are immutable
- Saves API costs and bandwidth

**Manual Refresh:**
```python
# Force refetch (rare use case)
concall_fetch_transcript(
    ticker="TCS.NS",
    quarter="Q1",
    fiscal_year=2025,
    force_refresh=True
)
```

## Performance Characteristics

| Metric | Value |
|--------|-------|
| **Cache Hit (L1/L2)** | < 100ms |
| **Fresh Fetch (PDF)** | 2-5 seconds |
| **Fresh Fetch (HTML)** | 1-3 seconds |
| **NSE API Fetch** | 3-8 seconds |
| **Batch Processing** | 50 tickers/minute |

## Best Practices

### 1. Check Data Availability

```python
# Verify earnings call date first
earnings_date = get_earnings_date("RELIANCE.NS", "Q1", 2025)
# Earnings: Jan 19, 2025

# Transcripts usually available within 2-3 days
fetch_date = earnings_date + timedelta(days=3)
# Safe to fetch: Jan 22, 2025
```

### 2. Use Batch Operations Efficiently

```python
# Good: Batch with delay
tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
for ticker in tickers:
    fetch_transcript(ticker, quarter, year)
    time.sleep(1)  # Respect rate limits

# Bad: Rapid-fire requests (will hit rate limit)
for ticker in tickers:
    fetch_transcript(ticker, quarter, year)  # Too fast!
```

### 3. Handle Missing Transcripts Gracefully

```python
try:
    result = fetch_transcript(ticker, quarter, year)
except TranscriptNotFound:
    # Try previous quarter
    result = fetch_transcript(ticker, f"Q{int(quarter[1])-1}", year)
```

### 4. Verify Quality Before Analysis

```python
transcript = fetch_transcript(ticker, quarter, year)

if transcript["word_count"] < 1000:
    logger.warning("Transcript seems incomplete")

if "question" not in transcript["raw_text"].lower():
    logger.warning("Q&A section may be missing")
```

## Supported Companies

### Indian Market (NSE/BSE)

**Nifty 50:**
All 50 constituents supported, including:
- RELIANCE.NS
- TCS.NS
- INFY.NS
- HDFCBANK.NS
- ICICIBANK.NS

**Nifty Next 50:**
Top 50 mid-cap stocks

**Banking Sector:**
All major banks with regular earnings calls

### US Market

**S&P 500:**
- Selected stocks based on IR website availability
- Major tech companies (AAPL, MSFT, GOOGL)
- Financial institutions

## API Reference

For detailed API documentation, see:
- [Transcript Models](../api-reference/concall/models.md)
- [Provider Architecture](../api-reference/concall/providers.md)

## Troubleshooting

### Transcript Not Downloading

**Check:**
1. Company has published transcript (verify on IR website)
2. Quarter/year format is correct (Q1-Q4, 4-digit year)
3. Ticker symbol includes market suffix (.NS, .BO)
4. Not hitting rate limits (wait 60 seconds between requests)

**Debug Command:**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Fetch with detailed logs
result = fetch_transcript(ticker, quarter, year, debug=True)
```

### Incomplete Transcript

**Possible Causes:**
- PDF parsing errors (corrupted file)
- HTML structure changed
- Partial transcript published

**Solution:**
```python
# Force refetch with different source
result = fetch_transcript(
    ticker, quarter, year,
    prefer_source="NSE",  # Try NSE instead of IR
    force_refresh=True
)
```

## Next Steps

- [AI Summarization →](summarization.md)
- [Sentiment Analysis →](sentiment-analysis.md)
- [RAG Q&A →](rag-qa.md)
