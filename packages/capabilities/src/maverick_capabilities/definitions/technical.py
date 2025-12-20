"""
Technical analysis capability definitions.
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

from maverick_services import TechnicalService


TECHNICAL_CAPABILITIES = [
    Capability(
        id="calculate_rsi",
        title="Calculate RSI",
        description="Calculate Relative Strength Index for a stock.",
        group=CapabilityGroup.TECHNICAL,
        service_class=TechnicalService,
        method_name="calculate_rsi",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=15,
            cache_enabled=True,
            cache_ttl_seconds=300,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="technical_rsi",
            category="technical",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/technical/rsi",
            method="POST",
        ),
        audit=AuditConfig(log=True, log_input=True),
        tags=["rsi", "momentum", "oscillator"],
    ),
    Capability(
        id="calculate_macd",
        title="Calculate MACD",
        description="Calculate Moving Average Convergence Divergence indicator.",
        group=CapabilityGroup.TECHNICAL,
        service_class=TechnicalService,
        method_name="calculate_macd",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=15,
            cache_enabled=True,
            cache_ttl_seconds=300,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="technical_macd",
            category="technical",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/technical/macd",
            method="POST",
        ),
        audit=AuditConfig(log=True, log_input=True),
        tags=["macd", "trend", "momentum"],
    ),
    Capability(
        id="calculate_bollinger_bands",
        title="Calculate Bollinger Bands",
        description="Calculate Bollinger Bands for volatility analysis.",
        group=CapabilityGroup.TECHNICAL,
        service_class=TechnicalService,
        method_name="calculate_bollinger_bands",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=15,
            cache_enabled=True,
            cache_ttl_seconds=300,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="technical_bollinger",
            category="technical",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/technical/bollinger",
            method="POST",
        ),
        audit=AuditConfig(log=True, log_input=True),
        tags=["bollinger", "volatility", "bands"],
    ),
    Capability(
        id="calculate_moving_averages",
        title="Calculate Moving Averages",
        description="Calculate SMA and EMA moving averages.",
        group=CapabilityGroup.TECHNICAL,
        service_class=TechnicalService,
        method_name="calculate_moving_averages",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=15,
            cache_enabled=True,
            cache_ttl_seconds=300,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="technical_ma",
            category="technical",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/technical/ma",
            method="POST",
        ),
        audit=AuditConfig(log=True, log_input=True),
        tags=["sma", "ema", "moving-average", "trend"],
    ),
    Capability(
        id="full_technical_analysis",
        title="Full Technical Analysis",
        description="Complete technical analysis with all indicators, support/resistance, and signals.",
        group=CapabilityGroup.TECHNICAL,
        service_class=TechnicalService,
        method_name="get_full_analysis",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=60,
            cache_enabled=True,
            cache_ttl_seconds=300,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="technical_full_analysis",
            category="technical",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/technical/full",
            method="POST",
        ),
        ui=UIConfig(
            expose=True,
            component="TechnicalAnalysisPage",
            route="/technical/{ticker}",
            menu_group="Analysis",
            menu_label="Technical Analysis",
            menu_order=10,
        ),
        audit=AuditConfig(log=True, log_input=True, log_output=True),
        tags=["comprehensive", "all-indicators", "signals"],
    ),
    Capability(
        id="support_resistance",
        title="Calculate Support/Resistance",
        description="Identify key support and resistance levels.",
        group=CapabilityGroup.TECHNICAL,
        service_class=TechnicalService,
        method_name="calculate_support_resistance",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=30,
            cache_enabled=True,
            cache_ttl_seconds=600,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="technical_levels",
            category="technical",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/technical/levels",
            method="POST",
        ),
        audit=AuditConfig(log=True, log_input=True),
        tags=["support", "resistance", "levels", "price-action"],
    ),
]
