"""
Tests for ConcallRAGEngine.

Tests cover:
- Engine initialization
- Transcript indexing
- Query and retrieval
- Auto-indexing
- Source citations
- Error handling
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maverick_mcp.concall.models import ConferenceCall
from maverick_mcp.concall.services.concall_rag_engine import ConcallRAGEngine


class TestConcallRAGEngineInit:
    """Test engine initialization."""

    @patch("maverick_mcp.concall.services.concall_rag_engine.VectorStoreManager")
    @patch("maverick_mcp.concall.services.concall_rag_engine.OpenRouterProvider")
    def test_initialization(self, mock_openrouter_class, mock_vector_class):
        """Test successful initialization."""
        rag = ConcallRAGEngine(openrouter_api_key="test-key")

        assert rag.vector_manager is not None
        assert rag.openrouter is not None
        assert rag.auto_index is True

    @patch("maverick_mcp.concall.services.concall_rag_engine.VectorStoreManager")
    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "env-key"})
    def test_initialization_from_env(self, mock_vector_class):
        """Test initialization from environment."""
        with patch("maverick_mcp.concall.services.concall_rag_engine.OpenRouterProvider"):
            rag = ConcallRAGEngine()
            assert rag.openrouter is not None

    @patch("maverick_mcp.concall.services.concall_rag_engine.VectorStoreManager")
    def test_initialization_without_api_key(self, mock_vector_class):
        """Test initialization fails without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="OpenRouter API key required"):
                ConcallRAGEngine()


class TestConcallRAGEngineIndexing:
    """Test transcript indexing."""

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_rag_engine.VectorStoreManager")
    @patch("maverick_mcp.concall.services.concall_rag_engine.OpenRouterProvider")
    async def test_index_transcript_new(self, mock_openrouter_class, mock_vector_class):
        """Test indexing new transcript."""
        # Mock vector manager
        mock_vector = MagicMock()
        mock_vector.collection_exists.return_value = False
        mock_vector.index_transcript = AsyncMock(return_value={
            "chunk_count": 50,
            "collection_name": "TEST_NS_Q1_2025",
        })
        mock_vector_class.return_value = mock_vector

        rag = ConcallRAGEngine(openrouter_api_key="test-key")

        result = await rag.index_transcript(
            "TEST.NS", "Q1", 2025, "Sample transcript text"
        )

        assert result["status"] == "indexed"
        assert result["chunk_count"] == 50
        mock_vector.index_transcript.assert_called_once()

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_rag_engine.VectorStoreManager")
    @patch("maverick_mcp.concall.services.concall_rag_engine.OpenRouterProvider")
    async def test_index_transcript_already_indexed(
        self, mock_openrouter_class, mock_vector_class
    ):
        """Test skips indexing if already indexed."""
        # Mock vector manager
        mock_vector = MagicMock()
        mock_vector.collection_exists.return_value = True
        mock_vector_class.return_value = mock_vector

        rag = ConcallRAGEngine(openrouter_api_key="test-key")

        result = await rag.index_transcript("TEST.NS", "Q1", 2025, "Sample text")

        assert result["status"] == "already_indexed"
        # Should not call index_transcript if already exists
        assert not hasattr(mock_vector, "index_transcript") or not mock_vector.index_transcript.called

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_rag_engine.VectorStoreManager")
    @patch("maverick_mcp.concall.services.concall_rag_engine.OpenRouterProvider")
    async def test_index_transcript_force_reindex(
        self, mock_openrouter_class, mock_vector_class
    ):
        """Test force re-indexing."""
        # Mock vector manager
        mock_vector = MagicMock()
        mock_vector.collection_exists.return_value = True
        mock_vector.index_transcript = AsyncMock(return_value={
            "chunk_count": 50,
            "collection_name": "TEST_NS_Q1_2025",
        })
        mock_vector_class.return_value = mock_vector

        rag = ConcallRAGEngine(openrouter_api_key="test-key")

        result = await rag.index_transcript(
            "TEST.NS", "Q1", 2025, "Sample text", force_reindex=True
        )

        assert result["status"] == "indexed"
        mock_vector.index_transcript.assert_called_once()

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_rag_engine.VectorStoreManager")
    @patch("maverick_mcp.concall.services.concall_rag_engine.OpenRouterProvider")
    @patch("maverick_mcp.concall.services.concall_rag_engine.get_session")
    async def test_index_transcript_from_database(
        self, mock_get_session, mock_openrouter_class, mock_vector_class
    ):
        """Test indexing fetches transcript from database."""
        # Mock database
        mock_session = MagicMock()
        mock_call = ConferenceCall(
            ticker="TEST.NS",
            quarter="Q1",
            fiscal_year=2025,
            transcript_text="Database transcript",
        )
        mock_session.query().filter().first.return_value = mock_call
        mock_get_session.return_value = mock_session

        # Mock vector manager
        mock_vector = MagicMock()
        mock_vector.collection_exists.return_value = False
        mock_vector.index_transcript = AsyncMock(return_value={
            "chunk_count": 30,
        })
        mock_vector_class.return_value = mock_vector

        rag = ConcallRAGEngine(openrouter_api_key="test-key")

        result = await rag.index_transcript("TEST.NS", "Q1", 2025)

        assert result["status"] == "indexed"
        # Should have called index_transcript with database text
        call_args = mock_vector.index_transcript.call_args
        assert call_args[1]["transcript_text"] == "Database transcript"


