# Conference Call Providers

Data providers for fetching conference call transcripts.

## Module: maverick_mcp.concall.providers.company_ir_provider

### CompanyIRProvider

Fetch transcripts from company investor relations websites.

**Class**: `CompanyIRProvider`

**Methods**:

#### fetch_transcript()

Fetch transcript from company IR website.

**Signature**:
```python
def fetch_transcript(
    self,
    ticker: str,
    quarter: str,
    fiscal_year: int
) -> dict | None
```

**Parameters**:
- `ticker` (str): Stock symbol (e.g., "AAPL", "MSFT")
- `quarter` (str): Quarter ("Q1", "Q2", "Q3", "Q4")
- `fiscal_year` (int): Fiscal year (e.g., 2025)

**Returns**:
- dict | None: Transcript data or None if not found
  - `transcript_text` (str): Full transcript
  - `source` (str): "company_ir"
  - `source_url` (str): Original URL
  - `metadata` (dict): Additional info

**Example**:
```python
from maverick_india.concall.providers.company_ir_provider import CompanyIRProvider

provider = CompanyIRProvider()
transcript = provider.fetch_transcript("AAPL", "Q4", 2024)

if transcript:
    print(f"Fetched from: {transcript['source_url']}")
    print(f"Length: {len(transcript['transcript_text'])} chars")
```

---

#### get_ir_url()

Get company IR website URL.

**Signature**:
```python
def get_ir_url(self, ticker: str) -> str | None
```

**Parameters**:
- `ticker` (str): Stock symbol

**Returns**:
- str | None: IR website URL or None if not found

**Example**:
```python
ir_url = provider.get_ir_url("AAPL")
print(ir_url)  # https://investor.apple.com/
```

---

## Module: maverick_mcp.concall.providers.nse_provider

### NSEProvider

Fetch transcripts from NSE (National Stock Exchange of India).

**Class**: `NSEProvider`

**Methods**:

#### fetch_transcript()

Fetch transcript from NSE filings.

**Signature**:
```python
def fetch_transcript(
    self,
    ticker: str,
    quarter: str,
    fiscal_year: int
) -> dict | None
```

**Parameters**:
- `ticker` (str): Stock symbol with .NS suffix (e.g., "RELIANCE.NS")
- `quarter` (str): Quarter ("Q1", "Q2", "Q3", "Q4")
- `fiscal_year` (int): Fiscal year

**Returns**:
- dict | None: Transcript data or None if not found

**Data Source**: NSE corporate announcements and filings

**Example**:
```python
from maverick_india.concall.providers.nse_provider import NSEProvider

provider = NSEProvider()
transcript = provider.fetch_transcript("RELIANCE.NS", "Q1", 2025)

if transcript:
    print(f"Source: NSE Exchange Filing")
    print(transcript['transcript_text'][:500])
```

---

#### search_filings()

Search NSE filings for transcripts.

**Signature**:
```python
def search_filings(
    self,
    ticker: str,
    start_date: str,
    end_date: str
) -> list[dict]
```

**Parameters**:
- `ticker` (str): Stock symbol with .NS suffix
- `start_date` (str): Start date (YYYY-MM-DD)
- `end_date` (str): End date (YYYY-MM-DD)

**Returns**:
- list[dict]: List of filing metadata

---

## Module: maverick_india.concall.providers.screener_provider

### ScreenerProvider

