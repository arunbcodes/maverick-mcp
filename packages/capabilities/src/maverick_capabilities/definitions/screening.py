"""
Screening capability definitions.
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

# Import service class for type-safe binding
from maverick_services import ScreeningService


SCREENING_CAPABILITIES = [
    Capability(
        id="get_maverick_stocks",
        title="Get Maverick Bullish Stocks",
        description="Get Maverick bullish stock picks with momentum and trend analysis from pre-seeded S&P 500 database.",
        group=CapabilityGroup.SCREENING,
        service_class=ScreeningService,
        method_name="get_maverick_stocks",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=30,
            cache_enabled=True,
            cache_ttl_seconds=300,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="screening_get_maverick_stocks",
            category="screening",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/screening/maverick",
            method="GET",
        ),
        ui=UIConfig(
            expose=True,
            component="MaverickStocksWidget",
            route="/screening/maverick",
            menu_group="Screening",
            menu_label="Bullish Picks",
            menu_order=10,
        ),
        audit=AuditConfig(log=True, log_input=True),
        tags=["bullish", "momentum", "sp500"],
    ),
    Capability(
        id="get_maverick_bear_stocks",
        title="Get Maverick Bearish Stocks",
        description="Get Maverick bearish stock picks for short opportunities.",
        group=CapabilityGroup.SCREENING,
        service_class=ScreeningService,
        method_name="get_maverick_bear_stocks",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=30,
            cache_enabled=True,
            cache_ttl_seconds=300,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="screening_get_maverick_bear_stocks",
            category="screening",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/screening/maverick-bear",
            method="GET",
        ),
        ui=UIConfig(
            expose=True,
            component="BearStocksWidget",
            route="/screening/bearish",
            menu_group="Screening",
            menu_label="Bearish Picks",
            menu_order=20,
        ),
        audit=AuditConfig(log=True, log_input=True),
        tags=["bearish", "short", "sp500"],
    ),
    Capability(
        id="get_breakout_stocks",
        title="Get Breakout Stocks",
        description="Get supply/demand breakout candidates with confirmed uptrend patterns.",
        group=CapabilityGroup.SCREENING,
        service_class=ScreeningService,
        method_name="get_breakout_stocks",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=30,
            cache_enabled=True,
            cache_ttl_seconds=300,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="screening_get_breakout_stocks",
            category="screening",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/screening/breakout",
            method="GET",
        ),
        ui=UIConfig(
            expose=True,
            component="BreakoutStocksWidget",
            route="/screening/breakout",
            menu_group="Screening",
            menu_label="Breakouts",
            menu_order=30,
        ),
        audit=AuditConfig(log=True, log_input=True),
        tags=["breakout", "supply-demand", "pattern"],
    ),
    Capability(
        id="screen_by_criteria",
        title="Screen by Custom Criteria",
        description="Screen stocks by custom technical and fundamental criteria.",
        group=CapabilityGroup.SCREENING,
        service_class=ScreeningService,
        method_name="screen_by_criteria",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=60,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="screening_custom",
            category="screening",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/screening/custom",
            method="POST",
        ),
        ui=UIConfig(
            expose=True,
            component="CustomScreenerPage",
            route="/screening/custom",
            menu_group="Screening",
            menu_label="Custom Screener",
            menu_order=40,
        ),
        audit=AuditConfig(log=True, log_input=True, log_output=True),
        tags=["custom", "filter", "advanced"],
    ),
    Capability(
        id="get_maverick_stocks_by_persona",
        title="Get Stocks by Investor Persona",
        description="Get stock recommendations filtered by investor risk profile (conservative, moderate, aggressive).",
        group=CapabilityGroup.SCREENING,
        service_class=ScreeningService,
        method_name="get_maverick_stocks_by_persona",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=30,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="screening_by_persona",
            category="screening",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/screening/by-persona",
            method="POST",
        ),
        audit=AuditConfig(log=True, log_input=True),
        tags=["persona", "risk-profile", "personalized"],
    ),
]
