"""
Portfolio capability definitions.
"""

from maverick_capabilities.models import (
    Capability,
    CapabilityGroup,
    ExecutionConfig,
    ExecutionMode,
    MCPConfig,
    APIConfig,
    UIConfig,
    AuditConfig,
)

from maverick_services import PortfolioService


PORTFOLIO_CAPABILITIES = [
    Capability(
        id="portfolio_add_position",
        title="Add Portfolio Position",
        description="Add or update a position with automatic cost basis averaging.",
        group=CapabilityGroup.PORTFOLIO,
        service_class=PortfolioService,
        method_name="add_position",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=10,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="portfolio_add_position",
            category="portfolio",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/portfolio/positions",
            method="POST",
        ),
        ui=UIConfig(
            expose=True,
            component="AddPositionModal",
        ),
        audit=AuditConfig(
            log=True,
            log_input=True,
            log_output=True,
            retention_days=365,  # Keep position changes for tax purposes
        ),
        tags=["position", "buy", "cost-basis"],
    ),
    Capability(
        id="portfolio_get_positions",
        title="Get Portfolio Positions",
        description="Get all positions with live P&L calculations.",
        group=CapabilityGroup.PORTFOLIO,
        service_class=PortfolioService,
        method_name="get_portfolio",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=30,
            cache_enabled=True,
            cache_ttl_seconds=60,  # Refresh every minute
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="portfolio_get_positions",
            category="portfolio",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/portfolio/positions",
            method="GET",
        ),
        ui=UIConfig(
            expose=True,
            component="PortfolioPage",
            route="/portfolio",
            menu_group="Portfolio",
            menu_label="Holdings",
            menu_order=10,
        ),
        audit=AuditConfig(log=True, log_input=True),
        tags=["positions", "holdings", "pnl"],
    ),
    Capability(
        id="portfolio_remove_position",
        title="Remove Portfolio Position",
        description="Remove partial or full position from portfolio.",
        group=CapabilityGroup.PORTFOLIO,
        service_class=PortfolioService,
        method_name="remove_position",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=10,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="portfolio_remove_position",
            category="portfolio",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/portfolio/positions/{ticker}",
            method="DELETE",
        ),
        audit=AuditConfig(
            log=True,
            log_input=True,
            log_output=True,
            retention_days=365,
        ),
        tags=["position", "sell", "remove"],
    ),
    Capability(
        id="portfolio_clear",
        title="Clear Portfolio",
        description="Clear all positions from portfolio (requires confirmation).",
        group=CapabilityGroup.PORTFOLIO,
        service_class=PortfolioService,
        method_name="clear_portfolio",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=10,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="portfolio_clear",
            category="portfolio",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/portfolio/clear",
            method="POST",
        ),
        audit=AuditConfig(
            log=True,
            log_input=True,
            log_output=True,
            retention_days=365,
        ),
        tags=["clear", "reset", "dangerous"],
    ),
    Capability(
        id="portfolio_summary",
        title="Get Portfolio Summary",
        description="Get portfolio summary with total value, P&L, and allocation breakdown.",
        group=CapabilityGroup.PORTFOLIO,
        service_class=PortfolioService,
        method_name="get_portfolio_summary",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=30,
            cache_enabled=True,
            cache_ttl_seconds=60,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="portfolio_summary",
            category="portfolio",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/portfolio/summary",
            method="GET",
        ),
        ui=UIConfig(
            expose=True,
            component="PortfolioSummaryWidget",
        ),
        audit=AuditConfig(log=True),
        tags=["summary", "overview", "allocation"],
    ),
]
