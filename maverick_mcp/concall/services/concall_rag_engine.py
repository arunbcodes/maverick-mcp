"""
Conference Call RAG (Retrieval-Augmented Generation) Engine.

Single Responsibility: Enable Q&A over conference call transcripts.
Open/Closed: Extensible via prompt templates, not code changes.
Liskov Substitution: Compatible with any vector store implementation.
Interface Segregation: Simple, focused Q&A API.
Dependency Inversion: Depends on abstractions (VectorStore, LLM).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from maverick_mcp.concall.models import ConferenceCall
from maverick_mcp.concall.utils import VectorStoreManager
from maverick_mcp.data.models import get_session
from maverick_mcp.providers.openrouter_provider import OpenRouterProvider, TaskType

logger = logging.getLogger(__name__)


class ConcallRAGEngine:
    """
    RAG engine for Q&A over conference call transcripts.

    Enables semantic search and question-answering over earnings call transcripts
    using vector embeddings and LLM-powered response generation.

    Design Philosophy:
        - Index-once: Cache vector embeddings for reuse
        - Context-aware: Retrieve relevant chunks before answering
        - Source-cited: Include transcript excerpts with answers
        - Multi-transcript: Query across multiple quarters/companies

    Attributes:
        vector_manager: Vector store manager for embeddings
        openrouter: OpenRouter provider for LLM access
        auto_index: Automatically index transcripts on first query

    Example:
        >>> rag = ConcallRAGEngine()
        >>>
        >>> # Index transcript
        >>> await rag.index_transcript("RELIANCE.NS", "Q1", 2025)
        >>>
        >>> # Ask questions
        >>> answer = await rag.query(
        ...     "What was the revenue growth in Q1?",
        ...     ticker="RELIANCE.NS",
        ...     quarter="Q1",
        ...     fiscal_year=2025
        ... )
        >>> print(answer["answer"])
        >>> print(answer["sources"])
    """

    def __init__(
        self,
        openrouter_api_key: str | None = None,
        persist_directory: str | None = None,
        auto_index: bool = True,
    ):
        """
        Initialize RAG engine.

        Args:
            openrouter_api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            persist_directory: Path to vector DB storage
            auto_index: Automatically index transcripts on first query
        """
        # Initialize vector store
        self.vector_manager = VectorStoreManager(persist_directory=persist_directory)

        # Initialize OpenRouter
        api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY env var."
            )
        self.openrouter = OpenRouterProvider(api_key)

        self.auto_index = auto_index

        logger.info("ConcallRAGEngine initialized")

    async def index_transcript(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        transcript_text: str | None = None,
        force_reindex: bool = False,
    ) -> dict[str, Any]:
        """
        Index conference call transcript for Q&A.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year
            transcript_text: Transcript content (if None, fetch from database)
            force_reindex: Force re-indexing even if exists

        Returns:
            dict: Indexing statistics

        Example:
            >>> stats = await rag.index_transcript("RELIANCE.NS", "Q1", 2025)
            >>> print(f"Indexed {stats['chunk_count']} chunks")
        """
        ticker = ticker.upper()
        quarter = quarter.upper()

        # Check if already indexed
        if not force_reindex and self.vector_manager.collection_exists(
            ticker, quarter, fiscal_year
        ):
            logger.info(
                f"Transcript for {ticker} {quarter} FY{fiscal_year} already indexed"
            )
            return {
                "status": "already_indexed",
                "ticker": ticker,
                "quarter": quarter,
                "fiscal_year": fiscal_year,
            }

        # Get transcript from database if not provided
        if transcript_text is None:
            transcript_text = self._get_transcript_from_db(ticker, quarter, fiscal_year)
            if not transcript_text:
                raise ValueError(
                    f"No transcript found for {ticker} {quarter} FY{fiscal_year}"
                )

        # Index transcript
        logger.info(f"Indexing transcript for {ticker} {quarter} FY{fiscal_year}")

        stats = await self.vector_manager.index_transcript(
            ticker=ticker,
            quarter=quarter,
            fiscal_year=fiscal_year,
            transcript_text=transcript_text,
            metadata={
                "source": "database",
            },
        )

        stats["status"] = "indexed"
        return stats

    async def query(
        self,
        question: str,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        top_k: int = 5,
        include_sources: bool = True,
    ) -> dict[str, Any]:
        """
        Ask question about conference call transcript.

        Args:
            question: User question
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year
            top_k: Number of context chunks to retrieve
            include_sources: Include source excerpts in response

        Returns:
            dict: Answer with sources and metadata

        Example:
            >>> answer = await rag.query(
            ...     "What was management's outlook?",
            ...     "RELIANCE.NS", "Q1", 2025
            ... )
            >>> print(answer["answer"])
            >>> for source in answer["sources"]:
            ...     print(f"  - {source['content'][:100]}...")
        """
        ticker = ticker.upper()
        quarter = quarter.upper()

        # Auto-index if not indexed
        if self.auto_index and not self.vector_manager.collection_exists(
            ticker, quarter, fiscal_year
        ):
            logger.info(f"Auto-indexing transcript for {ticker} {quarter} FY{fiscal_year}")
            try:
                await self.index_transcript(ticker, quarter, fiscal_year)
            except Exception as e:
                logger.error(f"Failed to auto-index transcript: {e}")
                return {
                    "answer": f"Unable to answer: Transcript not indexed and auto-indexing failed ({e})",
                    "sources": [],
                    "error": str(e),
                }

        try:
            # Retrieve relevant context
            logger.info(
                f"Querying {ticker} {quarter} FY{fiscal_year}: {question[:50]}..."
            )

            results = await self.vector_manager.query(
                ticker=ticker,
                quarter=quarter,
                fiscal_year=fiscal_year,
                query_text=question,
                top_k=top_k,
            )

            if not results:
                return {
                    "answer": "No relevant information found in the transcript.",
                    "sources": [],
                    "metadata": {
                        "ticker": ticker,
                        "quarter": quarter,
                        "fiscal_year": fiscal_year,
                    },
                }

            # Build context from retrieved chunks
            context = "\n\n".join([r["content"] for r in results])

            # Generate answer using LLM
            answer = await self._generate_answer(
                question=question,
                context=context,
                ticker=ticker,
                quarter=quarter,
                fiscal_year=fiscal_year,
            )

            # Format response
            response = {
                "answer": answer,
                "metadata": {
                    "ticker": ticker,
                    "quarter": quarter,
                    "fiscal_year": fiscal_year,
                    "chunks_retrieved": len(results),
                },
            }

            if include_sources:
                response["sources"] = [
                    {
                        "content": r["content"],
                        "score": r["score"],
                        "chunk_index": r["metadata"].get("chunk_index"),
                    }
                    for r in results
                ]

            return response

        except Exception as e:
            logger.error(f"Failed to query transcript: {e}")
            return {
                "answer": f"Error processing question: {e}",
                "sources": [],
                "error": str(e),
            }

    async def _generate_answer(
        self,
        question: str,
        context: str,
        ticker: str,
        quarter: str,
        fiscal_year: int,
    ) -> str:
        """
        Generate answer using LLM with retrieved context.

        Args:
            question: User question
            context: Retrieved context from vector store
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year

        Returns:
            str: Generated answer
        """
        # Build RAG prompt
        prompt = f"""You are a financial analyst assistant. Answer the question based ONLY on the provided context from the earnings call transcript.

