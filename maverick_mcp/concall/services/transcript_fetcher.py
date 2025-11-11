"""
Transcript Fetcher Service.

Single Responsibility: Orchestrate transcript fetching from multiple sources.
Open/Closed: Extensible via provider list, not code changes.
Liskov Substitution: All providers implement ConcallProvider interface.
Interface Segregation: Simple, focused public API.
Dependency Inversion: Depends on ConcallProvider abstraction.

Enhanced with multi-tier caching:
    - L1: Redis/In-memory cache (milliseconds)
    - L2: Database cache (seconds)
    - L3: External providers (minutes)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from maverick_mcp.concall.cache import ConcallCacheService
from maverick_mcp.concall.models import ConferenceCall
from maverick_mcp.concall.providers import CompanyIRProvider, ConcallProvider
from maverick_mcp.data.models import get_session

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
        2. NSEProvider (TODO - exchange filings)
        3. ScreenerProvider (TODO - screener.in)
        4. YouTubeProvider (TODO - audio transcription)

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
        cache_service: ConcallCacheService | None = None,
    ):
        """
        Initialize transcript fetcher.

        Args:
            providers: List of providers to try (default: [CompanyIRProvider])
            save_to_db: Save fetched transcripts to database
            use_cache: Check caches (Redis/in-memory + database) before fetching
            cache_service: Cache service instance (default: auto-created)
        """
        self.providers = providers or [CompanyIRProvider()]
        self.save_to_db = save_to_db
        self.use_cache = use_cache

        # Initialize L1 cache (Redis/in-memory)
        self.cache_service = cache_service or ConcallCacheService()
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

        Algorithm:
            1. Check database cache (if use_cache and not force_refresh)
            2. Try each provider in order until one succeeds
            3. Save to database (if save_to_db)
            4. Return result

        Example:
            >>> fetcher = TranscriptFetcher()
            >>> result = await fetcher.fetch_transcript("TCS.NS", "Q2", 2025)
            >>> if result:
            ...     print(f"Got transcript from {result['source']}")
        """
        # Normalize inputs
        ticker = ticker.upper()
        quarter = quarter.upper()

        # Step 1: Check L1 cache (Redis/in-memory - fastest)
        if self.use_cache and not force_refresh:
            l1_cached = await self.cache_service.get_transcript(ticker, quarter, fiscal_year)
            if l1_cached:
                logger.info(
                    f"[L1 HIT] Retrieved transcript for {ticker} {quarter} FY{fiscal_year} from Redis/memory cache"
                )
                return l1_cached

        # Step 2: Check L2 cache (database - slower but persistent)
        if self.use_cache and not force_refresh:
            l2_cached = self._get_from_cache(ticker, quarter, fiscal_year)
            if l2_cached:
                logger.info(
                    f"[L2 HIT] Retrieved transcript for {ticker} {quarter} FY{fiscal_year} from database"
                )
                # Populate L1 cache for future requests
                await self.cache_service.cache_transcript(
                    ticker=ticker,
                    quarter=quarter,
                    fiscal_year=fiscal_year,
                    transcript_text=l2_cached["transcript_text"],
                    metadata=l2_cached.get("metadata", {}),
                )
                return l2_cached

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

                    # Step 3: Save to L2 cache (database)
                    if self.save_to_db:
                        self._save_to_db(ticker, quarter, fiscal_year, result)

                    # Step 4: Populate L1 cache (Redis/in-memory)
                    if self.use_cache:
                        await self.cache_service.cache_transcript(
                            ticker=ticker,
                            quarter=quarter,
                            fiscal_year=fiscal_year,
                            transcript_text=result.get("transcript_text", ""),
                            metadata=result.get("metadata", {}),
                        )

                    logger.info(
                        f"[L3 FETCH] Successfully fetched {ticker} {quarter} FY{fiscal_year} from {provider.name}"
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
        try:
            session = get_session()

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
            logger.info(f"Saved transcript for {ticker} {quarter} FY{fiscal_year} to database")

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
        try:
            session = get_session()
            calls = (
                session.query(ConferenceCall)
                .filter(
                    ConferenceCall.ticker == ticker.upper(),
                    ConferenceCall.transcript_text.isnot(None),
                )
                .order_by(ConferenceCall.fiscal_year.desc(), ConferenceCall.quarter.desc())
                .limit(limit)
                .all()
            )

            results = []
            for call in calls:
                results.append({
                    "ticker": call.ticker,
                    "quarter": call.quarter,
                    "fiscal_year": call.fiscal_year,
                    "call_date": call.call_date,
                    "source": call.source,
                    "format": call.transcript_format,
                    "has_analysis": call.has_analysis,
                })

            return results

        except Exception as e:
            logger.error(f"Failed to get available transcripts: {e}")
            return []
        finally:
            session.close()

    async def clear_cache(
        self, ticker: str | None = None, older_than_days: int | None = None
    ) -> int:
        """
        Clear cached transcripts from both L1 (Redis/in-memory) and L2 (database) caches.

        Args:
            ticker: Clear cache for specific ticker (or all if None)
            older_than_days: Clear transcripts not accessed in N days

        Returns:
            int: Number of transcripts cleared

        Example:
            >>> fetcher = TranscriptFetcher()
            >>> # Clear all cache for RELIANCE.NS
            >>> count = await fetcher.clear_cache(ticker="RELIANCE.NS")
            >>> # Clear transcripts not accessed in 90 days
            >>> count = await fetcher.clear_cache(older_than_days=90)
        """
        # Clear L1 cache (Redis/in-memory)
        l1_count = 0
        if ticker:
            # For specific ticker, we need to query database to know which calls exist
            available = self.get_available_transcripts(ticker, limit=100)
            for call in available:
                deleted = await self.cache_service.cache_service.backend.delete(
                    self.cache_service.key_generator.generate_transcript_key(
                        call["ticker"], call["quarter"], call["fiscal_year"]
                    )
                )
                if deleted:
                    l1_count += 1
        else:
            # Clear all transcripts from L1 cache
            from maverick_mcp.concall.cache import CacheNamespace

            l1_count = await self.cache_service.invalidate_namespace(
                CacheNamespace.TRANSCRIPT
            )
        # Clear L2 cache (database)
        try:
            session = get_session()
            query = session.query(ConferenceCall)

            # Filter by ticker
            if ticker:
                query = query.filter(ConferenceCall.ticker == ticker.upper())

            # Filter by last accessed
            if older_than_days:
                cutoff_date = datetime.now(UTC).replace(
                    day=datetime.now(UTC).day - older_than_days
                )
                query = query.filter(
                    ConferenceCall.last_accessed < cutoff_date
                )

            # Delete
            l2_count = query.delete()
            session.commit()

            total_count = l1_count + l2_count
            logger.info(
                f"Cleared {total_count} cached transcripts (L1: {l1_count}, L2: {l2_count})"
            )
            return total_count

        except Exception as e:
            logger.error(f"Failed to clear L2 cache: {e}")
            session.rollback()
            return l1_count  # Return at least L1 count
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
            >>> # Add NSE provider as fallback
            >>> nse_provider = NSEProvider()
            >>> fetcher.add_provider(nse_provider, priority=1)
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
            ...     print(f"{status['name']}: {status['available']}")
        """
        status = []
        for i, provider in enumerate(self.providers):
            status.append({
                "priority": i,
                "name": provider.name,
                "type": type(provider).__name__,
            })
        return status
