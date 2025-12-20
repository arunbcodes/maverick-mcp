"""
Risk metrics capability definitions.
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

from maverick_services import RiskMetricsService


RISK_CAPABILITIES = [
    Capability(
        id="calculate_var",
        title="Calculate Value at Risk",
        description="Calculate Value at Risk (VaR) for a portfolio or position.",
        group=CapabilityGroup.RISK,
        service_class=RiskMetricsService,
        method_name="calculate_var",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=30,
            cache_enabled=True,
            cache_ttl_seconds=300,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="risk_var",
            category="risk",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/risk/var",
            method="POST",
        ),
        audit=AuditConfig(log=True, log_input=True),
        tags=["var", "value-at-risk", "quantitative"],
    ),
    Capability(
        id="calculate_beta",
        title="Calculate Beta",
        description="Calculate beta relative to a benchmark (default SPY).",
        group=CapabilityGroup.RISK,
        service_class=RiskMetricsService,
        method_name="calculate_beta",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=30,
            cache_enabled=True,
            cache_ttl_seconds=600,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="risk_beta",
            category="risk",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/risk/beta",
            method="POST",
        ),
        audit=AuditConfig(log=True, log_input=True),
        tags=["beta", "benchmark", "correlation"],
    ),
    Capability(
        id="calculate_volatility",
        title="Calculate Volatility",
        description="Calculate historical volatility and volatility metrics.",
        group=CapabilityGroup.RISK,
        service_class=RiskMetricsService,
        method_name="calculate_volatility",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=30,
            cache_enabled=True,
            cache_ttl_seconds=300,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="risk_volatility",
            category="risk",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/risk/volatility",
            method="POST",
        ),
        audit=AuditConfig(log=True, log_input=True),
        tags=["volatility", "standard-deviation", "risk"],
    ),
    Capability(
        id="stress_test",
        title="Run Stress Test",
        description="Run stress test scenarios on a portfolio.",
        group=CapabilityGroup.RISK,
        service_class=RiskMetricsService,
        method_name="run_stress_test",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=60,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="risk_stress_test",
            category="risk",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/risk/stress-test",
            method="POST",
        ),
        ui=UIConfig(
            expose=True,
            component="StressTestPage",
            route="/risk/stress-test",
            menu_group="Risk",
            menu_label="Stress Test",
            menu_order=20,
        ),
        audit=AuditConfig(log=True, log_input=True, log_output=True),
        tags=["stress-test", "scenario", "downside"],
    ),
    Capability(
        id="risk_summary",
        title="Get Risk Summary",
        description="Get comprehensive risk summary with all metrics.",
        group=CapabilityGroup.RISK,
        service_class=RiskMetricsService,
        method_name="get_risk_summary",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=120,
            cache_enabled=True,
            cache_ttl_seconds=300,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="risk_summary",
            category="risk",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/risk/summary",
            method="POST",
        ),
        ui=UIConfig(
            expose=True,
            component="RiskDashboard",
            route="/risk",
            menu_group="Risk",
            menu_label="Risk Dashboard",
            menu_order=10,
        ),
        audit=AuditConfig(log=True, log_input=True, log_output=True),
        tags=["summary", "comprehensive", "dashboard"],
    ),
]
