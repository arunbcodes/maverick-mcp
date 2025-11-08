"""
Conference Call Analysis Router for Maverick-MCP.

This module contains tools for fetching, analyzing, and querying
earnings call transcripts using AI-powered analysis.

Tools:
- fetch_transcript: Fetch earnings call transcript
- summarize_transcript: Generate AI-powered summary
- analyze_sentiment: Analyze sentiment and management tone
- query_transcript: RAG-powered Q&A over transcripts
"""

import logging
from typing import Any

from fastmcp import FastMCP

from maverick_mcp.concall.services import (
    ConcallRAGEngine,
    ConcallSummarizer,
    SentimentAnalyzer,
    TranscriptFetcher,
)

logger = logging.getLogger(__name__)

# Create the concall router
concall_router: FastMCP = FastMCP("Conference_Call_Analysis")


def fetch_transcript(
    ticker: str,
    quarter: str,
    fiscal_year: int,
    save_to_db: bool = True,
) -> dict[str, Any]:
    """
    Fetch earnings call transcript from multiple sources.

    Fetches conference call transcripts with cascading fallback across:
    1. Company IR website (primary)
    2. NSE exchange filings (fallback for Indian stocks)

    Supports multiple formats (PDF, HTML, TXT) with automatic parsing.

    Args:
        ticker: Stock symbol (e.g., "RELIANCE.NS", "AAPL")
        quarter: Quarter (e.g., "Q1", "Q2", "Q3", "Q4")
        fiscal_year: Fiscal year (e.g., 2025)
        save_to_db: Save transcript to database (default: True)

    Returns:
        Dictionary containing:
        - ticker: Stock symbol
        - quarter: Quarter
        - fiscal_year: Year
        - transcript_text: Full transcript content
        - source: Data source used
        - fetch_date: Timestamp
        - word_count: Transcript length

    Examples:
        >>> fetch_transcript(
        ...     ticker="RELIANCE.NS",
        ...     quarter="Q1",
        ...     fiscal_year=2025
        ... )

        >>> fetch_transcript(
        ...     ticker="TCS.NS",
        ...     quarter="Q4",
        ...     fiscal_year=2024
        ... )
    """
    try:
        import asyncio

        fetcher = TranscriptFetcher(save_to_db=save_to_db)

        # Run async function in sync context
        result = asyncio.run(
            fetcher.fetch_transcript(
                ticker=ticker,
                quarter=quarter,
                fiscal_year=fiscal_year,
            )
        )

        return result

    except Exception as e:
        logger.error(f"Failed to fetch transcript for {ticker} {quarter} FY{fiscal_year}: {e}")
        return {
            "error": str(e),
            "ticker": ticker,
            "quarter": quarter,
            "fiscal_year": fiscal_year,
            "message": "Failed to fetch transcript. Check if IR mapping exists in database.",
        }


