"""
Conference Call RAG (Retrieval-Augmented Generation) Module.

This module provides semantic search and Q&A capabilities over conference call transcripts
using vector embeddings and LLM-powered response generation.

Components:
    - ConcallRAGEngine: Main RAG engine for Q&A over transcripts
    - VectorStoreManager: Manages Chroma vector database for embeddings
"""

from maverick_india.concall.rag.engine import ConcallRAGEngine
from maverick_india.concall.rag.vector_store import VectorStoreManager

__all__ = [
    "ConcallRAGEngine",
    "VectorStoreManager",
]

