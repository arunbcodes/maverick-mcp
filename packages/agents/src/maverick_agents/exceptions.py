"""
Custom exceptions for maverick-agents package.

Provides domain-specific exceptions for agent operations.
"""


class AgentError(Exception):
    """Base exception for agent-related errors."""

    pass


class AgentInitializationError(AgentError):
    """Exception raised when agent initialization fails."""

    def __init__(self, agent_type: str, reason: str):
        self.agent_type = agent_type
        self.reason = reason
        super().__init__(f"Failed to initialize {agent_type}: {reason}")


class AgentExecutionError(AgentError):
    """Exception raised when agent execution fails."""

    def __init__(self, agent_type: str, operation: str, reason: str):
        self.agent_type = agent_type
        self.operation = operation
        self.reason = reason
        super().__init__(f"{agent_type} failed during {operation}: {reason}")


class QueryClassificationError(AgentError):
    """Exception raised when query classification fails."""

    def __init__(self, query: str, reason: str):
        self.query = query
        self.reason = reason
        super().__init__(f"Failed to classify query '{query[:50]}...': {reason}")


class AgentTimeoutError(AgentError):
    """Exception raised when agent operation times out."""

    def __init__(self, agent_type: str, timeout_seconds: float):
        self.agent_type = agent_type
        self.timeout_seconds = timeout_seconds
        super().__init__(f"{agent_type} timed out after {timeout_seconds}s")


class SynthesisError(AgentError):
    """Exception raised when result synthesis fails."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Failed to synthesize results: {reason}")
