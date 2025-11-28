"""
News article model for storing financial news with sentiment analysis.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Session

from maverick_data.models.base import Base, TimestampMixin


class NewsArticle(Base, TimestampMixin):
    """
    Model for storing financial news articles.

    Stores news articles from various Indian financial news sources
    (MoneyControl, Economic Times, LiveMint, Business Standard) with
    sentiment analysis and metadata for historical tracking.
    """

    __tablename__ = "mcp_news_articles"
    __table_args__ = (
        UniqueConstraint("url", name="mcp_news_article_url_unique"),
        Index("mcp_news_article_symbol_date_idx", "symbol", "published_date"),
        Index("mcp_news_article_source_idx", "source"),
        Index("mcp_news_article_sentiment_idx", "sentiment"),
        Index("mcp_news_article_published_idx", "published_date"),
        Index("mcp_news_article_symbol_sentiment_idx", "symbol", "sentiment"),
    )

    article_id = Column(Uuid, primary_key=True, default=uuid.uuid4)

    # Article metadata
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    source = Column(String(100), nullable=False, index=True)
    published_date = Column(DateTime(timezone=True), nullable=False, index=True)

    # Content
    summary = Column(Text)
    content = Column(Text)

    # Stock association
    symbol = Column(String(20), index=True)
    company_name = Column(String(255))

    # Sentiment analysis
    sentiment = Column(String(20), index=True)
    sentiment_score = Column(Numeric(5, 4))
    confidence = Column(Numeric(5, 4))

    # Classification
    category = Column(String(100))
    keywords = Column(JSON)
    entities = Column(JSON)

    # Engagement metrics
    view_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<NewsArticle(id={self.article_id}, title='{self.title[:50]}...', source={self.source}, sentiment={self.sentiment})>"

    @classmethod
    def store_article(
        cls,
        session: Session,
        title: str,
        url: str,
        source: str,
        published_date: datetime,
        summary: str | None = None,
        content: str | None = None,
        symbol: str | None = None,
        sentiment: str | None = None,
        sentiment_score: float | None = None,
        **kwargs,
    ) -> NewsArticle:
        """Store or update a news article in the database."""
        existing = session.query(cls).filter_by(url=url).first()

        if existing:
            existing.title = title
            existing.summary = summary
            existing.content = content
            existing.symbol = symbol
            existing.sentiment = sentiment
            existing.sentiment_score = sentiment_score
            existing.updated_at = datetime.now(UTC)

            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)

            session.commit()
            return existing
        else:
            new_article = cls(
                title=title,
                url=url,
                source=source,
                published_date=published_date,
                summary=summary,
                content=content,
                symbol=symbol,
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                **kwargs,
            )
            session.add(new_article)
            session.commit()
            return new_article

    @classmethod
    def get_recent_articles(
        cls,
        session: Session,
        symbol: str | None = None,
        source: str | None = None,
        days_back: int = 7,
        limit: int = 50,
    ) -> Sequence[NewsArticle]:
        """Get recent news articles."""
        cutoff_date = datetime.now(UTC) - timedelta(days=days_back)

        query = session.query(cls).filter(cls.published_date >= cutoff_date)

        if symbol:
            query = query.filter(cls.symbol == symbol.upper())

        if source:
            query = query.filter(cls.source == source.lower())

        return query.order_by(cls.published_date.desc()).limit(limit).all()

    @classmethod
    def get_sentiment_summary(
        cls, session: Session, symbol: str, days_back: int = 7
    ) -> dict:
        """Get sentiment summary for a stock."""
        cutoff_date = datetime.now(UTC) - timedelta(days=days_back)

        articles = (
            session.query(cls)
            .filter(
                cls.symbol == symbol.upper(),
                cls.published_date >= cutoff_date,
                cls.sentiment.isnot(None),
            )
            .all()
        )

        if not articles:
            return {
                "total_articles": 0,
                "bullish": 0,
                "bearish": 0,
                "neutral": 0,
                "overall_sentiment": "neutral",
                "average_score": 0.0,
            }

        sentiment_counts = {
            "bullish": sum(1 for a in articles if a.sentiment == "bullish"),
            "bearish": sum(1 for a in articles if a.sentiment == "bearish"),
            "neutral": sum(1 for a in articles if a.sentiment == "neutral"),
        }

        scores = [
            float(a.sentiment_score) for a in articles if a.sentiment_score is not None
        ]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        if sentiment_counts["bullish"] > sentiment_counts["bearish"]:
            overall = "bullish"
        elif sentiment_counts["bearish"] > sentiment_counts["bullish"]:
            overall = "bearish"
        else:
            overall = "neutral"

        return {
            "total_articles": len(articles),
            "bullish": sentiment_counts["bullish"],
            "bearish": sentiment_counts["bearish"],
            "neutral": sentiment_counts["neutral"],
            "overall_sentiment": overall,
            "average_score": round(avg_score, 4),
        }

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "article_id": str(self.article_id),
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "published_date": (
                self.published_date.isoformat() if self.published_date else None
            ),
            "summary": self.summary,
            "symbol": self.symbol,
            "company_name": self.company_name,
            "sentiment": self.sentiment,
            "sentiment_score": (
                float(self.sentiment_score) if self.sentiment_score else None
            ),
            "confidence": float(self.confidence) if self.confidence else None,
            "category": self.category,
            "keywords": self.keywords,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
