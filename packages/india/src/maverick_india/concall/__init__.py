"""
Conference Call Analysis.

Earnings call transcript fetching, summarization, and sentiment analysis.

This module provides:
- ConcallProvider: Abstract interface for transcript providers
- CompanyIRProvider: Fetch transcripts from company IR websites
- NSEProvider: Fetch transcripts from NSE exchange filings
- ScreenerProvider: Fetch from Screener.in (consolidated fallback)
- TranscriptLoader utilities: Parse PDF, HTML, and text transcripts

Models (from maverick-data):
- ConferenceCall: Main model for storing transcripts and analysis
- CompanyIRMapping: Model for company IR website URL mappings

Services (require LLM integration):
- TranscriptFetcher: Orchestrates transcript fetching with fallback
- ConcallSummarizer: AI-powered summarization (requires maverick-agents)
- SentimentAnalyzer: Sentiment analysis (requires maverick-agents)
- ConcallRAGEngine: RAG-based Q&A (requires maverick-agents)

Example:
    >>> from maverick_india.concall import CompanyIRProvider, NSEProvider, ScreenerProvider
    >>>
    >>> # Fetch from company IR website
    >>> ir_provider = CompanyIRProvider()
    >>> transcript = await ir_provider.fetch_transcript("RELIANCE.NS", "Q1", 2025)
    >>>
    >>> # Fallback to NSE filings
    >>> nse_provider = NSEProvider()
    >>> transcript = await nse_provider.fetch_transcript("RELIANCE.NS", "Q1", 2025)
    >>>
    >>> # Fallback to Screener.in (https://www.screener.in/concalls/)
    >>> screener_provider = ScreenerProvider()
    >>> transcript = await screener_provider.fetch_transcript("RELIANCE.NS", "Q1", 2025)
"""

from maverick_india.concall.providers import (
    CompanyIRProvider,
    ConcallProvider,
    NSEProvider,
    ScreenerProvider,
)
from maverick_india.concall.services import (
    SENTIMENT_ANALYSIS_PROMPT,
    SUMMARIZATION_PROMPT,
    ConcallSummarizer,
    SentimentAnalyzer,
    TranscriptFetcher,
)
from maverick_india.concall.utils import (
    HTMLTranscriptLoader,
    PDFTranscriptLoader,
    TextTranscriptLoader,
    TranscriptLoader,
    TranscriptLoaderFactory,
)

# RAG module (optional - requires chromadb and langchain)
try:
    from maverick_india.concall.rag import (
        ConcallRAGEngine,
        VectorStoreManager,
    )

    _RAG_AVAILABLE = True
except ImportError:
    _RAG_AVAILABLE = False
    ConcallRAGEngine = None  # type: ignore
    VectorStoreManager = None  # type: ignore

__all__ = [
    # Providers
    "ConcallProvider",
    "CompanyIRProvider",
    "NSEProvider",
    "ScreenerProvider",
    # Services
    "TranscriptFetcher",
    "ConcallSummarizer",
    "SentimentAnalyzer",
    "SUMMARIZATION_PROMPT",
    "SENTIMENT_ANALYSIS_PROMPT",
    # Transcript Loaders
    "TranscriptLoader",
    "PDFTranscriptLoader",
    "HTMLTranscriptLoader",
    "TextTranscriptLoader",
    "TranscriptLoaderFactory",
    # RAG (optional)
    "ConcallRAGEngine",
    "VectorStoreManager",
]