class TestConcallRAGEngineQuery:
    """Test querying."""

    @pytest.fixture
    def mock_vector_results(self):
        """Mock vector search results."""
        return [
            {
                "content": "Revenue grew 15% YoY to $10.5B in Q1.",
                "score": 0.85,
                "metadata": {"chunk_index": 5},
            },
            {
                "content": "Management expressed confidence in maintaining this growth trajectory.",
                "score": 0.78,
                "metadata": {"chunk_index": 12},
            },
        ]

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_rag_engine.VectorStoreManager")
    @patch("maverick_mcp.concall.services.concall_rag_engine.OpenRouterProvider")
    async def test_query_success(
        self, mock_openrouter_class, mock_vector_class, mock_vector_results
    ):
        """Test successful query."""
        # Mock vector manager
        mock_vector = MagicMock()
        mock_vector.collection_exists.return_value = True
        mock_vector.query = AsyncMock(return_value=mock_vector_results)
        mock_vector_class.return_value = mock_vector

        # Mock LLM
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Revenue grew 15% year-over-year."
        mock_llm.ainvoke.return_value = mock_response

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        rag = ConcallRAGEngine(openrouter_api_key="test-key", auto_index=False)

        result = await rag.query(
            "What was the revenue growth?", "TEST.NS", "Q1", 2025
        )

        assert result["answer"] == "Revenue grew 15% year-over-year."
        assert len(result["sources"]) == 2
        assert result["metadata"]["chunks_retrieved"] == 2
        assert result["sources"][0]["content"] == mock_vector_results[0]["content"]

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_rag_engine.VectorStoreManager")
    @patch("maverick_mcp.concall.services.concall_rag_engine.OpenRouterProvider")
    async def test_query_no_results(self, mock_openrouter_class, mock_vector_class):
        """Test query with no relevant results."""
        # Mock vector manager
        mock_vector = MagicMock()
        mock_vector.collection_exists.return_value = True
        mock_vector.query = AsyncMock(return_value=[])
        mock_vector_class.return_value = mock_vector

        rag = ConcallRAGEngine(openrouter_api_key="test-key", auto_index=False)

        result = await rag.query(
            "What was the revenue?", "TEST.NS", "Q1", 2025
        )

        assert "No relevant information found" in result["answer"]
        assert len(result["sources"]) == 0

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_rag_engine.VectorStoreManager")
    @patch("maverick_mcp.concall.services.concall_rag_engine.OpenRouterProvider")
    async def test_query_without_sources(
        self, mock_openrouter_class, mock_vector_class, mock_vector_results
    ):
        """Test query without including sources."""
        # Mock vector manager
        mock_vector = MagicMock()
        mock_vector.collection_exists.return_value = True
        mock_vector.query = AsyncMock(return_value=mock_vector_results)
        mock_vector_class.return_value = mock_vector

        # Mock LLM
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Answer text"
        mock_llm.ainvoke.return_value = mock_response

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        rag = ConcallRAGEngine(openrouter_api_key="test-key", auto_index=False)

        result = await rag.query(
            "Question?", "TEST.NS", "Q1", 2025, include_sources=False
        )

        assert "sources" not in result
        assert result["answer"] == "Answer text"

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_rag_engine.VectorStoreManager")
    @patch("maverick_mcp.concall.services.concall_rag_engine.OpenRouterProvider")
    @patch.object(ConcallRAGEngine, "index_transcript")
    async def test_query_auto_index(
        self, mock_index, mock_openrouter_class, mock_vector_class, mock_vector_results
    ):
        """Test auto-indexing on first query."""
        # Mock vector manager
        mock_vector = MagicMock()
        mock_vector.collection_exists.return_value = False  # Not indexed
        mock_vector.query = AsyncMock(return_value=mock_vector_results)
        mock_vector_class.return_value = mock_vector

        # Mock index_transcript
        mock_index.return_value = {"status": "indexed"}

        # Mock LLM
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Answer"
        mock_llm.ainvoke.return_value = mock_response

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        rag = ConcallRAGEngine(openrouter_api_key="test-key", auto_index=True)

        await rag.query("Question?", "TEST.NS", "Q1", 2025)

        # Should have called index_transcript
        mock_index.assert_called_once()


