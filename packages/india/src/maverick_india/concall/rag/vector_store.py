"""
Vector Store Manager for Conference Call RAG.

Manages Chroma vector database for semantic search over transcripts.
Handles embeddings, indexing, and retrieval operations.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class EmbeddingFunctionProtocol(Protocol):
    """Protocol for embedding functions."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Embed a query."""
        ...


class VectorStoreManager:
    """
    Manage vector store for conference call transcripts.

    Provides a unified interface for:
    - Creating/loading Chroma collections
    - Generating embeddings
    - Storing and retrieving transcript chunks
    - Managing metadata per transcript

    Design Philosophy:
        - Lightweight: Uses local Chroma database
        - Efficient: Caches embeddings to avoid recomputation
        - Organized: One collection per transcript (ticker_quarter_year)
        - Metadata-rich: Stores source info with each chunk

    Attributes:
        persist_directory: Path to Chroma database storage
        embedding_model: Embedding function (OpenAI or sentence-transformers)
        chunk_size: Size of text chunks in characters
        chunk_overlap: Overlap between chunks

    Example:
        >>> manager = VectorStoreManager()
        >>> # Index transcript
        >>> await manager.index_transcript(
        ...     "RELIANCE.NS", "Q1", 2025, transcript_text
        ... )
        >>> # Query
        >>> results = await manager.query(
        ...     "RELIANCE.NS", "Q1", 2025, "What was revenue?"
        ... )
    """

    def __init__(
        self,
        persist_directory: str | None = None,
        embedding_model: str = "openai",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize vector store manager.

        Args:
            persist_directory: Path to store Chroma database (default: ~/.maverick_mcp/chroma_db)
            embedding_model: Embedding model to use ("openai" or "sentence-transformers")
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between consecutive chunks
        """
        self.persist_directory = persist_directory or str(
            Path.home() / ".maverick_mcp" / "chroma_db"
        )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Create persist directory
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Lazy initialization for dependencies
        self._embedding_function: EmbeddingFunctionProtocol | None = None
        self._embedding_model = embedding_model
        self._text_splitter = None

        logger.info(
            f"VectorStoreManager initialized: {self.persist_directory}, "
            f"chunk_size={chunk_size}, overlap={chunk_overlap}"
        )

    def _get_embedding_function(self) -> EmbeddingFunctionProtocol:
        """Get or create embedding function (lazy initialization)."""
        if self._embedding_function is None:
            if self._embedding_model == "openai":
                from langchain_openai import OpenAIEmbeddings

                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError(
                        "OPENAI_API_KEY environment variable required for OpenAI embeddings"
                    )
                self._embedding_function = OpenAIEmbeddings(
                    model="text-embedding-3-small"  # Cost-effective embedding model
                )
            else:
                # Future: Add sentence-transformers support
                raise ValueError(f"Unsupported embedding model: {self._embedding_model}")

        return self._embedding_function

    def _get_text_splitter(self):
        """Get or create text splitter (lazy initialization)."""
        if self._text_splitter is None:
            from langchain.text_splitter import RecursiveCharacterTextSplitter

            self._text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
        return self._text_splitter

    def _get_collection_name(self, ticker: str, quarter: str, fiscal_year: int) -> str:
        """
        Get collection name for transcript.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year

        Returns:
            str: Collection name (e.g., "RELIANCE_NS_Q1_2025")
        """
        # Sanitize ticker (remove dots, make alphanumeric)
        clean_ticker = ticker.replace(".", "_").replace("-", "_")
        return f"{clean_ticker}_{quarter}_{fiscal_year}".upper()

    async def index_transcript(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        transcript_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Index transcript into vector store.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year
            transcript_text: Full transcript content
            metadata: Additional metadata to store

        Returns:
            dict: Indexing statistics (chunk_count, collection_name)

        Example:
            >>> stats = await manager.index_transcript(
            ...     "RELIANCE.NS", "Q1", 2025, transcript_text
            ... )
            >>> print(f"Indexed {stats['chunk_count']} chunks")
        """
        from langchain_chroma import Chroma

        collection_name = self._get_collection_name(ticker, quarter, fiscal_year)

        logger.info(
            f"Indexing transcript for {ticker} {quarter} FY{fiscal_year} "
            f"into collection {collection_name}"
        )

        try:
            # Split text into chunks
            text_splitter = self._get_text_splitter()
            chunks = text_splitter.split_text(transcript_text)

            # Prepare metadata for each chunk
            base_metadata = {
                "ticker": ticker,
                "quarter": quarter,
                "fiscal_year": fiscal_year,
                "collection": collection_name,
                **(metadata or {}),
            }

            # Add chunk index to metadata
            metadatas = [
                {**base_metadata, "chunk_index": i} for i in range(len(chunks))
            ]

            # Create/load vector store
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self._get_embedding_function(),
                persist_directory=self.persist_directory,
            )

            # Add documents
            vectorstore.add_texts(texts=chunks, metadatas=metadatas)

            logger.info(
                f"Successfully indexed {len(chunks)} chunks for {ticker} {quarter} FY{fiscal_year}"
            )

            return {
                "chunk_count": len(chunks),
                "collection_name": collection_name,
                "ticker": ticker,
                "quarter": quarter,
                "fiscal_year": fiscal_year,
            }

        except Exception as e:
            logger.error(f"Failed to index transcript: {e}")
            raise

    async def query(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        query_text: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Query vector store for relevant chunks.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year
            query_text: User query
            top_k: Number of results to return

        Returns:
            list: Relevant chunks with content, metadata, and similarity scores

        Example:
            >>> results = await manager.query(
            ...     "RELIANCE.NS", "Q1", 2025,
            ...     "What was the revenue growth?",
            ...     top_k=3
            ... )
            >>> for result in results:
            ...     print(result["content"])
            ...     print(result["score"])
        """
        from langchain_chroma import Chroma

        collection_name = self._get_collection_name(ticker, quarter, fiscal_year)

        logger.info(
            f"Querying collection {collection_name} with: {query_text[:50]}..."
        )

        try:
            # Load vector store
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self._get_embedding_function(),
                persist_directory=self.persist_directory,
            )

            # Similarity search with scores
            results_with_scores = vectorstore.similarity_search_with_score(
                query_text, k=top_k
            )

            # Format results
            formatted_results = []
            for doc, score in results_with_scores:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),  # Similarity score (lower = more similar for some metrics)
                })

            logger.info(f"Found {len(formatted_results)} relevant chunks")
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to query vector store: {e}")
            raise

    def collection_exists(
        self, ticker: str, quarter: str, fiscal_year: int
    ) -> bool:
        """
        Check if collection exists for transcript.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year

        Returns:
            bool: True if collection exists
        """
        from langchain_chroma import Chroma

        collection_name = self._get_collection_name(ticker, quarter, fiscal_year)

        try:
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self._get_embedding_function(),
                persist_directory=self.persist_directory,
            )
            # Try to get collection count
            count = vectorstore._collection.count()
            return count > 0
        except Exception:
            return False

    def delete_collection(
        self, ticker: str, quarter: str, fiscal_year: int
    ) -> None:
        """
        Delete collection for transcript.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Year
        """
        from langchain_chroma import Chroma

        collection_name = self._get_collection_name(ticker, quarter, fiscal_year)

        logger.info(f"Deleting collection {collection_name}")

        try:
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self._get_embedding_function(),
                persist_directory=self.persist_directory,
            )
            vectorstore.delete_collection()
            logger.info(f"Successfully deleted collection {collection_name}")
        except Exception as e:
            logger.warning(f"Failed to delete collection {collection_name}: {e}")

    def get_statistics(self) -> dict[str, Any]:
        """
        Get statistics about vector stores.

        Returns:
            dict: Statistics (total collections, total chunks, etc.)
        """
        try:
            # Get all collections in persist directory
            from chromadb import PersistentClient

            client = PersistentClient(path=self.persist_directory)
            collections = client.list_collections()

            total_chunks = 0
            collection_stats = []

            for collection in collections:
                count = collection.count()
                total_chunks += count
                collection_stats.append({
                    "name": collection.name,
                    "chunk_count": count,
                })

            return {
                "total_collections": len(collections),
                "total_chunks": total_chunks,
                "collections": collection_stats,
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                "total_collections": 0,
                "total_chunks": 0,
                "collections": [],
            }


__all__ = ["VectorStoreManager"]

