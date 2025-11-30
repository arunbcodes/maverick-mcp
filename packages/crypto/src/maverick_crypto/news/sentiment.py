"""
Crypto News Sentiment Analysis.

Provides sentiment analysis for cryptocurrency news using
keyword-based analysis and LLM integration.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SentimentScore(Enum):
    """Sentiment score levels."""
    VERY_BULLISH = 5
    BULLISH = 4
    NEUTRAL = 3
    BEARISH = 2
    VERY_BEARISH = 1
    
    @property
    def label(self) -> str:
        """Get human-readable label."""
        return self.name.lower().replace("_", " ")


@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    
    score: SentimentScore
    confidence: float  # 0-1
    keywords_found: list[str]
    explanation: str
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "score": self.score.value,
            "label": self.score.label,
            "confidence": round(self.confidence, 2),
            "keywords_found": self.keywords_found,
            "explanation": self.explanation,
        }


class CryptoSentimentAnalyzer:
    """
    Analyzes sentiment of crypto news articles.
    
    Uses keyword-based analysis with crypto-specific terminology.
    Can be extended with LLM integration for more nuanced analysis.
    
    Example:
        >>> analyzer = CryptoSentimentAnalyzer()
        >>> result = analyzer.analyze("Bitcoin surges past $100k as ETF demand soars")
        >>> print(f"Sentiment: {result.score.label}")
    """
    
    # Crypto-specific bullish keywords (include verb forms)
    BULLISH_KEYWORDS = {
        # Strong bullish
        "very_bullish": [
            "surge", "surges", "surging", "surged",
            "soar", "soars", "soaring", "soared",
            "skyrocket", "skyrockets", "skyrocketing",
            "moon", "mooning", "breakout", "breaks out",
            "all-time high", "ath", "parabolic", "explosive",
            "institutional adoption", "mass adoption", "bullrun", "bull run",
            "accumulation", "whale buying", "etf approved", "etf approval",
        ],
        # Moderate bullish
        "bullish": [
            "rally", "rallies", "rallying", "rallied",
            "gain", "gains", "gaining", "gained",
            "rise", "rises", "rising", "rose",
            "climb", "climbs", "climbing", "climbed",
            "increase", "increases", "increasing", "increased",
            "bullish", "positive", "optimistic", "uptrend",
            "support", "recovery", "rebound", "bounce", "bounces",
            "inflow", "inflows", "buying pressure", "accumulating",
            "partnership", "adoption", "integration",
            "upgrade", "launch", "milestone", "breaks", "breaking",
        ],
    }
    
    # Crypto-specific bearish keywords (include verb forms)
    BEARISH_KEYWORDS = {
        # Strong bearish
        "very_bearish": [
            "crash", "crashes", "crashing", "crashed",
            "collapse", "collapses", "collapsing", "collapsed",
            "plunge", "plunges", "plunging", "plunged",
            "plummet", "plummets", "plummeting", "plummeted",
            "tank", "tanks", "tanking", "tanked",
            "capitulation", "liquidation", "liquidated",
            "hack", "hacked", "exploit", "exploited",
            "rug pull", "rugged", "scam", "fraud", "ponzi",
            "ban", "banned", "crackdown", "shutdown", "arrest",
            "bankrupt", "bankruptcy", "insolvent", "default",
        ],
        # Moderate bearish
        "bearish": [
            "drop", "drops", "dropping", "dropped",
            "fall", "falls", "falling", "fell",
            "decline", "declines", "declining", "declined",
            "decrease", "decreases", "decreasing", "decreased",
            "dip", "dips", "dipping", "dipped",
            "bearish", "negative", "pessimistic", "downtrend",
            "resistance", "correction", "pullback", "sell-off", "selloff",
            "outflow", "outflows", "selling pressure", "distribution",
            "concern", "concerns", "warning", "risk", "uncertainty",
            "regulation", "lawsuit", "investigation", "probe",
        ],
    }
    
    # Neutral/important keywords
    NEUTRAL_KEYWORDS = [
        "update", "announce", "report", "analysis",
        "market", "trading", "volume", "price",
        "blockchain", "crypto", "bitcoin", "ethereum",
    ]
    
    def __init__(self):
        """Initialize sentiment analyzer."""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for keyword matching."""
        self.patterns = {
            "very_bullish": [
                re.compile(rf"\b{kw}\b", re.IGNORECASE)
                for kw in self.BULLISH_KEYWORDS["very_bullish"]
            ],
            "bullish": [
                re.compile(rf"\b{kw}\b", re.IGNORECASE)
                for kw in self.BULLISH_KEYWORDS["bullish"]
            ],
            "very_bearish": [
                re.compile(rf"\b{kw}\b", re.IGNORECASE)
                for kw in self.BEARISH_KEYWORDS["very_bearish"]
            ],
            "bearish": [
                re.compile(rf"\b{kw}\b", re.IGNORECASE)
                for kw in self.BEARISH_KEYWORDS["bearish"]
            ],
        }
    
    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze (article title/content)
            
        Returns:
            SentimentResult with score and analysis
        """
        if not text:
            return SentimentResult(
                score=SentimentScore.NEUTRAL,
                confidence=0.0,
                keywords_found=[],
                explanation="No text provided",
            )
        
        # Find matching keywords
        matches = {
            "very_bullish": [],
            "bullish": [],
            "very_bearish": [],
            "bearish": [],
        }
        
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    matches[category].append(pattern.pattern.replace("\\b", ""))
        
        # Calculate score
        very_bullish_count = len(matches["very_bullish"])
        bullish_count = len(matches["bullish"])
        very_bearish_count = len(matches["very_bearish"])
        bearish_count = len(matches["bearish"])
        
        # Weighted scoring
        bullish_score = very_bullish_count * 2 + bullish_count
        bearish_score = very_bearish_count * 2 + bearish_count
        
        total_keywords = very_bullish_count + bullish_count + very_bearish_count + bearish_count
        
        # Determine sentiment
        if bullish_score == 0 and bearish_score == 0:
            score = SentimentScore.NEUTRAL
            confidence = 0.3
            explanation = "No strong sentiment indicators found"
        elif bullish_score > bearish_score * 2:
            if very_bullish_count > 0:
                score = SentimentScore.VERY_BULLISH
                confidence = min(0.9, 0.5 + very_bullish_count * 0.1)
            else:
                score = SentimentScore.BULLISH
                confidence = min(0.8, 0.4 + bullish_count * 0.1)
            explanation = f"Found {bullish_score} bullish indicators"
        elif bearish_score > bullish_score * 2:
            if very_bearish_count > 0:
                score = SentimentScore.VERY_BEARISH
                confidence = min(0.9, 0.5 + very_bearish_count * 0.1)
            else:
                score = SentimentScore.BEARISH
                confidence = min(0.8, 0.4 + bearish_count * 0.1)
            explanation = f"Found {bearish_score} bearish indicators"
        elif bullish_score > bearish_score:
            score = SentimentScore.BULLISH
            confidence = 0.5 + (bullish_score - bearish_score) * 0.05
            explanation = f"Slightly bullish ({bullish_score} vs {bearish_score})"
        elif bearish_score > bullish_score:
            score = SentimentScore.BEARISH
            confidence = 0.5 + (bearish_score - bullish_score) * 0.05
            explanation = f"Slightly bearish ({bearish_score} vs {bullish_score})"
        else:
            score = SentimentScore.NEUTRAL
            confidence = 0.5
            explanation = "Mixed signals, leaning neutral"
        
        # Combine all found keywords
        all_keywords = (
            matches["very_bullish"] + matches["bullish"] +
            matches["very_bearish"] + matches["bearish"]
        )
        
        return SentimentResult(
            score=score,
            confidence=min(confidence, 1.0),
            keywords_found=all_keywords[:10],  # Limit to 10
            explanation=explanation,
        )
    
    def analyze_batch(self, texts: list[str]) -> dict[str, Any]:
        """
        Analyze sentiment of multiple texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            Aggregate sentiment analysis
        """
        if not texts:
            return {
                "overall_score": SentimentScore.NEUTRAL.value,
                "overall_label": "neutral",
                "average_confidence": 0.0,
                "distribution": {},
                "analyzed_count": 0,
            }
        
        results = [self.analyze(text) for text in texts]
        
        # Calculate distribution
        distribution = {
            "very_bullish": 0,
            "bullish": 0,
            "neutral": 0,
            "bearish": 0,
            "very_bearish": 0,
        }
        
        total_score = 0
        total_confidence = 0
        
        for result in results:
            label = result.score.label.replace(" ", "_")
            distribution[label] = distribution.get(label, 0) + 1
            total_score += result.score.value
            total_confidence += result.confidence
        
        avg_score = total_score / len(results)
        avg_confidence = total_confidence / len(results)
        
        # Map average score to sentiment
        if avg_score >= 4.5:
            overall = SentimentScore.VERY_BULLISH
        elif avg_score >= 3.5:
            overall = SentimentScore.BULLISH
        elif avg_score >= 2.5:
            overall = SentimentScore.NEUTRAL
        elif avg_score >= 1.5:
            overall = SentimentScore.BEARISH
        else:
            overall = SentimentScore.VERY_BEARISH
        
        return {
            "overall_score": overall.value,
            "overall_label": overall.label,
            "average_score": round(avg_score, 2),
            "average_confidence": round(avg_confidence, 2),
            "distribution": distribution,
            "analyzed_count": len(results),
            "timestamp": datetime.now().isoformat(),
        }
    
    def get_market_sentiment(
        self,
        articles: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Analyze market sentiment from news articles.
        
        Args:
            articles: List of article dictionaries with 'title' key
            
        Returns:
            Market sentiment analysis
        """
        titles = [a.get("title", "") for a in articles if a.get("title")]
        
        if not titles:
            return {
                "sentiment": "neutral",
                "score": 3,
                "confidence": 0.0,
                "article_count": 0,
                "interpretation": "No articles to analyze",
            }
        
        batch_result = self.analyze_batch(titles)
        
        # Generate interpretation
        if batch_result["overall_label"] == "very bullish":
            interpretation = "Strong positive sentiment - market optimism high"
        elif batch_result["overall_label"] == "bullish":
            interpretation = "Positive sentiment - favorable news coverage"
        elif batch_result["overall_label"] == "bearish":
            interpretation = "Negative sentiment - concerns in news coverage"
        elif batch_result["overall_label"] == "very bearish":
            interpretation = "Strong negative sentiment - significant concerns"
        else:
            interpretation = "Mixed sentiment - no clear market direction"
        
        return {
            "sentiment": batch_result["overall_label"],
            "score": batch_result["overall_score"],
            "average_score": batch_result["average_score"],
            "confidence": batch_result["average_confidence"],
            "article_count": batch_result["analyzed_count"],
            "distribution": batch_result["distribution"],
            "interpretation": interpretation,
            "timestamp": batch_result["timestamp"],
        }