class TestConcallRAGEngineUtilities:
    """Test utility methods."""

    @patch("maverick_mcp.concall.services.concall_rag_engine.VectorStoreManager")
    @patch("maverick_mcp.concall.services.concall_rag_engine.OpenRouterProvider")
    def test_clear_index(self, mock_openrouter_class, mock_vector_class):
        """Test clearing vector index."""
        mock_vector = MagicMock()
        mock_vector.delete_collection = MagicMock()
        mock_vector_class.return_value = mock_vector

        rag = ConcallRAGEngine(openrouter_api_key="test-key")
        rag.clear_index("TEST.NS", "Q1", 2025)

        mock_vector.delete_collection.assert_called_once_with("TEST.NS", "Q1", 2025)

    @patch("maverick_mcp.concall.services.concall_rag_engine.VectorStoreManager")
    @patch("maverick_mcp.concall.services.concall_rag_engine.OpenRouterProvider")
    def test_get_indexed_transcripts(self, mock_openrouter_class, mock_vector_class):
        """Test getting indexed transcripts."""
        mock_vector = MagicMock()
        mock_vector.get_statistics.return_value = {
            "collections": [
                {"name": "TEST_NS_Q1_2025", "chunk_count": 50},
                {"name": "AAPL_Q2_2024", "chunk_count": 45},
            ]
        }
        mock_vector_class.return_value = mock_vector

        rag = ConcallRAGEngine(openrouter_api_key="test-key")
        transcripts = rag.get_indexed_transcripts()

        assert len(transcripts) == 2
        assert transcripts[0]["name"] == "TEST_NS_Q1_2025"

    @patch("maverick_mcp.concall.services.concall_rag_engine.VectorStoreManager")
    @patch("maverick_mcp.concall.services.concall_rag_engine.OpenRouterProvider")
    def test_get_statistics(self, mock_openrouter_class, mock_vector_class):
        """Test getting statistics."""
        mock_vector = MagicMock()
        mock_vector.get_statistics.return_value = {
            "total_collections": 2,
            "total_chunks": 95,
            "collections": [],
        }
        mock_vector_class.return_value = mock_vector

        rag = ConcallRAGEngine(openrouter_api_key="test-key")
        stats = rag.get_statistics()

        assert stats["total_collections"] == 2
        assert stats["total_chunks"] == 95
