"""
Conference Call Summarization Service.

Single Responsibility: Summarize conference call transcripts using AI.
Open/Closed: Extensible via prompt templates, not code changes.
Liskov Substitution: Compatible with any LLM provider interface.
Interface Segregation: Simple, focused public API.
Dependency Inversion: Depends on provider abstraction.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from maverick_mcp.concall.models import ConferenceCall
from maverick_mcp.concall.prompts import (
    SENTIMENT_ANALYSIS_PROMPT,
    SUMMARIZATION_PROMPT,
)
from maverick_mcp.concall.prompts.concall_prompts import SUMMARIZATION_MODES
from maverick_mcp.data.models import get_session
from maverick_mcp.providers.openrouter_provider import OpenRouterProvider, TaskType

logger = logging.getLogger(__name__)


class ConcallSummarizer:
    """
    AI-powered summarization service for conference call transcripts.

    Uses OpenRouter with intelligent model selection for cost-effective,
    high-quality summaries. Caches results in database to avoid redundant API calls.

    Design Philosophy:
        - Cost-effective: Uses appropriate models for task complexity
        - Cache-first: Checks database before API calls
        - Structured output: JSON-formatted summaries for consistency
        - Error-resilient: Graceful fallback and error handling

    Attributes:
        openrouter: OpenRouter provider for LLM access
        save_to_db: Whether to cache summaries in database
        use_cache: Whether to check database cache first

    Example:
        >>> summarizer = ConcallSummarizer()
        >>> summary = await summarizer.summarize_transcript(
        ...     "RELIANCE.NS", "Q1", 2025, transcript_text
        ... )
        >>> if summary:
        ...     print(summary["executive_summary"])
    """

    def __init__(
        self,
        api_key: str | None = None,
        save_to_db: bool = True,
        use_cache: bool = True,
    ):
        """
        Initialize summarizer.

        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            save_to_db: Save summaries to database
            use_cache: Check database cache before summarizing
        """
        api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY env var or pass api_key parameter."
            )

        self.openrouter = OpenRouterProvider(api_key)
        self.save_to_db = save_to_db
        self.use_cache = use_cache

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
            ticker: Stock symbol (e.g., "RELIANCE.NS")
            quarter: Quarter (e.g., "Q1")
            fiscal_year: Year (e.g., 2025)
            transcript_text: Full transcript content
            company_name: Company name (optional, for better context)
            mode: Summarization mode (concise, standard, detailed)
            force_refresh: Skip cache and regenerate summary

        Returns:
            dict: Structured summary with metrics, sentiment, guidance, etc.
            None if summarization fails

        Example:
            >>> summary = await summarizer.summarize_transcript(
            ...     "RELIANCE.NS", "Q1", 2025, transcript_text,
            ...     mode="detailed"
            ... )
        """
        # Normalize inputs
        ticker = ticker.upper()
        quarter = quarter.upper()

        # Step 1: Check cache
        if self.use_cache and not force_refresh:
            cached = self._get_from_cache(ticker, quarter, fiscal_year)
            if cached:
                logger.info(
                    f"Retrieved summary for {ticker} {quarter} FY{fiscal_year} from cache"
                )
                return cached

        # Step 2: Generate summary
        try:
            logger.info(
                f"Generating {mode} summary for {ticker} {quarter} FY{fiscal_year}"
            )

            # Get mode configuration
            mode_config = SUMMARIZATION_MODES.get(mode, SUMMARIZATION_MODES["standard"])

            # Build prompt
            prompt = SUMMARIZATION_PROMPT.format(
                transcript_text=transcript_text,
                ticker=ticker,
                company_name=company_name or ticker,
                quarter=quarter,
                fiscal_year=fiscal_year,
            )

            # Get LLM with intelligent model selection
            # Use TaskType.MARKET_ANALYSIS for cost-effective, high-quality analysis
            llm = self.openrouter.get_llm(
                task_type=TaskType.MARKET_ANALYSIS,
                prefer_cheap=True,  # Cost-effective models
                temperature=mode_config["temperature"],
                max_tokens=mode_config["max_tokens"],
            )

            # Generate summary
            response = await llm.ainvoke(prompt)
            summary_text = response.content

            # Parse JSON response
            try:
                summary = json.loads(summary_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                if "```json" in summary_text:
                    json_start = summary_text.find("```json") + 7
                    json_end = summary_text.find("```", json_start)
                    summary_text = summary_text[json_start:json_end].strip()
                    summary = json.loads(summary_text)
                elif "```" in summary_text:
                    json_start = summary_text.find("```") + 3
                    json_end = summary_text.find("```", json_start)
                    summary_text = summary_text[json_start:json_end].strip()
                    summary = json.loads(summary_text)
                else:
                    raise

            # Add metadata
            summary["_metadata"] = {
                "ticker": ticker,
                "quarter": quarter,
                "fiscal_year": fiscal_year,
                "mode": mode,
                "model_used": llm.model_name,
                "generated_at": None,  # Will be set by database
            }

            # Step 3: Save to database
            if self.save_to_db:
                self._save_to_db(ticker, quarter, fiscal_year, summary)

            logger.info(
                f"Successfully summarized {ticker} {quarter} FY{fiscal_year}"
            )
            return summary

        except Exception as e:
            logger.error(
                f"Failed to summarize {ticker} {quarter} FY{fiscal_year}: {e}"
            )
            return None

    async def analyze_sentiment(
        self,
        transcript_text: str,
        force_refresh: bool = False,
    ) -> dict[str, Any] | None:
        """
        Analyze sentiment of transcript.

        Args:
            transcript_text: Full transcript content
            force_refresh: Skip cache and regenerate

        Returns:
            dict: Sentiment analysis with scores and explanations
            None if analysis fails

        Example:
            >>> sentiment = await summarizer.analyze_sentiment(transcript_text)
            >>> print(sentiment["sentiment"])  # "positive"
            >>> print(sentiment["confidence_score"])  # 0.85
        """
        try:
            logger.info("Analyzing transcript sentiment")

            # Build prompt
            prompt = SENTIMENT_ANALYSIS_PROMPT.format(
                transcript_text=transcript_text
            )

            # Use fast, cheap model for sentiment analysis
            llm = self.openrouter.get_llm(
                task_type=TaskType.SENTIMENT_ANALYSIS,
                prefer_cheap=True,
                prefer_fast=True,
                temperature=0.2,
                max_tokens=500,
            )

            # Analyze sentiment
            response = await llm.ainvoke(prompt)
            sentiment_text = response.content

            # Parse JSON response
            try:
                sentiment = json.loads(sentiment_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown
                if "```json" in sentiment_text:
                    json_start = sentiment_text.find("```json") + 7
                    json_end = sentiment_text.find("```", json_start)
                    sentiment_text = sentiment_text[json_start:json_end].strip()
                    sentiment = json.loads(sentiment_text)
                elif "```" in sentiment_text:
                    json_start = sentiment_text.find("```") + 3
                    json_end = sentiment_text.find("```", json_start)
                    sentiment_text = sentiment_text[json_start:json_end].strip()
                    sentiment = json.loads(sentiment_text)
                else:
                    raise

            logger.info(
                f"Sentiment analysis complete: {sentiment.get('sentiment')}"
            )
            return sentiment

        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {e}")
            return None

    def _get_from_cache(
        self, ticker: str, quarter: str, fiscal_year: int
    ) -> dict[str, Any] | None:
        """
        Get summary from database cache.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year

        Returns:
            dict: Cached summary or None
        """
        try:
            session = get_session()
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
                # Update access time
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
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        summary: dict[str, Any],
    ) -> None:
        """
        Save summary to database.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year
            summary: Summary dict
        """
        try:
            session = get_session()

            # Find or create call record
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
                call.summary = summary
                call.sentiment = summary.get("sentiment")
                logger.info(f"Updated summary for {ticker} {quarter} FY{fiscal_year}")
            else:
                # Create new (shouldn't happen in normal flow, but handle gracefully)
                call = ConferenceCall(
                    ticker=ticker,
                    quarter=quarter,
                    fiscal_year=fiscal_year,
                    summary=summary,
                    sentiment=summary.get("sentiment"),
                )
                session.add(call)
                logger.info(f"Created new record with summary for {ticker} {quarter} FY{fiscal_year}")

            session.commit()

        except Exception as e:
            logger.error(f"Failed to save summary to database: {e}")
            session.rollback()
        finally:
            session.close()

    def get_summary_statistics(self) -> dict[str, Any]:
        """
        Get statistics about cached summaries.

        Returns:
            dict: Statistics (total, by sentiment, etc.)

        Example:
            >>> stats = summarizer.get_summary_statistics()
            >>> print(f"Total summaries: {stats['total']}")
        """
        try:
            session = get_session()

            total = (
                session.query(ConferenceCall)
                .filter(ConferenceCall.summary.isnot(None))
                .count()
            )

            # Count by sentiment
            sentiments = {}
            for sentiment in [
                "very_positive",
                "positive",
                "neutral",
                "cautious",
                "negative",
            ]:
                count = (
                    session.query(ConferenceCall)
                    .filter(ConferenceCall.sentiment == sentiment)
                    .count()
                )
                if count > 0:
                    sentiments[sentiment] = count

            return {
                "total_summaries": total,
                "by_sentiment": sentiments,
            }

        except Exception as e:
            logger.error(f"Failed to get summary statistics: {e}")
            return {"total_summaries": 0, "by_sentiment": {}}
        finally:
            session.close()
