"""
Maverick Crypto News Module.

Provides cryptocurrency news aggregation and sentiment analysis.

Data Sources:
    - CryptoPanic: Free crypto news aggregator with community sentiment
    - NewsData.io: General news API with crypto coverage
    - RSS feeds from major crypto publications
"""

from maverick_crypto.news.providers import (
    CryptoPanicProvider,
    NewsAggregator,
)
from maverick_crypto.news.sentiment import (
    CryptoSentimentAnalyzer,
    SentimentScore,
)

__all__ = [
    "CryptoPanicProvider",
    "NewsAggregator",
    "CryptoSentimentAnalyzer",
    "SentimentScore",
]

