"""Ollama local LLM provider.

This module provides integration with Ollama for local LLM inference.
Ollama runs models locally and provides an OpenAI-compatible API.
"""

from __future__ import annotations

import logging
import os

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


def get_ollama_llm(
    base_url: str | None = None,
    model: str | None = None,
    temperature: float = 0.3,
) -> ChatOpenAI:
    """Create Ollama LLM instance with OpenAI-compatible API.

    Args:
        base_url: Base URL of Ollama API (default: http://localhost:11434/v1)
        model: Model name to use (default: from OLLAMA_MODEL env var or "llama2")
        temperature: Temperature for generation

    Returns:
        ChatOpenAI instance configured for Ollama

    Environment Variables:
        OLLAMA_BASE_URL: Base URL for Ollama API (optional)
        OLLAMA_MODEL: Model name (e.g., "gpt-oss-20b", "llama2", "mistral")

    Example:
        >>> llm = get_ollama_llm()
        >>> response = llm.invoke("Analyze AAPL stock")
    """
    # Get configuration from environment or use defaults
    if base_url is None:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    if model is None:
        model = os.getenv("OLLAMA_MODEL", "gpt-oss-20b")

    logger.info(f"Using Ollama model '{model}' at {base_url}")

    # Create ChatOpenAI instance configured for Ollama
    # Ollama's API is OpenAI-compatible, so we can use langchain_openai
    return ChatOpenAI(
        base_url=base_url,
        api_key="ollama",  # Ollama doesn't require real API keys
        model=model,
        temperature=temperature,
        streaming=False,
        request_timeout=120,  # Local models may be slower
    )


def check_ollama_available(base_url: str | None = None) -> bool:
    """Check if Ollama is available and responding.

    Args:
        base_url: Base URL to check (default: from env or http://localhost:11434)

    Returns:
        True if Ollama is available, False otherwise
    """
    import httpx

    if base_url is None:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Remove /v1 suffix if present for the tags endpoint
    base_url = base_url.rstrip("/v1").rstrip("/")

    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"Ollama not available: {e}")
        return False


def list_ollama_models(base_url: str | None = None) -> list[str]:
    """List available Ollama models.

    Args:
        base_url: Base URL to check (default: from env or http://localhost:11434)

    Returns:
        List of available model names
    """
    import httpx

    if base_url is None:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Remove /v1 suffix if present for the tags endpoint
    base_url = base_url.rstrip("/v1").rstrip("/")

    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        return []
    except Exception as e:
        logger.error(f"Error listing Ollama models: {e}")
        return []
