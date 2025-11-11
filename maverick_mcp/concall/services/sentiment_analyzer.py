"""
Conference Call Sentiment Analysis Service.

Single Responsibility: Analyze sentiment and tone from earnings call transcripts.
Open/Closed: Extensible via prompt templates and scoring algorithms.
Liskov Substitution: Compatible with any LLM provider.
Interface Segregation: Focused API for sentiment analysis only.
Dependency Inversion: Depends on abstractions (LLM provider).

Enhanced with multi-tier caching:
    - L1: Redis/In-memory cache (milliseconds)
    - L2: Database cache (seconds)
    - L3: AI sentiment analysis (expensive - minutes)
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from maverick_mcp.concall.cache import ConcallCacheService
from maverick_mcp.concall.models import ConferenceCall
from maverick_mcp.data.models import get_session
from maverick_mcp.providers.openrouter_provider import OpenRouterProvider, TaskType

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Analyze sentiment and tone from conference call transcripts.

    Provides multi-dimensional sentiment analysis including:
    - Overall sentiment (bullish/bearish scale)
    - Management tone (confident/cautious/defensive)
    - Forward outlook sentiment
    - Risk sentiment
    - Key signal detection (positive/negative phrases)

    Design Philosophy:
        - Fast: Uses cost-effective models for speed
        - Multi-dimensional: Beyond simple positive/negative
        - Context-aware: Considers industry and market conditions
        - Confidence-scored: Provides reliability metrics

    Attributes:
        openrouter: OpenRouter provider for LLM access
        save_to_db: Whether to cache results in database

    Example:
        >>> analyzer = SentimentAnalyzer()
        >>>
        >>> # Analyze sentiment
        >>> sentiment = await analyzer.analyze_sentiment(
        ...     ticker="RELIANCE.NS",
        ...     quarter="Q1",
        ...     fiscal_year=2025,
        ...     transcript_text="..."
        ... )
        >>> print(sentiment["overall_sentiment"])
        >>> print(sentiment["confidence_score"])
    """

    # Sentiment scoring scale
    SENTIMENT_SCALE = {
        "very_bullish": 5,
        "bullish": 4,
        "neutral": 3,
        "bearish": 2,
        "very_bearish": 1,
    }

    # Tone categories
    TONE_CATEGORIES = {
        "confident": "Management expresses high confidence and certainty",
        "optimistic": "Positive outlook with measured expectations",
        "cautious": "Careful language with hedging and qualifications",
        "defensive": "Responding to concerns or defending performance",
        "uncertain": "Lack of clarity or commitment to guidance",
    }

    def __init__(
        self,
        openrouter_api_key: str | None = None,
        save_to_db: bool = True,
        cache_service: ConcallCacheService | None = None,
    ):
        """
        Initialize sentiment analyzer.

        Args:
            openrouter_api_key: OpenRouter API key (defaults to env var)
            save_to_db: Whether to cache results in database
            cache_service: Cache service instance (default: auto-created)
        """
        self.openrouter = OpenRouterProvider(openrouter_api_key)
        self.save_to_db = save_to_db

        # Initialize L1 cache (Redis/in-memory)
        self.cache_service = cache_service or ConcallCacheService()
        logger.info("SentimentAnalyzer initialized with caching enabled")

    async def analyze_sentiment(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        transcript_text: str | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Analyze sentiment from conference call transcript.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year
            transcript_text: Transcript content (if None, fetch from database)
            use_cache: Use cached results if available

        Returns:
            dict: Comprehensive sentiment analysis

        Example:
            >>> sentiment = await analyzer.analyze_sentiment(
            ...     "RELIANCE.NS", "Q1", 2025
            ... )
            >>> print(f"Sentiment: {sentiment['overall_sentiment']}")
            >>> print(f"Confidence: {sentiment['confidence_score']}")
            >>> print(f"Management Tone: {sentiment['management_tone']}")
        """
        ticker = ticker.upper()
        quarter = quarter.upper()

        # Step 1: Check L1 cache (Redis/in-memory - fastest)
        if use_cache:
            l1_cached = await self.cache_service.get_sentiment(ticker, quarter, fiscal_year)
            if l1_cached:
                logger.info(
                    f"[L1 HIT] Retrieved sentiment for {ticker} {quarter} FY{fiscal_year} from Redis/memory cache"
                )
                return l1_cached.get("sentiment")

        # Step 2: Check L2 cache (database - slower but persistent)
        if use_cache:
            l2_cached = self._get_from_cache(ticker, quarter, fiscal_year)
            if l2_cached:
                logger.info(
                    f"[L2 HIT] Retrieved sentiment for {ticker} {quarter} FY{fiscal_year} from database"
                )
                # Populate L1 cache for future requests
                await self.cache_service.cache_sentiment(
                    ticker=ticker,
                    quarter=quarter,
                    fiscal_year=fiscal_year,
                    sentiment_data=l2_cached,
                )
                return l2_cached

        # Step 3: Get transcript (from L2 cache or parameter)
        if transcript_text is None:
            transcript_text = self._get_transcript_from_db(ticker, quarter, fiscal_year)
            if not transcript_text:
                raise ValueError(
                    f"No transcript found for {ticker} {quarter} FY{fiscal_year}"
                )

        logger.info(f"Analyzing sentiment for {ticker} {quarter} FY{fiscal_year}")

        # Step 4: Generate sentiment analysis (expensive AI operation)
        sentiment = await self._generate_sentiment_analysis(
            ticker=ticker,
            quarter=quarter,
            fiscal_year=fiscal_year,
            transcript_text=transcript_text,
        )

        # Step 5: Save to L2 cache (database)
        if self.save_to_db:
            self._save_to_db(ticker, quarter, fiscal_year, sentiment)

        # Step 6: Populate L1 cache (Redis/in-memory)
        if use_cache:
            await self.cache_service.cache_sentiment(
                ticker=ticker,
                quarter=quarter,
                fiscal_year=fiscal_year,
                sentiment_data=sentiment,
            )

        logger.info(
            f"[L3 GENERATED] Successfully analyzed sentiment for {ticker} {quarter} FY{fiscal_year}"
        )
        return sentiment

    async def _generate_sentiment_analysis(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        transcript_text: str,
    ) -> dict[str, Any]:
        """
        Generate sentiment analysis using LLM.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year
            transcript_text: Transcript content

        Returns:
            dict: Sentiment analysis results
        """
        # Build sentiment analysis prompt
        prompt = self._build_sentiment_prompt(
            ticker=ticker,
            quarter=quarter,
            fiscal_year=fiscal_year,
            transcript_text=transcript_text,
        )

        # Get fast, cost-effective LLM for sentiment analysis
        llm = self.openrouter.get_llm(
            task_type=TaskType.SENTIMENT_ANALYSIS,
            prefer_cheap=True,
            temperature=0.2,  # Low temperature for consistent scoring
            max_tokens=2000,
        )

        # Generate analysis
        response = await llm.ainvoke(prompt)

        # Parse JSON response
        try:
            sentiment_data = json.loads(response.content)
        except json.JSONDecodeError:
            logger.error("Failed to parse sentiment analysis JSON")
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response.content, re.DOTALL)
            if json_match:
                sentiment_data = json.loads(json_match.group(1))
            else:
                raise ValueError("Invalid JSON response from sentiment analysis")

        # Add metadata
        sentiment_data["ticker"] = ticker
        sentiment_data["quarter"] = quarter
        sentiment_data["fiscal_year"] = fiscal_year

        # Convert sentiment to numeric score
        sentiment_data["sentiment_score"] = self.SENTIMENT_SCALE.get(
            sentiment_data.get("overall_sentiment", "neutral"), 3
        )

        return sentiment_data

    def _build_sentiment_prompt(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        transcript_text: str,
    ) -> str:
        """
        Build sentiment analysis prompt.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year
            transcript_text: Transcript content

        Returns:
            str: Formatted prompt
        """
        # Truncate transcript if too long (keep first 80% for context)
        max_length = 15000
        if len(transcript_text) > max_length:
            transcript_text = transcript_text[:max_length] + "\n\n[Transcript truncated for analysis]"

        return f"""You are a financial sentiment analysis expert. Analyze the earnings call transcript and provide a comprehensive sentiment assessment.

**COMPANY INFORMATION:**
Ticker: {ticker}
Quarter: {quarter}
Fiscal Year: {fiscal_year}

**TRANSCRIPT:**
{transcript_text}

**ANALYSIS INSTRUCTIONS:**

Provide a JSON response with the following structure:

{{
    "overall_sentiment": "<very_bullish|bullish|neutral|bearish|very_bearish>",
    "confidence_score": <0.0 to 1.0>,
    "management_tone": "<confident|optimistic|cautious|defensive|uncertain>",
    "outlook_sentiment": "<positive|neutral|negative>",
    "risk_sentiment": "<low_risk|moderate_risk|high_risk>",
    "key_positive_signals": ["signal1", "signal2", ...],
    "key_negative_signals": ["signal1", "signal2", ...],
    "hedge_words_count": <integer>,
    "certainty_indicators": ["indicator1", "indicator2", ...],
    "sentiment_rationale": "Brief explanation of overall sentiment assessment",
    "tone_rationale": "Brief explanation of management tone assessment"
}}

**SCORING GUIDELINES:**

1. **Overall Sentiment**: Consider business performance, guidance, market conditions, management confidence
   - very_bullish: Exceptional results, strong guidance, highly confident management
   - bullish: Good results, positive guidance, confident tone
   - neutral: Mixed results, cautious guidance, balanced tone
   - bearish: Weak results, lowered guidance, defensive tone
   - very_bearish: Poor results, no guidance, uncertain management

2. **Confidence Score**: How confident are you in the sentiment assessment (0.0 = very uncertain, 1.0 = very certain)

3. **Management Tone**: Overall communication style and confidence level

4. **Outlook Sentiment**: Forward-looking guidance and expectations

5. **Risk Sentiment**: Perceived risk level based on discussed challenges and uncertainties

6. **Key Signals**: Specific phrases, metrics, or statements that indicate positive/negative sentiment

7. **Hedge Words**: Count of qualifying language (e.g., "may", "could", "possibly", "uncertain")

8. **Certainty Indicators**: Phrases showing management confidence (e.g., "we will", "confident", "committed")

**RESPONSE FORMAT:**
Return ONLY the JSON object, no additional text.
"""

    def _get_from_cache(
        self, ticker: str, quarter: str, fiscal_year: int
    ) -> dict[str, Any] | None:
        """
        Get cached sentiment from database.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year

        Returns:
            dict: Cached sentiment or None
        """
        try:
            session = get_session()
            call = (
                session.query(ConferenceCall)
                .filter(
                    ConferenceCall.ticker == ticker,
                    ConferenceCall.quarter == quarter,
                    ConferenceCall.fiscal_year == fiscal_year,
                    ConferenceCall.sentiment_data.isnot(None),
                )
                .first()
            )

            if call and call.sentiment_data:
                return call.sentiment_data

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve cached sentiment: {e}")
            return None
        finally:
            session.close()

    def _save_to_db(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        sentiment_data: dict[str, Any],
    ) -> None:
        """
        Save sentiment to database.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year
            sentiment_data: Sentiment analysis results
        """
        try:
            session = get_session()
            call = (
                session.query(ConferenceCall)
                .filter(
                    ConferenceCall.ticker == ticker,
                    ConferenceCall.quarter == quarter,
                    ConferenceCall.fiscal_year == fiscal_year,
                )
                .first()
            )

            if call:
                call.sentiment_data = sentiment_data
                session.commit()
                logger.info(f"Saved sentiment to database for {ticker} {quarter} FY{fiscal_year}")
            else:
                logger.warning(
                    f"Conference call not found in database: {ticker} {quarter} FY{fiscal_year}"
                )

        except Exception as e:
            logger.error(f"Failed to save sentiment to database: {e}")
            session.rollback()
        finally:
            session.close()

    def _get_transcript_from_db(
        self, ticker: str, quarter: str, fiscal_year: int
    ) -> str | None:
        """
        Retrieve transcript from database.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year

        Returns:
            str: Transcript text or None
        """
        try:
            session = get_session()
            call = (
                session.query(ConferenceCall)
                .filter(
                    ConferenceCall.ticker == ticker,
                    ConferenceCall.quarter == quarter,
                    ConferenceCall.fiscal_year == fiscal_year,
                    ConferenceCall.transcript_text.isnot(None),
                )
                .first()
            )

            if call:
                return call.transcript_text

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve transcript from database: {e}")
            return None
        finally:
            session.close()

    async def compare_sentiment(
        self,
        ticker: str,
        quarters: list[tuple[str, int]],
    ) -> dict[str, Any]:
        """
        Compare sentiment across multiple quarters.

        Args:
            ticker: Stock symbol
            quarters: List of (quarter, fiscal_year) tuples

        Returns:
            dict: Comparative sentiment analysis

        Example:
            >>> comparison = await analyzer.compare_sentiment(
            ...     "RELIANCE.NS",
            ...     [("Q4", 2024), ("Q1", 2025)]
            ... )
            >>> print(comparison["sentiment_trend"])
        """
        ticker = ticker.upper()

        sentiments = []
        for quarter, fiscal_year in quarters:
            try:
                sentiment = await self.analyze_sentiment(
                    ticker=ticker,
                    quarter=quarter,
                    fiscal_year=fiscal_year,
                    use_cache=True,
                )
                sentiments.append(sentiment)
            except Exception as e:
                logger.warning(f"Failed to analyze {ticker} {quarter} FY{fiscal_year}: {e}")

        if not sentiments:
            return {
                "error": "No sentiment data available for comparison",
                "ticker": ticker,
                "quarters": quarters,
            }

        # Calculate trend
        scores = [s["sentiment_score"] for s in sentiments]
        trend = "improving" if scores[-1] > scores[0] else "declining" if scores[-1] < scores[0] else "stable"

        return {
            "ticker": ticker,
            "quarters_analyzed": len(sentiments),
            "sentiment_trend": trend,
            "score_change": scores[-1] - scores[0],
            "sentiments": sentiments,
            "average_confidence": sum(s["confidence_score"] for s in sentiments) / len(sentiments),
        }
