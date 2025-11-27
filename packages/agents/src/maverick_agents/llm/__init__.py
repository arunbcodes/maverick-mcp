"""
LLM providers and factory.

Provides integration with various LLM providers including:
- OpenRouter (with intelligent model selection)
- Ollama (local inference)
- Factory function for automatic provider selection
"""

from maverick_agents.llm.factory import get_llm
from maverick_agents.llm.ollama import (
    check_ollama_available,
    get_ollama_llm,
    list_ollama_models,
)
from maverick_agents.llm.openrouter import (
    MODEL_PROFILES,
    ModelProfile,
    OpenRouterProvider,
    TaskType,
    get_openrouter_llm,
)

__all__ = [
    # OpenRouter
    "TaskType",
    "ModelProfile",
    "MODEL_PROFILES",
    "OpenRouterProvider",
    "get_openrouter_llm",
    # Ollama
    "get_ollama_llm",
    "check_ollama_available",
    "list_ollama_models",
    # Factory
    "get_llm",
]
