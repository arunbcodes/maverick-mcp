"""
Research capability definitions.

These are typically long-running and use async execution.
"""

from maverick_capabilities.models import (
    Capability,
    CapabilityGroup,
    ExecutionConfig,
    ExecutionMode,
    MCPConfig,
    APIConfig,
    UIConfig,
    AgentConfig,
    AuditConfig,
)

# Note: Research capabilities use agents, not direct services
# We'll use a placeholder service class here


class ResearchAgentService:
    """Placeholder for research agent service."""

    pass


RESEARCH_CAPABILITIES = [
    Capability(
        id="deep_research",
        title="Deep Research Analysis",
        description="Comprehensive multi-agent research on a stock or topic. Can run for several minutes.",
        group=CapabilityGroup.RESEARCH,
        service_class=ResearchAgentService,
        method_name="execute_deep_research",
        execution=ExecutionConfig(
            mode=ExecutionMode.ASYNC,  # Long-running, async execution
            timeout_seconds=600,  # 10 minutes max
            queue="research_queue",
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="research_deep_analysis",
            category="research",
            async_pattern="polling",
            status_tool="research_get_status",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/research/deep",
            method="POST",
            status_path="/api/v1/research/{task_id}/status",
        ),
        ui=UIConfig(
            expose=True,
            component="DeepResearchPage",
            route="/research/deep",
            menu_group="Research",
            menu_label="Deep Analysis",
            menu_order=10,
        ),
        agent=AgentConfig(
            can_invoke=True,
            is_agent=True,
            orchestrator="langgraph",
            agent_types=["supervisor"],
        ),
        audit=AuditConfig(
            log=True,
            log_input=True,
            log_output=True,
            retention_days=365,  # Keep research for compliance
        ),
        tags=["deep-research", "multi-agent", "comprehensive"],
    ),
    Capability(
        id="research_company",
        title="Company Research",
        description="Research a specific company with financial analysis.",
        group=CapabilityGroup.RESEARCH,
        service_class=ResearchAgentService,
        method_name="research_company",
        execution=ExecutionConfig(
            mode=ExecutionMode.ASYNC,
            timeout_seconds=300,
            queue="research_queue",
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="research_company",
            category="research",
            async_pattern="polling",
            status_tool="research_get_status",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/research/company",
            method="POST",
        ),
        agent=AgentConfig(
            can_invoke=True,
            is_agent=True,
            agent_types=["fundamental", "competitive"],
        ),
        audit=AuditConfig(log=True, log_input=True, log_output=True),
        tags=["company", "fundamental", "financials"],
    ),
    Capability(
        id="analyze_sentiment",
        title="Sentiment Analysis",
        description="Analyze market sentiment from multiple sources.",
        group=CapabilityGroup.RESEARCH,
        service_class=ResearchAgentService,
        method_name="analyze_sentiment",
        execution=ExecutionConfig(
            mode=ExecutionMode.ASYNC,
            timeout_seconds=180,
            queue="research_queue",
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="research_sentiment",
            category="research",
            async_pattern="polling",
            status_tool="research_get_status",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/research/sentiment",
            method="POST",
        ),
        agent=AgentConfig(
            can_invoke=True,
            is_agent=True,
            agent_types=["sentiment"],
        ),
        audit=AuditConfig(log=True, log_input=True, log_output=True),
        tags=["sentiment", "news", "social"],
    ),
    Capability(
        id="research_get_status",
        title="Get Research Status",
        description="Check the status of a running research task.",
        group=CapabilityGroup.RESEARCH,
        service_class=ResearchAgentService,
        method_name="get_research_status",
        execution=ExecutionConfig(
            mode=ExecutionMode.SYNC,
            timeout_seconds=5,
        ),
        mcp=MCPConfig(
            expose=True,
            tool_name="research_get_status",
            category="research",
        ),
        api=APIConfig(
            expose=True,
            path="/api/v1/research/{task_id}/status",
            method="GET",
        ),
        audit=AuditConfig(log=False),  # Don't log status checks
        tags=["status", "polling"],
    ),
]
