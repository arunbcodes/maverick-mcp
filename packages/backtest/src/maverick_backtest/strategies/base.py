"""Base strategy class for VectorBT backtesting."""

from abc import ABC, abstractmethod
from typing import Any

from pandas import DataFrame, Series


class Strategy(ABC):
    """Abstract base class for trading strategies.

    All strategies must implement the generate_signals method which produces
    entry and exit signals based on price data.

    Attributes:
        parameters: Strategy-specific configuration parameters
    """

    def __init__(self, parameters: dict[str, Any] | None = None):
        """Initialize strategy with parameters.

        Args:
            parameters: Strategy parameters (e.g., periods, thresholds)
        """
        self.parameters = parameters or {}

    @abstractmethod
    def generate_signals(self, data: DataFrame) -> tuple[Series, Series]:
        """Generate entry and exit signals.

        Args:
            data: Price data with OHLCV columns (open, high, low, close, volume)

        Returns:
            Tuple of (entry_signals, exit_signals) as boolean Series
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get strategy name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get strategy description."""
        pass

    def validate_parameters(self) -> bool:
        """Validate strategy parameters.

        Returns:
            True if parameters are valid
        """
        return True

    def get_default_parameters(self) -> dict[str, Any]:
        """Get default parameters for the strategy.

        Returns:
            Dictionary of default parameters
        """
        return {}

    def to_dict(self) -> dict[str, Any]:
        """Convert strategy to dictionary representation.

        Returns:
            Dictionary with strategy details
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "default_parameters": self.get_default_parameters(),
        }


__all__ = ["Strategy"]
