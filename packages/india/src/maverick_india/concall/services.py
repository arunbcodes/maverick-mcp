"""
Conference Call Business Logic Services.

Core services for transcript processing and AI analysis.

Available Services:
    - TranscriptFetcher: Orchestrate multi-source fetching with fallback
    - ConcallSummarizer: AI-powered summarization (requires LLM)
    - SentimentAnalyzer: Multi-dimensional sentiment analysis (requires LLM)

Note: ConcallSummarizer and SentimentAnalyzer require maverick-agents for LLM access.
These are optional and will gracefully degrade if not available.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Callable

from maverick_india.concall.providers import CompanyIRProvider, ConcallProvider, NSEProvider

if TYPE_CHECKING:
    from maverick_data.models import ConferenceCall

logger = logging.getLogger(__name__)


class TranscriptFetcher:
    """
    High-level service for fetching conference call transcripts.

    Orchestrates multiple data providers with cascading fallback logic.
    Handles caching, persistence, and error recovery.

    Design Philosophy:
        - Provider-agnostic: Works with any ConcallProvider
        - Fail-safe: Tries multiple sources before giving up
        - Cache-friendly: Stores results in database
        - Simple API: One method to fetch transcripts

    Provider Priority:
        1. CompanyIRProvider (legal, reliable)
        2. NSEProvider (exchange filings)

    Attributes:
        providers: List of data providers to try
        save_to_db: Whether to persist transcripts to database
        use_cache: Whether to check database before fetching

    Example:
        >>> fetcher = TranscriptFetcher()
        >>> result = await fetcher.fetch_transcript("RELIANCE.NS", "Q1", 2025)
        >>> if result:
        ...     print(result["transcript_text"][:100])
    """

    def __init__(
        self,
        providers: list[ConcallProvider] | None = None,
        save_to_db: bool = True,
        use_cache: bool = True,
        session_factory: Callable[[], Any] | None = None,
    ):
        """
        Initialize transcript fetcher.

        Args:
            providers: List of providers to try (default: [CompanyIRProvider, NSEProvider])
            save_to_db: Save fetched transcripts to database
            use_cache: Check database cache before fetching
            session_factory: Optional callable returning database session
        """
        self.providers = providers or [
            CompanyIRProvider(session_factory=session_factory),
            NSEProvider(),
        ]
        self.save_to_db = save_to_db
        self.use_cache = use_cache
        self._session_factory = session_factory
        logger.info(f"Initialized TranscriptFetcher with {len(self.providers)} providers")

    async def fetch_transcript(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        force_refresh: bool = False,
    ) -> dict[str, Any] | None:
        """
        Fetch conference call transcript using cascading fallback.

        Args:
            ticker: Stock symbol (e.g., "RELIANCE.NS", "AAPL")
            quarter: Quarter (e.g., "Q1", "Q2", "Q3", "Q4")
            fiscal_year: Year (e.g., 2025)
            force_refresh: Skip cache and fetch fresh data

        Returns:
            dict with transcript data or None if not found:
                - transcript_text: Full transcript content
                - source: Provider that supplied the data
                - source_url: Original URL
                - transcript_format: Format (pdf, html, txt)
                - metadata: Additional info

        Example:
            >>> fetcher = TranscriptFetcher()
            >>> result = await fetcher.fetch_transcript("TCS.NS", "Q2", 2025)
            >>> if result:
            ...     print(f"Got transcript from {result['source']}")
        """
        # Normalize inputs
        ticker = ticker.upper()
        quarter = quarter.upper()

        # Step 1: Check database cache
        if self.use_cache and not force_refresh and self._session_factory:
            cached = self._get_from_cache(ticker, quarter, fiscal_year)
            if cached:
                logger.info(
                    f"[CACHE HIT] Retrieved transcript for {ticker} {quarter} FY{fiscal_year}"
                )
                return cached

        # Step 2: Try each provider
        for provider in self.providers:
            try:
                # Check if provider supports this ticker
                if not provider.is_available(ticker):
                    logger.debug(
                        f"Provider {provider.name} does not support {ticker}"
                    )
                    continue

                logger.info(
                    f"Attempting to fetch {ticker} {quarter} FY{fiscal_year} from {provider.name}"
                )

                # Fetch transcript
                result = await provider.fetch_transcript(ticker, quarter, fiscal_year)

                if result:
                    # Add provider info
                    result["source"] = provider.name

                    # Step 3: Save to database
                    if self.save_to_db and self._session_factory:
                        self._save_to_db(ticker, quarter, fiscal_year, result)

                    logger.info(
                        f"[FETCH] Successfully fetched {ticker} {quarter} FY{fiscal_year} from {provider.name}"
                    )
                    return result

            except Exception as e:
                logger.warning(
                    f"Provider {provider.name} failed for {ticker}: {e}"
                )
                # Continue to next provider

        # All providers failed
        logger.warning(
            f"All providers failed for {ticker} {quarter} FY{fiscal_year}"
        )
        return None

    def _get_from_cache(
        self, ticker: str, quarter: str, fiscal_year: int
    ) -> dict[str, Any] | None:
        """
        Get transcript from database cache.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year

        Returns:
            dict with transcript data or None
        """
        if not self._session_factory:
            return None

        try:
            from maverick_data.models import ConferenceCall

            session = self._session_factory()
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
                # Update access time for cache management
                call.mark_accessed()
                session.commit()

                result = {
                    "transcript_text": call.transcript_text,
                    "source": call.source,
                    "source_url": call.source_url,
                    "transcript_format": call.transcript_format,
                    "metadata": {
                        "ticker": call.ticker,
                        "quarter": call.quarter,
                        "fiscal_year": call.fiscal_year,
                        "call_date": call.call_date,
                        "cached": True,
                    },
                }
                return result

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve from cache: {e}")
            return None
        finally:
            session.close()

    def _save_to_db(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        result: dict[str, Any],
    ) -> None:
        """
        Save fetched transcript to database.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year
            result: Transcript result from provider
        """
        if not self._session_factory:
            return

        try:
            from maverick_data.models import ConferenceCall

            session = self._session_factory()

            # Check if exists
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
                # Update existing
                call.transcript_text = result.get("transcript_text")
                call.source = result.get("source")
                call.source_url = result.get("source_url")
                call.transcript_format = result.get("transcript_format")
                call.last_accessed = datetime.now(UTC)
            else:
                # Create new
                call = ConferenceCall(
                    ticker=ticker,
                    quarter=quarter,
                    fiscal_year=fiscal_year,
                    source=result.get("source", "unknown"),
                    source_url=result.get("source_url"),
                    transcript_text=result.get("transcript_text"),
                    transcript_format=result.get("transcript_format"),
                    call_date=result.get("metadata", {}).get("call_date"),
                )
                session.add(call)

            session.commit()
            logger.info(f"Saved transcript for {ticker} {quarter} FY{fiscal_year}")

        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
            session.rollback()
        finally:
            session.close()

    def get_available_transcripts(
        self, ticker: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get list of available transcripts for a company.

        Args:
            ticker: Stock symbol
            limit: Maximum number of results

        Returns:
            list of dicts with transcript metadata

        Example:
            >>> fetcher = TranscriptFetcher()
            >>> transcripts = fetcher.get_available_transcripts("RELIANCE.NS")
            >>> for t in transcripts:
            ...     print(f"{t['quarter']} FY{t['fiscal_year']}")
        """
        if not self._session_factory:
            return []

        try:
            from maverick_data.models import ConferenceCall

            session = self._session_factory()
            calls = (
                session.query(ConferenceCall)
                .filter(
                    ConferenceCall.ticker == ticker.upper(),
                    ConferenceCall.transcript_text.isnot(None),
                )
                .order_by(
                    ConferenceCall.fiscal_year.desc(), ConferenceCall.quarter.desc()
                )
                .limit(limit)
                .all()
            )

            results = []
            for call in calls:
                results.append(
                    {
                        "ticker": call.ticker,
                        "quarter": call.quarter,
                        "fiscal_year": call.fiscal_year,
                        "call_date": call.call_date,
                        "source": call.source,
                        "format": call.transcript_format,
                        "has_analysis": call.has_analysis,
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Failed to get available transcripts: {e}")
            return []
        finally:
            session.close()

    def add_provider(self, provider: ConcallProvider, priority: int = -1) -> None:
        """
        Add a new provider to the fetcher.

        Args:
            provider: Provider instance to add
            priority: Insert position (default: append to end)

        Example:
            >>> fetcher = TranscriptFetcher()
            >>> custom_provider = MyCustomProvider()
            >>> fetcher.add_provider(custom_provider, priority=0)
        """
        if priority == -1:
            self.providers.append(provider)
        else:
            self.providers.insert(priority, provider)

        logger.info(f"Added provider {provider.name} at priority {priority}")

    def get_provider_status(self) -> list[dict[str, Any]]:
        """
        Get status of all configured providers.

        Returns:
            list of dicts with provider info

        Example:
            >>> fetcher = TranscriptFetcher()
            >>> for status in fetcher.get_provider_status():
            ...     print(f"{status['name']}: {status['type']}")
        """
        status = []
        for i, provider in enumerate(self.providers):
            status.append(
                {
                    "priority": i,
                    "name": provider.name,
                    "type": type(provider).__name__,
                }
            )
        return status


# Prompts for AI analysis
SUMMARIZATION_PROMPT = """You are a financial analyst expert. Summarize this earnings call transcript for {ticker} ({company_name}) {quarter} FY{fiscal_year}.

**TRANSCRIPT:**
{transcript_text}

Provide a JSON response with:
{{
    "executive_summary": "2-3 sentence high-level summary",
    "key_metrics": {{"revenue": "...", "profit": "...", "growth": "..."}},
    "business_highlights": ["highlight1", "highlight2", ...],
    "management_guidance": {{"outlook": "...", "targets": [...]}},
    "sentiment": "<very_positive|positive|neutral|cautious|negative>",
    "key_risks": ["risk1", "risk2", ...],
    "opportunities": ["opportunity1", "opportunity2", ...],
    "qa_insights": ["insight1", "insight2", ...]
}}

Return ONLY the JSON object, no additional text.
"""

SENTIMENT_ANALYSIS_PROMPT = """Analyze the sentiment and management tone from this earnings call transcript.

**TRANSCRIPT:**
{transcript_text}

Provide a JSON response with:
{{
    "overall_sentiment": "<very_bullish|bullish|neutral|bearish|very_bearish>",
    "confidence_score": <0.0 to 1.0>,
    "management_tone": "<confident|optimistic|cautious|defensive|uncertain>",
    "outlook_sentiment": "<positive|neutral|negative>",
    "risk_sentiment": "<low_risk|moderate_risk|high_risk>",
    "key_positive_signals": ["signal1", "signal2", ...],
    "key_negative_signals": ["signal1", "signal2", ...],
    "sentiment_rationale": "Brief explanation",
    "tone_rationale": "Brief explanation"
}}

Return ONLY the JSON object, no additional text.
"""


class ConcallSummarizer:
    """
    AI-powered summarization service for conference call transcripts.

    Requires maverick-agents package for LLM access.
    Falls back gracefully if LLM is not available.

    Example:
        >>> summarizer = ConcallSummarizer()
        >>> summary = await summarizer.summarize_transcript(
        ...     "RELIANCE.NS", "Q1", 2025, transcript_text
        ... )
    """

    def __init__(
        self,
        llm_provider: Any | None = None,
        session_factory: Callable[[], Any] | None = None,
        save_to_db: bool = True,
    ):
        """
        Initialize summarizer.

        Args:
            llm_provider: LLM provider instance (from maverick-agents)
            session_factory: Optional callable returning database session
            save_to_db: Save summaries to database
        """
        self._llm_provider = llm_provider
        self._session_factory = session_factory
        self.save_to_db = save_to_db
        logger.info("Initialized ConcallSummarizer")

    async def summarize_transcript(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        transcript_text: str,
        company_name: str | None = None,
        mode: str = "standard",
        force_refresh: bool = False,
    ) -> dict[str, Any] | None:
        """
        Generate AI summary of conference call transcript.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year
            transcript_text: Full transcript content
            company_name: Company name (optional)
            mode: Summarization mode (concise, standard, detailed)
            force_refresh: Skip cache and regenerate

        Returns:
            dict: Structured summary or None if failed
        """
        ticker = ticker.upper()
        quarter = quarter.upper()

        # Check cache first
        if not force_refresh and self._session_factory:
            cached = self._get_from_cache(ticker, quarter, fiscal_year)
            if cached:
                logger.info(f"[CACHE HIT] Retrieved summary for {ticker} {quarter} FY{fiscal_year}")
                return cached

        # Check if LLM is available
        if self._llm_provider is None:
            logger.warning("LLM provider not configured, cannot generate summary")
            return None

        try:
            # Build prompt
            prompt = SUMMARIZATION_PROMPT.format(
                transcript_text=transcript_text[:20000],  # Truncate for context window
                ticker=ticker,
                company_name=company_name or ticker,
                quarter=quarter,
                fiscal_year=fiscal_year,
            )

            # Generate summary
            import json

            response = await self._llm_provider.ainvoke(prompt)
            summary_text = response.content if hasattr(response, "content") else str(response)

            # Parse JSON
            summary = self._parse_json_response(summary_text)
            if not summary:
                return None

            # Add metadata
            summary["_metadata"] = {
                "ticker": ticker,
                "quarter": quarter,
                "fiscal_year": fiscal_year,
                "mode": mode,
            }

            # Save to database
            if self.save_to_db and self._session_factory:
                self._save_to_db(ticker, quarter, fiscal_year, summary)

            logger.info(f"Generated summary for {ticker} {quarter} FY{fiscal_year}")
            return summary

        except Exception as e:
            logger.error(f"Failed to summarize {ticker} {quarter} FY{fiscal_year}: {e}")
            return None

    def _parse_json_response(self, text: str) -> dict[str, Any] | None:
        """Parse JSON from LLM response."""
        import json
        import re

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return None

    def _get_from_cache(
        self, ticker: str, quarter: str, fiscal_year: int
    ) -> dict[str, Any] | None:
        """Get cached summary from database."""
        if not self._session_factory:
            return None

        try:
            from maverick_data.models import ConferenceCall

            session = self._session_factory()
            call = (
                session.query(ConferenceCall)
                .filter(
                    ConferenceCall.ticker == ticker,
                    ConferenceCall.quarter == quarter,
                    ConferenceCall.fiscal_year == fiscal_year,
                    ConferenceCall.summary.isnot(None),
                )
                .first()
            )

            if call and call.summary:
                call.mark_accessed()
                session.commit()
                return call.summary

            return None
        except Exception as e:
            logger.error(f"Failed to retrieve summary from cache: {e}")
            return None
        finally:
            session.close()

    def _save_to_db(
        self, ticker: str, quarter: str, fiscal_year: int, summary: dict[str, Any]
    ) -> None:
        """Save summary to database."""
        if not self._session_factory:
            return

        try:
            from maverick_data.models import ConferenceCall

            session = self._session_factory()
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
                call.summary = summary
                call.sentiment = summary.get("sentiment")
                session.commit()
                logger.info(f"Saved summary for {ticker} {quarter} FY{fiscal_year}")
            else:
                logger.warning(f"No call record found for {ticker} {quarter} FY{fiscal_year}")

        except Exception as e:
            logger.error(f"Failed to save summary: {e}")
            session.rollback()
        finally:
            session.close()


class SentimentAnalyzer:
    """
    Analyze sentiment and tone from conference call transcripts.

    Requires maverick-agents package for LLM access.

    Example:
        >>> analyzer = SentimentAnalyzer()
        >>> sentiment = await analyzer.analyze_sentiment(
        ...     "RELIANCE.NS", "Q1", 2025, transcript_text
        ... )
    """

    SENTIMENT_SCALE = {
        "very_bullish": 5,
        "bullish": 4,
        "neutral": 3,
        "bearish": 2,
        "very_bearish": 1,
    }

    def __init__(
        self,
        llm_provider: Any | None = None,
        session_factory: Callable[[], Any] | None = None,
        save_to_db: bool = True,
    ):
        """
        Initialize sentiment analyzer.

        Args:
            llm_provider: LLM provider instance
            session_factory: Optional callable returning database session
            save_to_db: Save results to database
        """
        self._llm_provider = llm_provider
        self._session_factory = session_factory
        self.save_to_db = save_to_db
        logger.info("Initialized SentimentAnalyzer")

    async def analyze_sentiment(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        transcript_text: str,
        use_cache: bool = True,
    ) -> dict[str, Any] | None:
        """
        Analyze sentiment from conference call transcript.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year
            transcript_text: Transcript content
            use_cache: Use cached results if available

        Returns:
            dict: Sentiment analysis results or None
        """
        ticker = ticker.upper()
        quarter = quarter.upper()

        # Check cache
        if use_cache and self._session_factory:
            cached = self._get_from_cache(ticker, quarter, fiscal_year)
            if cached:
                logger.info(f"[CACHE HIT] Retrieved sentiment for {ticker} {quarter} FY{fiscal_year}")
                return cached

        # Check LLM availability
        if self._llm_provider is None:
            logger.warning("LLM provider not configured, cannot analyze sentiment")
            return None

        try:
            # Build prompt
            prompt = SENTIMENT_ANALYSIS_PROMPT.format(
                transcript_text=transcript_text[:15000]  # Truncate
            )

            # Generate analysis
            import json

            response = await self._llm_provider.ainvoke(prompt)
            sentiment_text = response.content if hasattr(response, "content") else str(response)

            # Parse JSON
            sentiment = self._parse_json_response(sentiment_text)
            if not sentiment:
                return None

            # Add metadata
            sentiment["ticker"] = ticker
            sentiment["quarter"] = quarter
            sentiment["fiscal_year"] = fiscal_year
            sentiment["sentiment_score"] = self.SENTIMENT_SCALE.get(
                sentiment.get("overall_sentiment", "neutral"), 3
            )

            # Save to database
            if self.save_to_db and self._session_factory:
                self._save_to_db(ticker, quarter, fiscal_year, sentiment)

            logger.info(f"Analyzed sentiment for {ticker} {quarter} FY{fiscal_year}")
            return sentiment

        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {e}")
            return None

    def _parse_json_response(self, text: str) -> dict[str, Any] | None:
        """Parse JSON from LLM response."""
        import json
        import re

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return None

    def _get_from_cache(
        self, ticker: str, quarter: str, fiscal_year: int
    ) -> dict[str, Any] | None:
        """Get cached sentiment from database."""
        if not self._session_factory:
            return None

        try:
            from maverick_data.models import ConferenceCall

            session = self._session_factory()
            call = (
                session.query(ConferenceCall)
                .filter(
                    ConferenceCall.ticker == ticker,
                    ConferenceCall.quarter == quarter,
                    ConferenceCall.fiscal_year == fiscal_year,
                )
                .first()
            )

            # Check if sentiment data exists in summary
            if call and call.summary and "sentiment_score" in call.summary:
                return call.summary

            return None
        except Exception as e:
            logger.error(f"Failed to retrieve sentiment from cache: {e}")
            return None
        finally:
            session.close()

    def _save_to_db(
        self, ticker: str, quarter: str, fiscal_year: int, sentiment: dict[str, Any]
    ) -> None:
        """Save sentiment to database."""
        if not self._session_factory:
            return

        try:
            from maverick_data.models import ConferenceCall

            session = self._session_factory()
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
                call.sentiment = sentiment.get("overall_sentiment")
                call.management_tone = sentiment.get("management_tone")
                # Store full sentiment in summary if not exists
                if not call.summary:
                    call.summary = sentiment
                session.commit()
                logger.info(f"Saved sentiment for {ticker} {quarter} FY{fiscal_year}")

        except Exception as e:
            logger.error(f"Failed to save sentiment: {e}")
            session.rollback()
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
        """
        ticker = ticker.upper()

        sentiments = []
        for quarter, fiscal_year in quarters:
            cached = self._get_from_cache(ticker, quarter, fiscal_year)
            if cached:
                sentiments.append(cached)

        if not sentiments:
            return {
                "error": "No sentiment data available for comparison",
                "ticker": ticker,
                "quarters": quarters,
            }

        # Calculate trend
        scores = [s.get("sentiment_score", 3) for s in sentiments]
        trend = (
            "improving"
            if scores[-1] > scores[0]
            else "declining"
            if scores[-1] < scores[0]
            else "stable"
        )

        return {
            "ticker": ticker,
            "quarters_analyzed": len(sentiments),
            "sentiment_trend": trend,
            "score_change": scores[-1] - scores[0],
            "sentiments": sentiments,
            "average_confidence": sum(
                s.get("confidence_score", 0.5) for s in sentiments
            )
            / len(sentiments),
        }


__all__ = [
    "TranscriptFetcher",
    "ConcallSummarizer",
    "SentimentAnalyzer",
    "SUMMARIZATION_PROMPT",
    "SENTIMENT_ANALYSIS_PROMPT",
]
