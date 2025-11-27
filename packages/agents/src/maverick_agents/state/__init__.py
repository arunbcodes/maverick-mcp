"""
State definitions for LangGraph agent workflows.

These TypedDict classes define the state structure for various agent workflows.
"""

from maverick_agents.state.definitions import (
    BaseAgentState,
    BacktestingWorkflowState,
    DeepResearchState,
    MarketAnalysisState,
    PortfolioState,
    RiskManagementState,
    SupervisorState,
    TechnicalAnalysisState,
    take_latest_status,
)

__all__ = [
    "take_latest_status",
    "BaseAgentState",
    "MarketAnalysisState",
    "TechnicalAnalysisState",
    "RiskManagementState",
    "PortfolioState",
    "SupervisorState",
    "DeepResearchState",
    "BacktestingWorkflowState",
]