**CONTEXT FROM EARNINGS CALL:**
Ticker: {ticker}
Quarter: {quarter}
Fiscal Year: {fiscal_year}

**TRANSCRIPT EXCERPTS:**
{context}

**QUESTION:**
{question}

**INSTRUCTIONS:**
1. Answer the question based on the context above
2. Be specific and cite relevant details from the transcript
3. If the context doesn't contain enough information, say so clearly
4. Use bullet points for structured information
5. Keep the answer concise but informative

**ANSWER:**"""

        # Get LLM for question answering
        llm = self.openrouter.get_llm(
            task_type=TaskType.MARKET_ANALYSIS,
            prefer_cheap=True,  # Cost-effective for Q&A
            temperature=0.3,
            max_tokens=1000,
        )

        # Generate answer
        response = await llm.ainvoke(prompt)
        return response.content

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

    def clear_index(self, ticker: str, quarter: str, fiscal_year: int) -> None:
        """
        Clear vector index for transcript.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year
        """
        logger.info(f"Clearing index for {ticker} {quarter} FY{fiscal_year}")
        self.vector_manager.delete_collection(ticker, quarter, fiscal_year)

    def get_indexed_transcripts(self) -> list[dict[str, Any]]:
        """
        Get list of indexed transcripts.

        Returns:
            list: Indexed transcript info

        Example:
            >>> transcripts = rag.get_indexed_transcripts()
            >>> for t in transcripts:
            ...     print(f"{t['name']}: {t['chunk_count']} chunks")
        """
        stats = self.vector_manager.get_statistics()
        return stats.get("collections", [])

    def get_statistics(self) -> dict[str, Any]:
        """
        Get RAG engine statistics.

        Returns:
            dict: Statistics (indexed transcripts, total chunks, etc.)
        """
        return self.vector_manager.get_statistics()
