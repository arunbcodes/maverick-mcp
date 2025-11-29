# Conference Call Cache System

Multi-tier caching architecture for conference call data (Commit 13).

## Overview

Production-grade caching layer with SOLID principles, designed for easy extraction into a separate microservice.

### Architecture Tiers

- **L1 Cache**: Redis/In-memory (1-5ms response time)
- **L2 Cache**: Database (10-50ms response time)
- **L3 Source**: External APIs/AI (1000-60000ms response time)

### Performance Benefits

- 100-1000x speedup for cached data
- Significant cost savings on AI operations
- Redis connection pooling for production efficiency
- Automatic fallback to in-memory cache if Redis unavailable

---

## Module: maverick_mcp.concall.cache.backends

### ICacheBackend

Abstract interface for all cache implementations.

**Class**: `ICacheBackend` (Abstract Base Class)

**Methods**:

#### get()

Retrieve value from cache.

**Signature**:
```python
@abstractmethod
def get(self, key: str) -> Any | None
```

**Parameters**:
- `key` (str): Cache key

**Returns**:
- Any | None: Cached value or None if not found

---

#### set()

Store value in cache.

**Signature**:
```python
@abstractmethod
def set(self, key: str, value: Any, ttl: int | None = None) -> bool
```

**Parameters**:
- `key` (str): Cache key
- `value` (Any): Value to cache (must be serializable)
- `ttl` (int, optional): Time-to-live in seconds

**Returns**:
- bool: True if successful

---

#### delete()

Remove value from cache.

**Signature**:
```python
@abstractmethod
def delete(self, key: str) -> bool
```

---

#### clear()

Clear all or pattern-matched cache entries.

**Signature**:
```python
@abstractmethod
def clear(self, pattern: str = "*") -> int
```

**Parameters**:
- `pattern` (str, optional): Key pattern to match. Default: "*" (all)

**Returns**:
- int: Number of entries cleared

---

#### health_check()

Check cache backend health.

**Signature**:
```python
@abstractmethod
def health_check(self) -> bool
```

**Returns**:
- bool: True if cache backend is healthy

---

### RedisCacheBackend

Production Redis cache with connection pooling.

**Class**: `RedisCacheBackend`

**Initialization**:
```python
from maverick_india.concall.cache.backends import RedisCacheBackend

cache = RedisCacheBackend(
    host="localhost",
    port=6379,
    db=0,
    password=None,
    max_connections=10
)
```

**Parameters**:
- `host` (str, optional): Redis host. Default: "localhost"
- `port` (int, optional): Redis port. Default: 6379
- `db` (int, optional): Redis database number. Default: 0
- `password` (str, optional): Redis password. Default: None
- `max_connections` (int, optional): Connection pool size. Default: 10

**Features**:
- Connection pooling for efficiency
- Automatic reconnection on failure
- JSON serialization for complex objects
- Namespace support for key organization
- Pattern-based key deletion

**Example**:
```python
from maverick_india.concall.cache.backends import RedisCacheBackend

# Initialize
cache = RedisCacheBackend(host="localhost", port=6379)

# Store data
cache.set("transcript:AAPL:Q4:2024", transcript_data, ttl=604800)

# Retrieve data
data = cache.get("transcript:AAPL:Q4:2024")

# Clear namespace
cache.clear("transcript:*")

# Health check
if cache.health_check():
    print("Redis is healthy")
```

---

### InMemoryCacheBackend

In-memory cache for development and fallback.

**Class**: `InMemoryCacheBackend`

**Initialization**:
```python
from maverick_india.concall.cache.backends import InMemoryCacheBackend

cache = InMemoryCacheBackend(max_size=1000)
```

**Parameters**:
- `max_size` (int, optional): Maximum cache entries. Default: 1000

**Features**:
- No external dependencies
- TTL support with automatic expiration
- LRU eviction when max_size reached
- Thread-safe operations
- Perfect for testing and development

