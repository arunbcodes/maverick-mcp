"""
Agent tools for financial analysis.

Provides persona-aware tools for:
- Sentiment analysis (news, market breadth, sector rotation)
- Risk management (position sizing, stop loss, portfolio risk)
"""

from maverick_agents.tools.base import PersonaAwareTool
from maverick_agents.tools.risk_management import (
    PositionSizeInput,
    PositionSizeTool,
    RiskMetricsInput,
    RiskMetricsTool,
    StockDataProviderProtocol,
    TechnicalAnalysisProtocol,
    TechnicalStopsInput,
    TechnicalStopsTool,
)
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
    # Risk management tools
    "PositionSizeTool",
    "TechnicalStopsTool",
    "RiskMetricsTool",
    "PositionSizeInput",
    "TechnicalStopsInput",
    "RiskMetricsInput",
    # Protocols
    "MarketDataProviderProtocol",
    "SettingsProtocol",
    "StockDataProviderProtocol",
    "TechnicalAnalysisProtocol",
]
