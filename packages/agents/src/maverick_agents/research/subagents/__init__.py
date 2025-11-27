"""
Specialized research subagents.

Provides specialized agents for different types of research:
- Fundamental analysis (earnings, valuation, financial health)
- Technical analysis (price patterns, indicators, chart analysis)
- Sentiment analysis (analyst ratings, news sentiment, opinions)
- Competitive analysis (market position, competitors, industry trends)
"""

from maverick_agents.research.subagents.base import (
    BaseSubagent,
    LLMProtocol,
    ResearchTask,
)
from maverick_agents.research.subagents.competitive import CompetitiveResearchAgent
from maverick_agents.research.subagents.fundamental import FundamentalResearchAgent
from maverick_agents.research.subagents.sentiment import SentimentResearchAgent
from maverick_agents.research.subagents.technical import TechnicalResearchAgent

__all__ = [
    # Base classes
    "BaseSubagent",
    "ResearchTask",
    "LLMProtocol",
    # Specialized subagents
    "FundamentalResearchAgent",
    "TechnicalResearchAgent",
    "SentimentResearchAgent",
    "CompetitiveResearchAgent",
]