**Example**:
```python
from maverick_india.concall.cache.backends import InMemoryCacheBackend

# Initialize
cache = InMemoryCacheBackend(max_size=500)

# Use same interface as Redis
cache.set("key", "value", ttl=3600)
value = cache.get("key")
```

---

## Module: maverick_mcp.concall.cache.cache_service

### ConcallCacheService

High-level domain-specific caching API.

**Class**: `ConcallCacheService`

**Initialization**:
```python
from maverick_india.concall.cache.cache_service import ConcallCacheService

# Auto-detects Redis, falls back to in-memory
service = ConcallCacheService()

# Force specific backend
service = ConcallCacheService(backend="redis")
service = ConcallCacheService(backend="memory")
```

**Methods**:

#### get_transcript()

Retrieve cached transcript.

**Signature**:
```python
def get_transcript(
    self,
    ticker: str,
    quarter: str,
    fiscal_year: int
) -> dict | None
```

**Parameters**:
- `ticker` (str): Stock symbol
- `quarter` (str): Quarter ("Q1", "Q2", "Q3", "Q4")
- `fiscal_year` (int): Fiscal year

**Returns**:
- dict | None: Cached transcript or None

**Cache Key Format**: `concall:transcript:{ticker}:{quarter}:{year}:v1`

**Example**:
```python
service = ConcallCacheService()

# Check cache
transcript = service.get_transcript("AAPL", "Q4", 2024)
if transcript:
    print("Cache hit!")
else:
    print("Cache miss - fetch from source")
```

---

#### set_transcript()

Cache transcript data.

**Signature**:
```python
def set_transcript(
    self,
    ticker: str,
    quarter: str,
    fiscal_year: int,
    transcript_data: dict,
    ttl: int = 604800
) -> bool
```

**Parameters**:
- `ticker` (str): Stock symbol
- `quarter` (str): Quarter
- `fiscal_year` (int): Year
- `transcript_data` (dict): Transcript to cache
- `ttl` (int, optional): Time-to-live in seconds. Default: 604800 (7 days)

**Returns**:
- bool: True if cached successfully

---

#### get_summary()

Retrieve cached summary.

**Signature**:
```python
def get_summary(
    self,
    ticker: str,
    quarter: str,
    fiscal_year: int,
    mode: str = "standard"
) -> dict | None
```

**Parameters**:
- `ticker` (str): Stock symbol
- `quarter` (str): Quarter
- `fiscal_year` (int): Year
- `mode` (str, optional): Summary mode ("concise", "standard", "detailed")

**Returns**:
- dict | None: Cached summary or None

---

#### set_summary()

Cache summary data.

**Signature**:
```python
def set_summary(
    self,
    ticker: str,
    quarter: str,
    fiscal_year: int,
    summary_data: dict,
    mode: str = "standard",
    ttl: int = 604800
) -> bool
```

---

#### get_sentiment()

Retrieve cached sentiment analysis.

**Signature**:
```python
def get_sentiment(
    self,
    ticker: str,
    quarter: str,
    fiscal_year: int
) -> dict | None
```

---

#### set_sentiment()

Cache sentiment analysis.

**Signature**:
```python
def set_sentiment(
    self,
    ticker: str,
    quarter: str,
    fiscal_year: int,
    sentiment_data: dict,
    ttl: int = 604800
) -> bool
```

---

#### clear_ticker()

Clear all cache for a ticker.

**Signature**:
```python
def clear_ticker(self, ticker: str) -> int
```

**Parameters**:
- `ticker` (str): Stock symbol

**Returns**:
- int: Number of entries cleared

**Example**:
```python
# Clear all cached data for AAPL
count = service.clear_ticker("AAPL")
print(f"Cleared {count} entries")
```

---

#### clear_old_entries()

Clear entries older than specified days.

**Signature**:
```python
def clear_old_entries(self, days: int = 7) -> int
```

