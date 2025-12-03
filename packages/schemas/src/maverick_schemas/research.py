"""
Research and sentiment analysis models.

Models for AI-powered research, news sentiment, and earnings analysis.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import Field

from maverick_schemas.base import MaverickBaseModel, SentimentScore


class ResearchDepth(str, Enum):
    """Research depth levels."""
    
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    EXHAUSTIVE = "exhaustive"


class SentimentAnalysis(MaverickBaseModel):
    """Sentiment analysis result."""
    
    ticker: str = Field(description="Stock ticker symbol")
    
    # Overall sentiment
    sentiment: SentimentScore = Field(description="Overall sentiment")
    sentiment_score: Decimal = Field(ge=-1, le=1, description="Sentiment score (-1 to 1)")
    confidence: Decimal = Field(ge=0, le=1, description="Confidence level")
    
    # Breakdown
    positive_signals: list[str] = Field(default_factory=list, description="Positive indicators")
    negative_signals: list[str] = Field(default_factory=list, description="Negative indicators")
    
    # News-based sentiment
    news_sentiment: Decimal | None = Field(default=None, description="News sentiment score")
    news_count: int = Field(default=0, description="Number of news articles analyzed")
    
    # Social sentiment (if available)
    social_sentiment: Decimal | None = Field(default=None, description="Social media sentiment")
    
    # Analyst sentiment
    analyst_rating: str | None = Field(default=None, description="Consensus analyst rating")
    price_target: Decimal | None = Field(default=None, description="Average price target")
    
    # Timeframe
    timeframe: str = Field(default="7d", description="Analysis timeframe")
    analyzed_at: datetime = Field(description="Analysis timestamp")


class NewsArticle(MaverickBaseModel):
    """News article with sentiment."""
    
    title: str = Field(description="Article title")
    source: str = Field(description="News source")
    url: str | None = Field(default=None, description="Article URL")
    published_at: datetime = Field(description="Publication date")
    
    # Sentiment
    sentiment: SentimentScore = Field(description="Article sentiment")
    sentiment_score: Decimal = Field(description="Sentiment score")
    
    # Summary
    summary: str | None = Field(default=None, description="Article summary")
    
    # Relevance
    relevance_score: Decimal = Field(default=Decimal("1.0"), description="Relevance to ticker")


class ResearchQuery(MaverickBaseModel):
    """Request model for AI research."""
    
    topic: str = Field(description="Research topic or stock symbol")
    
    # Options
    depth: ResearchDepth = Field(default=ResearchDepth.STANDARD, description="Research depth")
    focus_areas: list[str] | None = Field(
        default=None,
        description="Specific areas to focus on"
    )
    timeframe: str = Field(default="30d", description="Timeframe for research")
    
    # Persona (affects analysis perspective)
    persona: str = Field(default="moderate", description="Investor persona")
    
    # Output options
    max_sources: int = Field(default=10, ge=1, le=50, description="Maximum sources to analyze")


class ResearchInsight(MaverickBaseModel):
    """Individual research insight."""
    
    title: str = Field(description="Insight title")
    content: str = Field(description="Insight content")
    category: str = Field(description="Insight category")
    importance: str = Field(description="Importance: high, medium, low")
    
    # Sources
    sources: list[str] = Field(default_factory=list, description="Source URLs")


class ResearchResult(MaverickBaseModel):
    """Complete research result."""
    
    query: str = Field(description="Original query")
    
    # Executive summary
    summary: str = Field(description="Executive summary")
    
    # Key insights
    insights: list[ResearchInsight] = Field(default_factory=list, description="Key insights")
    
    # Sentiment
    overall_sentiment: SentimentScore = Field(description="Overall sentiment")
    sentiment_rationale: str | None = Field(default=None, description="Sentiment explanation")
    
    # Recommendations (persona-adjusted)
    recommendations: list[str] = Field(default_factory=list, description="Recommendations")
    risk_factors: list[str] = Field(default_factory=list, description="Risk factors")
    
    # Sources analyzed
    sources_analyzed: int = Field(description="Number of sources analyzed")
    source_urls: list[str] = Field(default_factory=list, description="Source URLs")
    
    # Metadata
    research_depth: ResearchDepth = Field(description="Research depth used")
    persona: str = Field(description="Investor persona used")
    execution_time_ms: int = Field(description="Research execution time")
    completed_at: datetime = Field(description="Completion timestamp")


class EarningsTranscript(MaverickBaseModel):
    """Earnings call transcript."""
    
    ticker: str = Field(description="Stock ticker")
    quarter: str = Field(description="Quarter (Q1, Q2, Q3, Q4)")
    fiscal_year: int = Field(description="Fiscal year")
    
    # Transcript
    transcript_text: str | None = Field(default=None, description="Full transcript")
    word_count: int = Field(default=0, description="Transcript word count")
    
    # Metadata
    call_date: datetime | None = Field(default=None, description="Earnings call date")
    source: str | None = Field(default=None, description="Transcript source")


class EarningsSummary(MaverickBaseModel):
    """AI-generated earnings call summary."""
    
    ticker: str = Field(description="Stock ticker")
    quarter: str = Field(description="Quarter")
    fiscal_year: int = Field(description="Fiscal year")
    
    # Summary sections
    executive_summary: str = Field(description="Executive summary")
    key_metrics: dict[str, str] = Field(default_factory=dict, description="Key financial metrics")
    business_highlights: list[str] = Field(default_factory=list, description="Business highlights")
    management_guidance: str | None = Field(default=None, description="Forward guidance")
    
    # Sentiment
    sentiment: SentimentScore = Field(description="Overall sentiment")
    management_tone: str = Field(description="Management tone: confident, cautious, defensive")
    
    # Risks and opportunities
    key_risks: list[str] = Field(default_factory=list, description="Identified risks")
    opportunities: list[str] = Field(default_factory=list, description="Growth opportunities")
    
    # Q&A insights
    analyst_concerns: list[str] = Field(default_factory=list, description="Key analyst concerns")


__all__ = [
    "ResearchDepth",
    "SentimentAnalysis",
    "NewsArticle",
    "ResearchQuery",
    "ResearchInsight",
    "ResearchResult",
    "EarningsTranscript",
    "EarningsSummary",
]

