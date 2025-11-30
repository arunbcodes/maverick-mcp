# News & Sentiment

Cryptocurrency news aggregation and sentiment analysis.

## CryptoPanicProvider

News aggregation from CryptoPanic and RSS feeds.

::: maverick_crypto.news.CryptoPanicProvider
    options:
      show_root_heading: true
      members:
        - get_news
        - get_trending
        - get_bullish_news
        - get_bearish_news

### Example Usage

```python
from maverick_crypto.news import CryptoPanicProvider

provider = CryptoPanicProvider()

# Get all news
news = await provider.get_news(limit=20)

# Filter by currency
btc_news = await provider.get_news(currencies=["BTC", "ETH"])

# Get trending (high engagement)
trending = await provider.get_trending(limit=10)

# Get bullish news
bullish = await provider.get_bullish_news(limit=10)

# Get bearish news
bearish = await provider.get_bearish_news(limit=10)
```

### News Sources

Primary source:
- **CryptoPanic**: Aggregated crypto news with community votes

RSS fallback sources:
- Cointelegraph
- Decrypt
- The Block

### News Article Structure

```python
{
    "title": "Bitcoin surges past $100k",
    "url": "https://...",
    "source": "Cointelegraph",
    "published_at": "2024-12-01T10:30:00Z",
    "sentiment": "bullish",  # bullish, bearish, neutral
    "votes": {
        "positive": 45,
        "negative": 5
    },
    "currencies": ["BTC"]
}
```

## NewsAggregator

Combine news from multiple sources.

::: maverick_crypto.news.NewsAggregator
    options:
      show_root_heading: true
      members:
        - get_all_news
        - get_news_summary

### Example Usage

```python
from maverick_crypto.news import NewsAggregator

aggregator = NewsAggregator()

# Get all news
news = await aggregator.get_all_news(
    currencies=["BTC", "ETH"],
    limit=20
)

# Get summary with sentiment breakdown
summary = await aggregator.get_news_summary(currencies=["BTC"])
print(f"Overall: {summary['overall_sentiment']}")
print(f"Bullish: {summary['sentiment_breakdown']['bullish']}")
print(f"Bearish: {summary['sentiment_breakdown']['bearish']}")
```

## CryptoSentimentAnalyzer

Keyword-based sentiment analysis.

::: maverick_crypto.news.CryptoSentimentAnalyzer
    options:
      show_root_heading: true
      members:
        - analyze
        - analyze_batch
        - get_market_sentiment

### Example Usage

```python
from maverick_crypto.news import CryptoSentimentAnalyzer

analyzer = CryptoSentimentAnalyzer()

# Analyze single headline
result = analyzer.analyze("Bitcoin surges past $100k as ETF demand soars")
print(f"Score: {result.score.value}/5")  # 5 (very bullish)
print(f"Label: {result.score.label}")     # "very bullish"
print(f"Confidence: {result.confidence}") # 0.85
print(f"Keywords: {result.keywords_found}")  # ["surges", "soars"]

# Analyze batch
headlines = [
    "BTC rallies to new highs",
    "Exchange hack causes panic",
    "New update released"
]
batch_result = analyzer.analyze_batch(headlines)
print(f"Overall: {batch_result['overall_label']}")

# Market sentiment from articles
articles = [{"title": "..."}, {"title": "..."}]
sentiment = analyzer.get_market_sentiment(articles)
```

### Sentiment Keywords

#### Bullish Keywords (70+)

**Very Bullish:**

- surge, surges, surging
- soar, soars, soaring
- skyrocket, moon, breakout
- all-time high, ATH
- institutional adoption
- ETF approved/approval

**Bullish:**

- rally, gain, rise, climb
- increase, bullish, positive
- support, recovery, rebound
- partnership, adoption

#### Bearish Keywords (60+)

**Very Bearish:**

- crash, collapse, plunge
- capitulation, liquidation
- hack, exploit, rug pull
- scam, fraud, ban

**Bearish:**

- drop, fall, decline
- dip, correction, pullback
- concern, warning, risk
- regulation, lawsuit

## SentimentScore

Sentiment score enumeration.

::: maverick_crypto.news.SentimentScore
    options:
      show_root_heading: true

### Score Values

| Score | Value | Description |
|-------|-------|-------------|
| VERY_BULLISH | 5 | Extremely positive |
| BULLISH | 4 | Positive |
| NEUTRAL | 3 | No clear direction |
| BEARISH | 2 | Negative |
| VERY_BEARISH | 1 | Extremely negative |

## MCP Tools Reference

| Tool | Description |
|------|-------------|
| `crypto_news` | Get latest crypto news |
| `crypto_news_sentiment` | Analyze news sentiment |
| `crypto_trending_news` | Hot stories |
| `crypto_analyze_headline` | Analyze single headline |
| `crypto_bullish_news` | Positive news filter |
| `crypto_bearish_news` | Negative news filter |

## Example Queries

### Get News

```
User: "What's the latest Bitcoin news?"

→ Returns 20 recent BTC articles with:
  - Title, source, URL
  - Published time
  - Sentiment (bullish/bearish/neutral)
```

### Sentiment Analysis

```
User: "Is the news bullish for crypto?"

→ Returns:
  - Overall sentiment: Bullish
  - Breakdown: 15 bullish, 5 bearish, 10 neutral
  - Top positive keywords
  - Top headlines
```

### Headline Analysis

```
User: "Analyze: SEC approves spot Ethereum ETF"

→ Returns:
  - Score: 5/5 (very bullish)
  - Keywords: ["approved", "ETF"]
  - Confidence: 0.90
```

## API Keys

| Source | API Key | Notes |
|--------|---------|-------|
| CryptoPanic | Optional | Free tier limited |
| RSS Feeds | Not needed | Always available |

### Getting CryptoPanic Key

1. Go to [cryptopanic.com/developers](https://cryptopanic.com/developers/api/)
2. Create free account
3. Get API key
4. Set: `CRYPTOPANIC_API_KEY=your-key`

## Best Practices

### Sentiment Interpretation

- **Don't trade on sentiment alone**: Use as one of many signals
- **Consider source reliability**: Major outlets vs unknown blogs
- **Check recency**: Old news may already be priced in
- **Volume matters**: Many articles amplify signal

### Combining with Technical Analysis

```
User: "Is now a good time to buy ETH?"

→ Maverick combines:
  1. Technical: RSI at 35 (oversold)
  2. News: 60% bullish sentiment
  3. Fear/Greed: 25 (Fear)
  
→ Interpretation: Potential buying opportunity
   but market is fearful. Proceed with caution.
```

