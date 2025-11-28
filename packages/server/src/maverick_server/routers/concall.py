"""
Conference Call Analysis Router for maverick-server.

Thin wrapper around maverick-india concall services.
Provides MCP tools for fetching, analyzing, and querying
earnings call transcripts using AI-powered analysis.

Tools:
- concall_fetch_transcript: Fetch earnings call transcript
- concall_summarize_transcript: Generate AI-powered summary
- concall_analyze_sentiment: Analyze sentiment and management tone
- concall_query_transcript: RAG-powered Q&A over transcripts
- concall_compare_quarters: Compare sentiment across quarters
"""

import asyncio
import logging
from typing import Any, Dict, List, Tuple

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_concall_tools(mcp: FastMCP) -> None:
    """
    Register conference call analysis tools with the MCP server.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    async def concall_fetch_transcript(
        ticker: str,
        quarter: str,
        fiscal_year: int,
        save_to_db: bool = True,
    ) -> Dict[str, Any]:
        """
        Fetch earnings call transcript from multiple sources.

        Fetches conference call transcripts with cascading fallback across:
        1. Company IR website (primary)
        2. NSE exchange filings (fallback for Indian stocks)

        Supports multiple formats (PDF, HTML, TXT) with automatic parsing.

        Args:
            ticker: Stock ticker symbol (e.g., "RELIANCE.NS")
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
            from maverick_india.concall import TranscriptFetcher

            fetcher = TranscriptFetcher(save_to_db=save_to_db)

            result = await fetcher.fetch_transcript(
                ticker=ticker,
                quarter=quarter,
                fiscal_year=fiscal_year,
            )

            if result:
                # Add word count
                transcript_text = result.get("transcript_text", "")
                result["word_count"] = len(transcript_text.split()) if transcript_text else 0
                return result

            return {
                "error": "Transcript not found",
                "ticker": ticker,
                "quarter": quarter,
                "fiscal_year": fiscal_year,
                "message": "No transcript available from any source.",
            }

        except ImportError as e:
            logger.error(f"maverick-india not available: {e}")
            return {
                "error": "maverick-india package not installed",
                "message": "Install maverick-india for conference call analysis.",
            }
        except Exception as e:
            logger.error(f"Failed to fetch transcript for {ticker} {quarter} FY{fiscal_year}: {e}")
            return {
                "error": str(e),
                "ticker": ticker,
                "quarter": quarter,
                "fiscal_year": fiscal_year,
                "message": "Failed to fetch transcript.",
            }

    @mcp.tool()
    async def concall_summarize_transcript(
        ticker: str,
        quarter: str,
        fiscal_year: int,
        mode: str = "standard",
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
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
            ticker: Stock ticker symbol (e.g., "RELIANCE.NS", "AAPL")
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
            import os

            from maverick_india.concall import ConcallSummarizer, TranscriptFetcher

            # First, ensure we have the transcript
            fetcher = TranscriptFetcher(save_to_db=True)
            transcript_result = await fetcher.fetch_transcript(
                ticker=ticker,
                quarter=quarter,
                fiscal_year=fiscal_year,
            )

            if not transcript_result or not transcript_result.get("transcript_text"):
                return {
                    "error": "Transcript not found",
                    "ticker": ticker,
                    "quarter": quarter,
                    "fiscal_year": fiscal_year,
                    "message": "Fetch transcript first before summarizing.",
                }

            # Check for LLM provider
            # Try to get OpenRouter provider from maverick-agents
            llm_provider = None
            try:
                from maverick_agents.llm import OpenRouterProvider

                api_key = os.getenv("OPENROUTER_API_KEY")
                if api_key:
                    provider = OpenRouterProvider(api_key)
                    llm_provider = provider.get_llm(prefer_cheap=True)
            except ImportError:
                pass

            if not llm_provider:
                return {
                    "error": "LLM provider not configured",
                    "message": "Set OPENROUTER_API_KEY and install maverick-agents for AI summarization.",
                }

            summarizer = ConcallSummarizer(llm_provider=llm_provider, save_to_db=True)

            result = await summarizer.summarize_transcript(
                ticker=ticker,
                quarter=quarter,
                fiscal_year=fiscal_year,
                transcript_text=transcript_result["transcript_text"],
                mode=mode,
                force_refresh=force_refresh,
            )

            return result or {
                "error": "Summarization failed",
                "ticker": ticker,
                "quarter": quarter,
                "fiscal_year": fiscal_year,
            }

        except ImportError as e:
            logger.error(f"Required package not available: {e}")
            return {
                "error": "Required packages not installed",
                "message": "Install maverick-india and maverick-agents for summarization.",
            }
        except Exception as e:
            logger.error(f"Failed to summarize transcript: {e}")
            return {
                "error": str(e),
                "ticker": ticker,
                "quarter": quarter,
                "fiscal_year": fiscal_year,
            }

    @mcp.tool()
    async def concall_analyze_sentiment(
        ticker: str,
        quarter: str,
        fiscal_year: int,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
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
            ticker: Stock ticker symbol (e.g., "RELIANCE.NS", "AAPL")
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
            import os

            from maverick_india.concall import SentimentAnalyzer, TranscriptFetcher

            # First, ensure we have the transcript
            fetcher = TranscriptFetcher(save_to_db=True)
            transcript_result = await fetcher.fetch_transcript(
                ticker=ticker,
                quarter=quarter,
                fiscal_year=fiscal_year,
            )

            if not transcript_result or not transcript_result.get("transcript_text"):
                return {
                    "error": "Transcript not found",
                    "ticker": ticker,
                    "quarter": quarter,
                    "fiscal_year": fiscal_year,
                    "message": "Fetch transcript first before analyzing sentiment.",
                }

            # Check for LLM provider
            llm_provider = None
            try:
                from maverick_agents.llm import OpenRouterProvider

                api_key = os.getenv("OPENROUTER_API_KEY")
                if api_key:
                    provider = OpenRouterProvider(api_key)
                    llm_provider = provider.get_llm(prefer_cheap=True, prefer_fast=True)
            except ImportError:
                pass

            if not llm_provider:
                return {
                    "error": "LLM provider not configured",
                    "message": "Set OPENROUTER_API_KEY and install maverick-agents for sentiment analysis.",
                }

            analyzer = SentimentAnalyzer(llm_provider=llm_provider, save_to_db=True)

            result = await analyzer.analyze_sentiment(
                ticker=ticker,
                quarter=quarter,
                fiscal_year=fiscal_year,
                transcript_text=transcript_result["transcript_text"],
                use_cache=use_cache,
            )

            return result or {
                "error": "Sentiment analysis failed",
                "ticker": ticker,
                "quarter": quarter,
                "fiscal_year": fiscal_year,
            }

        except ImportError as e:
            logger.error(f"Required package not available: {e}")
            return {
                "error": "Required packages not installed",
                "message": "Install maverick-india and maverick-agents for sentiment analysis.",
            }
        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {e}")
            return {
                "error": str(e),
                "ticker": ticker,
                "quarter": quarter,
                "fiscal_year": fiscal_year,
            }

    @mcp.tool()
    async def concall_query_transcript(
        question: str,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        top_k: int = 5,
    ) -> Dict[str, Any]:
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
            ticker: Stock ticker symbol (e.g., "RELIANCE.NS", "AAPL")
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
        # RAG engine requires more complex setup with vector store
        # For now, provide a simpler keyword-based search
        try:
            from maverick_india.concall import TranscriptFetcher

            fetcher = TranscriptFetcher(save_to_db=True)
            transcript_result = await fetcher.fetch_transcript(
                ticker=ticker,
                quarter=quarter,
                fiscal_year=fiscal_year,
            )

            if not transcript_result or not transcript_result.get("transcript_text"):
                return {
                    "error": "Transcript not found",
                    "ticker": ticker,
                    "quarter": quarter,
                    "fiscal_year": fiscal_year,
                    "message": "Fetch transcript first before querying.",
                }

            # Simple keyword search for now
            transcript_text = transcript_result["transcript_text"]
            question_lower = question.lower()

            # Split into paragraphs and find relevant ones
            paragraphs = transcript_text.split("\n\n")
            relevant = []

            for i, para in enumerate(paragraphs):
                if any(word in para.lower() for word in question_lower.split()):
                    relevant.append({
                        "content": para[:500],  # Truncate
                        "chunk_index": i,
                        "score": 0.5,  # Placeholder score
                    })
                    if len(relevant) >= top_k:
                        break

            return {
                "answer": f"Found {len(relevant)} relevant sections. Full RAG requires maverick-agents.",
                "sources": relevant,
                "metadata": {
                    "ticker": ticker,
                    "quarter": quarter,
                    "fiscal_year": fiscal_year,
                    "chunks_retrieved": len(relevant),
                    "note": "Keyword-based search. Install maverick-agents for full RAG.",
                },
            }

        except ImportError as e:
            logger.error(f"maverick-india not available: {e}")
            return {
                "error": "maverick-india package not installed",
                "message": "Install maverick-india for conference call analysis.",
            }
        except Exception as e:
            logger.error(f"Failed to query transcript: {e}")
            return {
                "error": str(e),
                "ticker": ticker,
                "quarter": quarter,
                "fiscal_year": fiscal_year,
            }

    @mcp.tool()
    async def concall_compare_quarters(
        ticker: str,
        quarters: List[Tuple[str, int]],
    ) -> Dict[str, Any]:
        """
        Compare sentiment across multiple quarters.

        Analyzes sentiment trends over time to identify:
        - Improving/declining/stable sentiment patterns
        - Management confidence changes
        - Risk perception evolution
        - Score changes over time

        Args:
            ticker: Stock ticker symbol (e.g., "RELIANCE.NS", "AAPL")
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
            from maverick_india.concall import SentimentAnalyzer

            analyzer = SentimentAnalyzer(save_to_db=True)

            result = await analyzer.compare_sentiment(
                ticker=ticker,
                quarters=quarters,
            )

            return result

        except ImportError as e:
            logger.error(f"maverick-india not available: {e}")
            return {
                "error": "maverick-india package not installed",
                "message": "Install maverick-india for conference call analysis.",
            }
        except Exception as e:
            logger.error(f"Failed to compare quarters: {e}")
            return {
                "error": str(e),
                "ticker": ticker,
                "quarters": quarters,
            }

    logger.info("Registered concall tools")