def summarize_transcript(
    ticker: str,
    quarter: str,
    fiscal_year: int,
    mode: str = "standard",
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    Generate AI-powered summary of earnings call transcript.

    Creates comprehensive structured summaries using AI analysis with:
    - Executive summary
    - Key financial metrics
    - Business highlights
    - Management guidance
    - Sentiment analysis
    - Risk assessment
    - Q&A insights

    Summaries are cached in database for fast retrieval.

    Args:
        ticker: Stock symbol (e.g., "RELIANCE.NS", "AAPL")
        quarter: Quarter (e.g., "Q1", "Q2", "Q3", "Q4")
        fiscal_year: Fiscal year (e.g., 2025)
        mode: Summary detail level - "concise" (1500 tokens), "standard" (3000 tokens),
              or "detailed" (5000 tokens). Default: "standard"
        force_refresh: Regenerate summary even if cached (default: False)

    Returns:
        Dictionary containing:
        - executive_summary: High-level overview
        - key_metrics: Financial performance data
        - business_highlights: Major developments
        - management_guidance: Forward-looking statements
        - sentiment: Overall tone (very_positive/positive/neutral/cautious/negative)
        - key_risks: Identified risk factors
        - opportunities: Growth opportunities
        - qa_insights: Key points from Q&A
        - market_context: Industry and competitive context
        - analyst_focus: Areas of analyst attention

    Examples:
        >>> summarize_transcript(
        ...     ticker="RELIANCE.NS",
        ...     quarter="Q1",
        ...     fiscal_year=2025,
        ...     mode="standard"
        ... )

        >>> summarize_transcript(
        ...     ticker="TCS.NS",
        ...     quarter="Q4",
        ...     fiscal_year=2024,
        ...     mode="detailed",
        ...     force_refresh=True
        ... )
    """
    try:
        import asyncio
        import os

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return {
                "error": "OPENROUTER_API_KEY not configured",
                "message": "Set OPENROUTER_API_KEY environment variable to use AI summarization",
            }

        summarizer = ConcallSummarizer(api_key=api_key, save_to_db=True, use_cache=True)

        # Run async function in sync context
        result = asyncio.run(
            summarizer.summarize_transcript(
                ticker=ticker,
                quarter=quarter,
                fiscal_year=fiscal_year,
                mode=mode,
                force_refresh=force_refresh,
            )
        )

        return result

    except Exception as e:
        logger.error(f"Failed to summarize transcript for {ticker} {quarter} FY{fiscal_year}: {e}")
        return {
            "error": str(e),
            "ticker": ticker,
            "quarter": quarter,
            "fiscal_year": fiscal_year,
            "message": "Failed to generate summary. Ensure transcript exists in database.",
        }


def analyze_sentiment(
    ticker: str,
    quarter: str,
    fiscal_year: int,
    use_cache: bool = True,
) -> dict[str, Any]:
    """
    Analyze sentiment and management tone from earnings call.

    Provides multi-dimensional sentiment analysis including:
    - Overall sentiment (very_bullish to very_bearish)
    - Management tone (confident/cautious/defensive)
    - Forward outlook sentiment
    - Risk sentiment assessment
    - Key positive/negative signals
    - Confidence scoring

    Results are cached in database for fast retrieval.

    Args:
        ticker: Stock symbol (e.g., "RELIANCE.NS", "AAPL")
        quarter: Quarter (e.g., "Q1", "Q2", "Q3", "Q4")
        fiscal_year: Fiscal year (e.g., 2025)
        use_cache: Use cached results if available (default: True)

    Returns:
        Dictionary containing:
        - overall_sentiment: very_bullish/bullish/neutral/bearish/very_bearish
        - sentiment_score: Numeric score (1-5)
        - confidence_score: Analysis confidence (0.0-1.0)
        - management_tone: confident/optimistic/cautious/defensive/uncertain
        - outlook_sentiment: positive/neutral/negative
        - risk_sentiment: low_risk/moderate_risk/high_risk
        - key_positive_signals: List of positive indicators
        - key_negative_signals: List of negative indicators
        - hedge_words_count: Number of qualifying terms
        - certainty_indicators: List of confidence phrases
        - sentiment_rationale: Explanation of assessment
        - tone_rationale: Explanation of tone

    Examples:
        >>> analyze_sentiment(
        ...     ticker="RELIANCE.NS",
        ...     quarter="Q1",
        ...     fiscal_year=2025
        ... )

        >>> analyze_sentiment(
        ...     ticker="TCS.NS",
        ...     quarter="Q4",
        ...     fiscal_year=2024,
        ...     use_cache=False
        ... )
    """
    try:
        import asyncio
        import os

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return {
                "error": "OPENROUTER_API_KEY not configured",
                "message": "Set OPENROUTER_API_KEY environment variable to use AI sentiment analysis",
            }

        analyzer = SentimentAnalyzer(openrouter_api_key=api_key, save_to_db=True)

        # Run async function in sync context
        result = asyncio.run(
            analyzer.analyze_sentiment(
                ticker=ticker,
                quarter=quarter,
                fiscal_year=fiscal_year,
                use_cache=use_cache,
            )
        )

        return result

    except Exception as e:
        logger.error(f"Failed to analyze sentiment for {ticker} {quarter} FY{fiscal_year}: {e}")
        return {
            "error": str(e),
            "ticker": ticker,
            "quarter": quarter,
            "fiscal_year": fiscal_year,
            "message": "Failed to analyze sentiment. Ensure transcript exists in database.",
        }


def query_transcript(
    question: str,
    ticker: str,
    quarter: str,
    fiscal_year: int,
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Ask questions about earnings call transcript using RAG.

    Enables semantic search and Q&A over conference call transcripts using:
    - Vector embeddings for semantic search
    - Context-aware LLM responses
    - Source citations from transcript
    - Automatic indexing on first query

    Powered by Chroma vector database and OpenAI embeddings.

    Args:
        question: Question to ask about the transcript
        ticker: Stock symbol (e.g., "RELIANCE.NS", "AAPL")
        quarter: Quarter (e.g., "Q1", "Q2", "Q3", "Q4")
        fiscal_year: Fiscal year (e.g., 2025)
        top_k: Number of relevant chunks to retrieve (default: 5)

    Returns:
        Dictionary containing:
        - answer: AI-generated answer based on transcript
        - sources: List of relevant transcript excerpts with:
            - content: Transcript chunk text
            - score: Relevance score
            - chunk_index: Position in transcript
        - metadata: Query metadata (ticker, quarter, year, chunks_retrieved)

    Examples:
        >>> query_transcript(
        ...     question="What was the revenue growth?",
        ...     ticker="RELIANCE.NS",
        ...     quarter="Q1",
        ...     fiscal_year=2025
        ... )

        >>> query_transcript(
        ...     question="What did management say about future guidance?",
        ...     ticker="TCS.NS",
        ...     quarter="Q4",
        ...     fiscal_year=2024,
        ...     top_k=3
        ... )
    """
    try:
        import asyncio
        import os

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return {
                "error": "OPENROUTER_API_KEY not configured",
                "message": "Set OPENROUTER_API_KEY environment variable to use RAG Q&A",
            }

        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return {
                "error": "OPENAI_API_KEY not configured",
                "message": "Set OPENAI_API_KEY environment variable for embeddings (required for RAG)",
            }

        rag = ConcallRAGEngine(
            openrouter_api_key=api_key,
            auto_index=True,  # Auto-index on first query
        )

        # Run async function in sync context
        result = asyncio.run(
            rag.query(
                question=question,
                ticker=ticker,
                quarter=quarter,
                fiscal_year=fiscal_year,
                top_k=top_k,
            )
        )

        return result

    except Exception as e:
        logger.error(f"Failed to query transcript for {ticker} {quarter} FY{fiscal_year}: {e}")
        return {
            "error": str(e),
            "ticker": ticker,
            "quarter": quarter,
            "fiscal_year": fiscal_year,
            "message": "Failed to query transcript. Ensure transcript exists in database.",
        }


def compare_quarters(
    ticker: str,
    quarters: list[tuple[str, int]],
) -> dict[str, Any]:
    """
    Compare sentiment across multiple quarters.

    Analyzes sentiment trends over time to identify:
    - Improving/declining/stable sentiment patterns
    - Management confidence changes
    - Risk perception evolution
    - Score changes over time

    Args:
        ticker: Stock symbol (e.g., "RELIANCE.NS", "AAPL")
        quarters: List of (quarter, fiscal_year) tuples to compare
                 Example: [("Q3", 2024), ("Q4", 2024), ("Q1", 2025)]

    Returns:
        Dictionary containing:
        - ticker: Stock symbol
        - quarters_analyzed: Number of quarters analyzed
        - sentiment_trend: "improving", "declining", or "stable"
        - score_change: Change in sentiment score
        - sentiments: List of sentiment data for each quarter
        - average_confidence: Average confidence across quarters

    Examples:
        >>> compare_quarters(
        ...     ticker="RELIANCE.NS",
        ...     quarters=[("Q4", 2024), ("Q1", 2025)]
        ... )

        >>> compare_quarters(
        ...     ticker="TCS.NS",
        ...     quarters=[("Q2", 2024), ("Q3", 2024), ("Q4", 2024)]
        ... )
    """
    try:
        import asyncio
        import os

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return {
                "error": "OPENROUTER_API_KEY not configured",
                "message": "Set OPENROUTER_API_KEY environment variable to use sentiment comparison",
            }

        analyzer = SentimentAnalyzer(openrouter_api_key=api_key, save_to_db=True)

        # Run async function in sync context
        result = asyncio.run(
            analyzer.compare_sentiment(
                ticker=ticker,
                quarters=quarters,
            )
        )

        return result

    except Exception as e:
        logger.error(f"Failed to compare quarters for {ticker}: {e}")
        return {
            "error": str(e),
            "ticker": ticker,
            "message": "Failed to compare quarters. Ensure transcripts exist for all quarters.",
        }


# Register all tools with the router
concall_router.tool(fetch_transcript)
concall_router.tool(summarize_transcript)
concall_router.tool(analyze_sentiment)
concall_router.tool(query_transcript)
concall_router.tool(compare_quarters)