**Parameters**:
- `days` (int, optional): Age threshold in days. Default: 7

**Returns**:
- int: Number of entries cleared

---

#### get_cache_stats()

Get cache statistics.

**Signature**:
```python
def get_cache_stats(self) -> dict
```

**Returns**:
- dict: Contains:
  - `backend_type` (str): "redis" or "memory"
  - `total_keys` (int): Total cached entries
  - `hit_rate` (float): Cache hit rate (if tracked)
  - `health` (bool): Backend health status

---

## Module: maverick_mcp.concall.cache.key_generator

### CacheKeyGenerator

Consistent, versioned cache key generation.

**Class**: `CacheKeyGenerator`

**Methods**:

#### generate_transcript_key()

Generate cache key for transcript.

**Signature**:
```python
@staticmethod
def generate_transcript_key(
    ticker: str,
    quarter: str,
    fiscal_year: int,
    version: int = 1
) -> str
```

**Parameters**:
- `ticker` (str): Stock symbol
- `quarter` (str): Quarter
- `fiscal_year` (int): Year
- `version` (int, optional): Cache key version. Default: 1

**Returns**:
- str: Cache key

**Format**: `concall:transcript:{ticker}:{quarter}:{year}:v{version}`

**Example**:
```python
from maverick_india.concall.cache.key_generator import CacheKeyGenerator

key = CacheKeyGenerator.generate_transcript_key("AAPL", "Q4", 2024)
print(key)  # "concall:transcript:AAPL:Q4:2024:v1"
```

---

#### generate_summary_key()

Generate cache key for summary.

**Signature**:
```python
@staticmethod
def generate_summary_key(
    ticker: str,
    quarter: str,
    fiscal_year: int,
    mode: str = "standard",
    version: int = 1
) -> str
```

**Format**: `concall:summary:{ticker}:{quarter}:{year}:{mode}:v{version}`

---

#### generate_sentiment_key()

Generate cache key for sentiment.

**Signature**:
```python
@staticmethod
def generate_sentiment_key(
    ticker: str,
    quarter: str,
    fiscal_year: int,
    version: int = 1
) -> str
```

**Format**: `concall:sentiment:{ticker}:{quarter}:{year}:v{version}`

---

#### parse_key()

Parse cache key into components.

**Signature**:
```python
@staticmethod
def parse_key(key: str) -> dict
```

**Parameters**:
- `key` (str): Cache key

**Returns**:
- dict: Parsed components (type, ticker, quarter, year, version, etc.)

**Example**:
```python
key = "concall:transcript:AAPL:Q4:2024:v1"
parsed = CacheKeyGenerator.parse_key(key)

print(parsed)
# {
#   'namespace': 'concall',
#   'type': 'transcript',
#   'ticker': 'AAPL',
#   'quarter': 'Q4',
#   'fiscal_year': 2024,
#   'version': 1
# }
```

---

## Design Principles

### SOLID Compliance

**Single Responsibility**: Each class has one reason to change
- `ICacheBackend`: Cache operations interface
- `RedisCacheBackend`: Redis-specific implementation
- `InMemoryCacheBackend`: In-memory implementation
- `CacheKeyGenerator`: Key generation logic
- `ConcallCacheService`: Domain-specific caching API

**Open/Closed**: Extensible via new backends without modifying core
- Add new backends by implementing `ICacheBackend`
- No changes needed to existing code

**Liskov Substitution**: All backends are interchangeable
- Any `ICacheBackend` can replace another
- Services work with any backend

**Interface Segregation**: Minimal, focused interfaces
- `ICacheBackend` has only essential methods
- No bloated interfaces

**Dependency Inversion**: Services depend on abstractions
- `ConcallCacheService` depends on `ICacheBackend` interface
- Not on concrete implementations

---

## Integration with Services

### TranscriptFetcher Integration