Fetch transcripts from [Screener.in](https://www.screener.in/concalls/) - a consolidated repository of Indian company earnings call transcripts.

**Class**: `ScreenerProvider`

**Status**: ✅ Available

**Methods**:

#### fetch_transcript()

Fetch transcript from Screener.in.

**Signature**:
```python
async def fetch_transcript(
    self,
    ticker: str,
    quarter: str,
    fiscal_year: int
) -> dict | None
```

**Parameters**:
- `ticker` (str): Stock symbol (e.g., "RELIANCE.NS", "TCS.NS")
- `quarter` (str): Quarter ("Q1", "Q2", "Q3", "Q4")
- `fiscal_year` (int): Fiscal year

**Returns**:
- dict | None: Transcript data or None if not found
  - `transcript_text` (str): Full transcript
  - `source` (str): "screener"
  - `source_url` (str): Screener.in URL
  - `metadata` (dict): Additional info

**Data Sources**:
1. Company-specific concalls page: `/company/{SYMBOL}/concalls/`
2. Main concalls search page: `/concalls/`

**Example**:
```python
from maverick_india.concall import ScreenerProvider

provider = ScreenerProvider()
transcript = await provider.fetch_transcript("RELIANCE.NS", "Q1", 2025)

if transcript:
    print(f"Source: {transcript['source_url']}")
    print(transcript['transcript_text'][:500])
```

**Features**:
- All Indian NSE/BSE companies supported
- Automatic symbol normalization
- Rate-limited (2s between requests)
- 20+ ticker-to-company mappings pre-configured
- PDF/HTML format support

!!! note "Premium Features"
    Some transcripts on Screener.in may require a premium account.

---

## Cascading Provider System

### TranscriptFetcher

Multi-provider orchestration with automatic fallback.

**Class**: `TranscriptFetcher`

**Methods**:

#### fetch_transcript()

Fetch transcript with cascading fallback.

**Signature**:
```python
def fetch_transcript(
    self,
    ticker: str,
    quarter: str,
    fiscal_year: int
) -> dict | None
```

**Fallback Order**:
1. **Database Cache** (always checked first) - 7-day TTL
2. **Company IR Website** (primary) - Direct from official source
3. **NSE Exchange Filings** (fallback 1) - For Indian stocks
4. **Screener.in** (fallback 2) - Consolidated Indian transcripts

**Example**:
```python
from maverick_india.concall.providers import TranscriptFetcher

fetcher = TranscriptFetcher()

# Automatically tries all providers
transcript = fetcher.fetch_transcript("RELIANCE.NS", "Q1", 2025)

if transcript:
    print(f"Fetched from: {transcript['source']}")
else:
    print("Transcript not found in any source")
```

---

## Provider Selection Logic

### US Stocks

For US stocks (no suffix):
1. Try Company IR website
2. Return None if not found

**Example**: "AAPL" → Company IR only

### Indian NSE Stocks

For .NS suffix stocks:
1. Check database cache first
2. Try Company IR website
3. Fallback to NSE exchange filings
4. Fallback to Screener.in

**Example**: "RELIANCE.NS" → Cache → Company IR → NSE → Screener.in

### Indian BSE Stocks

For .BO suffix stocks:
1. Try Company IR website
2. Return None if not found (BSE filing support future)

**Example**: "TCS.BO" → Company IR only

---

## Error Handling

### Provider Errors

```python
from maverick_india.concall.providers import TranscriptFetcher, ProviderError

fetcher = TranscriptFetcher()

try:
    transcript = fetcher.fetch_transcript("AAPL", "Q4", 2024)
except ProviderError as e:
    print(f"Provider error: {e}")
except ValueError as e:
    print(f"Invalid input: {e}")
```

### Common Errors

- **ProviderError**: Provider-specific failure
- **ValueError**: Invalid ticker, quarter, or year
- **TimeoutError**: Request timeout (30s default)
- **ConnectionError**: Network issues

---

## Performance Optimization

### Caching

All providers automatically cache results:
- **Cache Duration**: 7 days
- **Cache Key**: `transcript:{ticker}:{quarter}:{year}`
- **Cache Tiers**: Redis (L1) → Database (L2) → API (L3)

### Retry Logic

- **Max Retries**: 3 attempts per provider
- **Backoff**: Exponential (1s, 2s, 4s)
- **Timeout**: 30s per request

### Rate Limiting

- **NSE Provider**: 10 requests/minute
- **Company IR**: No specific limit (be respectful)

---

## Best Practices

### Error Recovery

```python
fetcher = TranscriptFetcher()

# Try with error handling
for attempt in range(3):
    try:
        transcript = fetcher.fetch_transcript(ticker, quarter, year)
        break
    except ProviderError:
        if attempt == 2:
            raise
        time.sleep(2 ** attempt)
```

### Batch Fetching

```python
from concurrent.futures import ThreadPoolExecutor

calls = [
    ("AAPL", "Q1", 2025),
    ("MSFT", "Q1", 2025),
    ("GOOGL", "Q1", 2025)
]

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(
        lambda x: fetcher.fetch_transcript(*x),
        calls
    ))
```

### Cache Warming

```python
# Pre-fetch and cache important transcripts
important_stocks = ["AAPL", "MSFT", "GOOGL"]
quarters = ["Q1", "Q2", "Q3", "Q4"]

for ticker in important_stocks:
    for quarter in quarters:
        fetcher.fetch_transcript(ticker, quarter, 2024)
```
