"""
Conference Call Business Logic Services.

Core business logic for transcript processing.

Available:
    - TranscriptFetcher: Orchestrate multi-source fetching [IMPLEMENTED]

Future:
    - ConcallSummarizer: AI-powered summarization
    - RAGEngine: Q&A over transcripts
    - SentimentAnalyzer: Tone and sentiment detection
"""

from maverick_mcp.concall.services.transcript_fetcher import TranscriptFetcher

__all__ = ["TranscriptFetcher"]
