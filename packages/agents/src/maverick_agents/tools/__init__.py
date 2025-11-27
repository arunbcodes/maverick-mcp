"""
Agent tools for financial analysis.

Provides persona-aware tools for:
- Sentiment analysis (news, market breadth, sector rotation)
- More tools to be added as needed
"""

from maverick_agents.tools.base import PersonaAwareTool
from maverick_agents.tools.sentiment import (
    MarketBreadthInput,
    MarketBreadthTool,
    MarketDataProviderProtocol,
    NewsSentimentTool,
    SectorSentimentTool,
    SentimentInput,
    SettingsProtocol,
)

__all__ = [
    # Base tool
    "PersonaAwareTool",
    # Sentiment tools
    "NewsSentimentTool",
    "MarketBreadthTool",
    "SectorSentimentTool",
    "SentimentInput",
    "MarketBreadthInput",
    # Protocols
    "MarketDataProviderProtocol",
    "SettingsProtocol",
]
