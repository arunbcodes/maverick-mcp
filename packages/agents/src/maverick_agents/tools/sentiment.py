"""
Sentiment analysis tools for news, social media, and market sentiment.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from maverick_agents.personas import InvestorPersona, PersonaAwareTool

logger = logging.getLogger(__name__)


# Protocol for settings dependency injection
@runtime_checkable
class SettingsProtocol(Protocol):
    """Protocol for settings configuration."""

    @property
    def sentiment_news_limit(self) -> int:
        """Number of news articles to analyze."""
        ...

    @property
    def market_movers_gainers_limit(self) -> int:
        """Limit for top gainers."""
        ...

    @property
    def market_movers_losers_limit(self) -> int:
        """Limit for top losers."""
        ...

    @property
    def market_movers_active_limit(self) -> int:
        """Limit for most active stocks."""
        ...


# Protocol for market data provider dependency injection
@runtime_checkable
class MarketDataProviderProtocol(Protocol):
    """Protocol for market data provider."""

    def get_stock_news(self, symbol: str, limit: int = 10) -> dict[str, Any]:
        """Get news articles for a stock."""
        ...

    def get_top_gainers(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top gaining stocks."""
        ...

    def get_top_losers(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top losing stocks."""
        ...

    def get_most_active(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get most active stocks by volume."""
        ...

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get quote for a symbol."""
        ...


class DefaultSettings:
    """Default settings implementation."""

    sentiment_news_limit: int = 20
    market_movers_gainers_limit: int = 10
    market_movers_losers_limit: int = 10
    market_movers_active_limit: int = 10


class SentimentInput(BaseModel):
    """Input for sentiment analysis."""

    symbol: str = Field(description="Stock symbol to analyze")
    days_back: int = Field(default=7, description="Days of history to analyze")


class MarketBreadthInput(BaseModel):
    """Input for market breadth analysis."""

    index: str = Field(default="SPY", description="Market index to analyze")


class NewsSentimentTool(PersonaAwareTool):
    """Analyze news sentiment for stocks."""

    name: str = "analyze_news_sentiment"
    description: str = "Analyze recent news sentiment and its impact on stock price"
    args_schema: type[BaseModel] = SentimentInput  # type: ignore[assignment]

    # Injected dependencies
    _market_provider: MarketDataProviderProtocol | None = None
    _settings: SettingsProtocol | None = None

    def __init__(
        self,
        persona: InvestorPersona | None = None,
        market_provider: MarketDataProviderProtocol | None = None,
        settings: SettingsProtocol | None = None,
    ):
        """Initialize sentiment tool.

        Args:
            persona: Investor persona for formatting
            market_provider: Market data provider (optional)
            settings: Settings configuration (optional)
        """
        super().__init__(persona=persona)
        self._market_provider = market_provider
        self._settings = settings or DefaultSettings()

    def _run(self, symbol: str, days_back: int = 7) -> str:
        """Analyze news sentiment synchronously."""
        try:
            # Get recent news
            news_data: dict[str, Any] = {"articles": []}
            if self._market_provider:
                news_data = self._market_provider.get_stock_news(
                    symbol, limit=self._settings.sentiment_news_limit
                )

            if not news_data or "articles" not in news_data:
                return f"No news data available for {symbol}"

            articles = news_data.get("articles", [])
            if not articles:
                return f"No recent news articles found for {symbol}"

            # Simple sentiment scoring based on keywords
            positive_keywords = [
                "beat",
                "exceed",
                "upgrade",
                "strong",
                "growth",
                "profit",
                "revenue",
                "bullish",
                "buy",
                "outperform",
                "surge",
                "rally",
                "breakthrough",
                "innovation",
                "expansion",
                "record",
            ]
            negative_keywords = [
                "miss",
                "downgrade",
                "weak",
                "loss",
                "decline",
                "bearish",
                "sell",
                "underperform",
                "fall",
                "cut",
                "concern",
                "risk",
                "lawsuit",
                "investigation",
                "recall",
                "bankruptcy",
            ]

            sentiment_scores = []
            analyzed_articles = []

            cutoff_date = datetime.now() - timedelta(days=days_back)

            for article in articles[:20]:  # Analyze top 20 most recent
                title = article.get("title", "").lower()
                description = article.get("description", "").lower()
                published = article.get("publishedAt", "")

                # Skip old articles
                try:
                    pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    if pub_date.replace(tzinfo=None) < cutoff_date:
                        continue
                except Exception:
                    continue

                text = f"{title} {description}"

                # Count keyword occurrences
                positive_count = sum(1 for word in positive_keywords if word in text)
                negative_count = sum(1 for word in negative_keywords if word in text)

                # Calculate sentiment score
                if positive_count + negative_count > 0:
                    score = (positive_count - negative_count) / (
                        positive_count + negative_count
                    )
                else:
                    score = 0

                sentiment_scores.append(score)
                analyzed_articles.append(
                    {
                        "title": article.get("title", ""),
                        "published": published,
                        "sentiment_score": round(score, 2),
                        "source": article.get("source", {}).get("name", "Unknown"),
                    }
                )

            if not sentiment_scores:
                return f"No recent news articles found for {symbol} in the last {days_back} days"

            # Calculate aggregate sentiment
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

            # Determine sentiment category
            if avg_sentiment > 0.2:
                sentiment_category = "Positive"
                sentiment_impact = "Bullish"
            elif avg_sentiment < -0.2:
                sentiment_category = "Negative"
                sentiment_impact = "Bearish"
            else:
                sentiment_category = "Neutral"
                sentiment_impact = "Mixed"

            # Calculate momentum (recent vs older sentiment)
            if len(sentiment_scores) >= 5:
                recent_sentiment = sum(sentiment_scores[:5]) / 5
                older_sentiment = sum(sentiment_scores[5:]) / len(sentiment_scores[5:])
                sentiment_momentum = recent_sentiment - older_sentiment
            else:
                sentiment_momentum = 0

            result: dict[str, Any] = {
                "status": "success",
                "symbol": symbol,
                "sentiment_analysis": {
                    "overall_sentiment": sentiment_category,
                    "sentiment_score": round(avg_sentiment, 3),
                    "sentiment_impact": sentiment_impact,
                    "sentiment_momentum": round(sentiment_momentum, 3),
                    "articles_analyzed": len(analyzed_articles),
                    "analysis_period": f"{days_back} days",
                },
                "recent_articles": analyzed_articles[:5],  # Top 5 most recent
                "sentiment_distribution": {
                    "positive": sum(1 for s in sentiment_scores if s > 0.2),
                    "neutral": sum(1 for s in sentiment_scores if -0.2 <= s <= 0.2),
                    "negative": sum(1 for s in sentiment_scores if s < -0.2),
                },
            }

            # Add trading recommendations based on sentiment and persona
            if self.persona:
                if sentiment_category == "Positive" and sentiment_momentum > 0:
                    if self.persona.name == "Aggressive":
                        result["recommendation"] = "Strong momentum - consider entry"
                    elif self.persona.name == "Conservative":
                        result["recommendation"] = (
                            "Positive sentiment but wait for pullback"
                        )
                    else:
                        result["recommendation"] = (
                            "Favorable sentiment for gradual entry"
                        )
                elif sentiment_category == "Negative":
                    if self.persona.name == "Conservative":
                        result["recommendation"] = "Avoid - negative sentiment"
                    else:
                        result["recommendation"] = "Monitor for reversal signals"

            # Format for persona
            formatted = self.format_for_persona(result)
            return str(formatted)

        except Exception as e:
            logger.error(f"Error analyzing news sentiment for {symbol}: {e}")
            return f"Error analyzing news sentiment: {str(e)}"


class MarketBreadthTool(PersonaAwareTool):
    """Analyze overall market breadth and sentiment."""

    name: str = "analyze_market_breadth"
    description: str = "Analyze market breadth indicators and overall market sentiment"
    args_schema: type[BaseModel] = MarketBreadthInput  # type: ignore[assignment]

    # Injected dependencies
    _market_provider: MarketDataProviderProtocol | None = None
    _settings: SettingsProtocol | None = None

    def __init__(
        self,
        persona: InvestorPersona | None = None,
        market_provider: MarketDataProviderProtocol | None = None,
        settings: SettingsProtocol | None = None,
    ):
        """Initialize market breadth tool.

        Args:
            persona: Investor persona for formatting
            market_provider: Market data provider (required for full functionality)
            settings: Settings configuration (optional)
        """
        super().__init__(persona=persona)
        self._market_provider = market_provider
        self._settings = settings or DefaultSettings()

    def _run(self, index: str = "SPY") -> str:
        """Analyze market breadth synchronously."""
        try:
            if not self._market_provider:
                return "Error: Market data provider not configured"

            # Get market movers
            gainers = {
                "movers": self._market_provider.get_top_gainers(
                    limit=self._settings.market_movers_gainers_limit
                )
            }
            losers = {
                "movers": self._market_provider.get_top_losers(
                    limit=self._settings.market_movers_losers_limit
                )
            }
            most_active = {
                "movers": self._market_provider.get_most_active(
                    limit=self._settings.market_movers_active_limit
                )
            }

            # Calculate breadth metrics
            total_gainers = len(gainers.get("movers", []))
            total_losers = len(losers.get("movers", []))

            if total_gainers + total_losers > 0:
                advance_decline_ratio = total_gainers / (total_gainers + total_losers)
            else:
                advance_decline_ratio = 0.5

            # Calculate average moves
            avg_gain = 0.0
            if gainers.get("movers"):
                gains = [m.get("change_percent", 0) for m in gainers["movers"]]
                avg_gain = sum(gains) / len(gains) if gains else 0

            avg_loss = 0.0
            if losers.get("movers"):
                losses = [abs(m.get("change_percent", 0)) for m in losers["movers"]]
                avg_loss = sum(losses) / len(losses) if losses else 0

            # Determine market sentiment
            if advance_decline_ratio > 0.65:
                market_sentiment = "Bullish"
                strength = "Strong" if advance_decline_ratio > 0.75 else "Moderate"
            elif advance_decline_ratio < 0.35:
                market_sentiment = "Bearish"
                strength = "Strong" if advance_decline_ratio < 0.25 else "Moderate"
            else:
                market_sentiment = "Neutral"
                strength = "Mixed"

            # Get VIX if available (fear gauge)
            vix_data = self._market_provider.get_quote("VIX")
            vix_level = None
            fear_gauge = "Unknown"

            if vix_data and "price" in vix_data:
                vix_level = vix_data["price"]
                if vix_level < 15:
                    fear_gauge = "Low (Complacent)"
                elif vix_level < 20:
                    fear_gauge = "Normal"
                elif vix_level < 30:
                    fear_gauge = "Elevated (Cautious)"
                else:
                    fear_gauge = "High (Fearful)"

            result: dict[str, Any] = {
                "status": "success",
                "market_breadth": {
                    "sentiment": market_sentiment,
                    "strength": strength,
                    "advance_decline_ratio": round(advance_decline_ratio, 3),
                    "gainers": total_gainers,
                    "losers": total_losers,
                    "most_active": most_active,
                    "avg_gain_pct": round(avg_gain, 2),
                    "avg_loss_pct": round(avg_loss, 2),
                },
                "fear_gauge": {
                    "vix_level": round(vix_level, 2) if vix_level else None,
                    "fear_level": fear_gauge,
                },
                "market_leaders": [
                    {
                        "symbol": m.get("symbol"),
                        "change_pct": round(m.get("change_percent", 0), 2),
                        "volume": m.get("volume"),
                    }
                    for m in gainers.get("movers", [])[:5]
                ],
                "market_laggards": [
                    {
                        "symbol": m.get("symbol"),
                        "change_pct": round(m.get("change_percent", 0), 2),
                        "volume": m.get("volume"),
                    }
                    for m in losers.get("movers", [])[:5]
                ],
            }

            # Add persona-specific market interpretation
            if self.persona:
                if (
                    market_sentiment == "Bullish"
                    and self.persona.name == "Conservative"
                ):
                    result["interpretation"] = (
                        "Market is bullish but be cautious of extended moves"
                    )
                elif (
                    market_sentiment == "Bearish" and self.persona.name == "Aggressive"
                ):
                    result["interpretation"] = (
                        "Market weakness presents buying opportunities in oversold stocks"
                    )
                elif market_sentiment == "Neutral":
                    result["interpretation"] = (
                        "Mixed market - focus on individual stock selection"
                    )

            # Format for persona
            formatted = self.format_for_persona(result)
            return str(formatted)

        except Exception as e:
            logger.error(f"Error analyzing market breadth: {e}")
            return f"Error analyzing market breadth: {str(e)}"


class SectorSentimentTool(PersonaAwareTool):
    """Analyze sector rotation and sentiment."""

    name: str = "analyze_sector_sentiment"
    description: str = (
        "Analyze sector rotation patterns and identify leading/lagging sectors"
    )

    # Injected dependencies
    _market_provider: MarketDataProviderProtocol | None = None

    def __init__(
        self,
        persona: InvestorPersona | None = None,
        market_provider: MarketDataProviderProtocol | None = None,
    ):
        """Initialize sector sentiment tool.

        Args:
            persona: Investor persona for formatting
            market_provider: Market data provider (required for full functionality)
        """
        super().__init__(persona=persona)
        self._market_provider = market_provider

    def _run(self) -> str:
        """Analyze sector sentiment synchronously."""
        try:
            # Major sector ETFs
            sectors = {
                "Technology": "XLK",
                "Healthcare": "XLV",
                "Financials": "XLF",
                "Energy": "XLE",
                "Consumer Discretionary": "XLY",
                "Consumer Staples": "XLP",
                "Industrials": "XLI",
                "Materials": "XLB",
                "Real Estate": "XLRE",
                "Utilities": "XLU",
                "Communications": "XLC",
            }

            sector_performance: dict[str, dict[str, Any]] = {}

            for sector_name, etf in sectors.items():
                quote = None
                if self._market_provider:
                    quote = self._market_provider.get_quote(etf)

                if quote and "change_percent" in quote:
                    sector_performance[sector_name] = {
                        "symbol": etf,
                        "change_pct": round(quote["change_percent"], 2),
                        "price": quote.get("price", 0),
                        "volume": quote.get("volume", 0),
                    }

            if not sector_performance:
                return "Error: Unable to fetch sector performance data"

            # Sort sectors by performance
            sorted_sectors = sorted(
                sector_performance.items(),
                key=lambda x: x[1]["change_pct"],
                reverse=True,
            )

            # Identify rotation patterns
            leading_sectors = sorted_sectors[:3]
            lagging_sectors = sorted_sectors[-3:]

            # Determine market regime based on sector leadership
            tech_performance = sector_performance.get("Technology", {}).get(
                "change_pct", 0
            )
            defensive_avg = (
                sector_performance.get("Utilities", {}).get("change_pct", 0)
                + sector_performance.get("Consumer Staples", {}).get("change_pct", 0)
            ) / 2

            if tech_performance > 1 and defensive_avg < 0:
                market_regime = "Risk-On (Growth Leading)"
            elif defensive_avg > 1 and tech_performance < 0:
                market_regime = "Risk-Off (Defensive Leading)"
            else:
                market_regime = "Neutral/Transitioning"

            result: dict[str, Any] = {
                "status": "success",
                "sector_rotation": {
                    "market_regime": market_regime,
                    "leading_sectors": [
                        {"name": name, **data} for name, data in leading_sectors
                    ],
                    "lagging_sectors": [
                        {"name": name, **data} for name, data in lagging_sectors
                    ],
                },
                "all_sectors": dict(sorted_sectors),
                "rotation_signals": self._identify_rotation_signals(sector_performance),
            }

            # Add persona-specific sector recommendations
            if self.persona:
                if self.persona.name == "Conservative":
                    result["recommendations"] = (
                        "Focus on defensive sectors: "
                        + ", ".join(
                            [
                                s
                                for s in ["Utilities", "Consumer Staples", "Healthcare"]
                                if s in sector_performance
                            ]
                        )
                    )
                elif self.persona.name == "Aggressive":
                    result["recommendations"] = (
                        "Target high-momentum sectors: "
                        + ", ".join([name for name, _ in leading_sectors])
                    )

            # Format for persona
            formatted = self.format_for_persona(result)
            return str(formatted)

        except Exception as e:
            logger.error(f"Error analyzing sector sentiment: {e}")
            return f"Error analyzing sector sentiment: {str(e)}"

    def _identify_rotation_signals(
        self, sector_performance: dict[str, dict[str, Any]]
    ) -> list[str]:
        """Identify sector rotation signals."""
        signals = []

        # Check for tech leadership
        tech_perf = sector_performance.get("Technology", {}).get("change_pct", 0)
        if tech_perf > 2:
            signals.append("Strong tech leadership - growth environment")

        # Check for defensive rotation
        defensive_sectors = ["Utilities", "Consumer Staples", "Healthcare"]
        defensive_perfs = [
            sector_performance.get(s, {}).get("change_pct", 0)
            for s in defensive_sectors
        ]
        if all(p > 0 for p in defensive_perfs) and tech_perf < 0:
            signals.append("Defensive rotation - risk-off environment")

        # Check for energy/materials strength
        cyclical_strength = (
            sector_performance.get("Energy", {}).get("change_pct", 0)
            + sector_performance.get("Materials", {}).get("change_pct", 0)
        ) / 2
        if cyclical_strength > 2:
            signals.append("Cyclical strength - inflation/growth theme")

        return signals