```python
from maverick_india.concall.cache.cache_service import ConcallCacheService
from maverick_india.concall.services.transcript_fetcher import TranscriptFetcher

cache_service = ConcallCacheService()
fetcher = TranscriptFetcher(cache_service=cache_service)

# Automatically uses L1 cache
transcript = fetcher.fetch_transcript("AAPL", "Q4", 2024)
```

### Summarization Service Integration

```python
from maverick_india.concall.services.concall_summarizer import ConcallSummarizer

summarizer = ConcallSummarizer(cache_service=cache_service)

# Check L1 cache before generating
summary = summarizer.summarize(transcript_id=123, mode="standard")
```

---

## Deployment Configurations

### Development (In-Memory)

```python
service = ConcallCacheService(backend="memory")
```

**Benefits**:
- No external dependencies
- Fast setup
- Perfect for testing

### Production (Redis)

```python
service = ConcallCacheService(
    backend="redis",
    redis_host="cache.example.com",
    redis_port=6379,
    redis_password="secure-password"
)
```

**Benefits**:
- Shared cache across instances
- Persistent across restarts
- High performance (1-5ms)

### Hybrid (Auto-Detection)

```python
service = ConcallCacheService()  # Auto-detects Redis
```

**Benefits**:
- Tries Redis first
- Falls back to in-memory if Redis unavailable
- Works everywhere

---

## Monitoring and Health Checks

### Health Check

```python
service = ConcallCacheService()

if service.health_check():
    print("✅ Cache is healthy")
else:
    print("⚠️ Cache degraded (using fallback)")
```

### Cache Statistics

```python
stats = service.get_cache_stats()
print(f"Backend: {stats['backend_type']}")
print(f"Total Keys: {stats['total_keys']}")
print(f"Hit Rate: {stats['hit_rate']:.2%}")
```

### Logging

All cache operations are logged with L1/L2/L3 hit tracking:

```
INFO: L1 cache hit for concall:transcript:AAPL:Q4:2024:v1
INFO: L2 cache miss for concall:summary:MSFT:Q3:2024:standard:v1
INFO: L3 source fetch for concall:sentiment:GOOGL:Q2:2024:v1
```

---

## Performance Metrics

### Response Times

- **L1 Hit (Redis)**: ~1-5ms
- **L1 Hit (Memory)**: ~0.1-1ms
- **L2 Hit (Database)**: ~10-50ms
- **L3 Miss (API/AI)**: ~1000-60000ms

### Cost Savings

- **Transcript Fetch**: $0 (cached) vs $0.01 (API)
- **AI Summary**: $0 (cached) vs $0.01-0.05 (API)
- **Sentiment Analysis**: $0 (cached) vs $0.005-0.01 (API)

**7-day cache = 100% cost savings for repeat access**

---

## Future Enhancements

### Microservice Extraction

The cache layer is designed for easy extraction:

```
maverick-mcp/
  └── maverick_mcp/
      └── concall/
          └── cache/  ← Can become separate service
```

### Additional Backends

Easy to add:
- Memcached backend
- DynamoDB backend
- S3 backend for large objects

### Distributed Caching

Redis Cluster support for horizontal scaling.

---

## Best Practices

### Always Use Service Layer

```python
# Good - Use ConcallCacheService
service = ConcallCacheService()
transcript = service.get_transcript("AAPL", "Q4", 2024)

# Bad - Direct backend usage
backend = RedisCacheBackend()
transcript = backend.get("concall:transcript:AAPL:Q4:2024:v1")
```

### Handle Cache Misses Gracefully

```python
transcript = service.get_transcript("AAPL", "Q4", 2024)
if not transcript:
    transcript = fetch_from_source()
    service.set_transcript("AAPL", "Q4", 2024, transcript)
```

### Clear Stale Data

```python
# Clear old entries weekly
service.clear_old_entries(days=7)

# Clear ticker on news/events
service.clear_ticker("AAPL")
```

### Monitor Health

```python
# Periodic health checks
if not service.health_check():
    alert_ops_team()
```
