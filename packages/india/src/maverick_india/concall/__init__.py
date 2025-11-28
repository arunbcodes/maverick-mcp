"""
Conference Call Analysis.

Earnings call transcript fetching, summarization, and sentiment analysis.

This module provides the core interfaces and protocols for conference call
analysis. The interfaces are designed to be implemented by providers that
can fetch and analyze earnings call transcripts.

Note: Full implementations with database integration and AI analysis services
are available in the main maverick_mcp.concall package. This module provides
the independent, portable interface layer.

Components:
    - ConcallProvider: Abstract interface for transcript providers

Future Integration:
    When maverick-data and maverick-agents packages are complete, additional
    components will be migrated:
    - ConferenceCall model (from maverick-data)
    - CompanyIRMapping model (from maverick-data)
    - TranscriptFetcher service
    - ConcallSummarizer service (requires maverick-agents)
    - SentimentAnalyzer service (requires maverick-agents)
    - ConcallRAGEngine (requires maverick-agents)

Example:
    >>> from maverick_india.concall import ConcallProvider
    >>>
    >>> class MyProvider(ConcallProvider):
    ...     async def fetch_transcript(self, ticker, quarter, fiscal_year):
    ...         # Implementation
    ...         pass
    ...
    ...     def is_available(self, ticker):
    ...         return True
    ...
    ...     @property
    ...     def name(self):
    ...         return "my_provider"
"""

from maverick_india.concall.providers import ConcallProvider

__all__ = [
    "ConcallProvider",
]
