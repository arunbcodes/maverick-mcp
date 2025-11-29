"""
Fallback strategies for circuit breakers to provide graceful degradation.

This module provides base classes and generic fallback patterns.
Specific fallback implementations (like database fallbacks) should be
in their respective packages (maverick-data, maverick-server, etc.)
"""

import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from maverick_core.exceptions import DataNotFoundError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class FallbackStrategy(ABC, Generic[T]):
    """Base class for fallback strategies."""

    @abstractmethod
    async def execute_async(self, *args, **kwargs) -> T:
        """Execute the fallback strategy asynchronously."""
        pass

    @abstractmethod
    def execute_sync(self, *args, **kwargs) -> T:
        """Execute the fallback strategy synchronously."""
        pass


class FallbackChain(Generic[T]):
    """
    Chain of fallback strategies to execute in order.
    Stops at the first successful strategy.
    """

    def __init__(self, strategies: list[FallbackStrategy[T]]):
        """Initialize fallback chain with ordered strategies."""
        self.strategies = strategies

    async def execute_async(self, *args, **kwargs) -> T:
        """Execute strategies asynchronously until one succeeds."""
        last_error = None

        for i, strategy in enumerate(self.strategies):
            try:
                logger.info(
                    f"Executing fallback strategy {i + 1}/{len(self.strategies)}: {strategy.__class__.__name__}"
                )
                result = await strategy.execute_async(*args, **kwargs)
                if result is not None:  # Success
                    return result
            except Exception as e:
                logger.warning(
                    f"Fallback strategy {strategy.__class__.__name__} failed: {e}"
                )
                last_error = e
                continue

        # All strategies failed
        if last_error:
            raise last_error
        raise DataNotFoundError("All fallback strategies failed")

    def execute_sync(self, *args, **kwargs) -> T:
        """Execute strategies synchronously until one succeeds."""
        last_error = None

        for i, strategy in enumerate(self.strategies):
            try:
                logger.info(
                    f"Executing fallback strategy {i + 1}/{len(self.strategies)}: {strategy.__class__.__name__}"
                )
                result = strategy.execute_sync(*args, **kwargs)
                if result is not None:  # Success
                    return result
            except Exception as e:
                logger.warning(
                    f"Fallback strategy {strategy.__class__.__name__} failed: {e}"
                )
                last_error = e
                continue

        # All strategies failed
        if last_error:
            raise last_error
        raise DataNotFoundError("All fallback strategies failed")


class DefaultFallbackStrategy(FallbackStrategy[T]):
    """A simple fallback that returns a default value."""

    def __init__(self, default_value: T):
        """Initialize with a default value."""
        self.default_value = default_value

    async def execute_async(self, *args, **kwargs) -> T:
        """Return default value asynchronously."""
        logger.warning(f"Using default fallback value: {self.default_value}")
        return self.default_value

    def execute_sync(self, *args, **kwargs) -> T:
        """Return default value synchronously."""
        logger.warning(f"Using default fallback value: {self.default_value}")
        return self.default_value


class EmptyDictFallback(FallbackStrategy[dict]):
    """Fallback that returns an empty dict with metadata."""

    def __init__(self, source_name: str = "fallback"):
        """Initialize with source name for metadata."""
        self.source_name = source_name

    async def execute_async(self, *args, **kwargs) -> dict:
        """Return empty dict asynchronously."""
        return self._create_fallback_dict()

    def execute_sync(self, *args, **kwargs) -> dict:
        """Return empty dict synchronously."""
        return self._create_fallback_dict()

    def _create_fallback_dict(self) -> dict:
        """Create fallback dictionary with metadata."""
        from datetime import UTC, datetime

        return {
            "data": {},
            "metadata": {
                "source": self.source_name,
                "timestamp": datetime.now(UTC).isoformat(),
                "is_fallback": True,
                "message": "Data temporarily unavailable",
            },
        }


class EmptyListFallback(FallbackStrategy[list]):
    """Fallback that returns an empty list."""

    async def execute_async(self, *args, **kwargs) -> list:
        """Return empty list asynchronously."""
        logger.warning("Using empty list fallback")
        return []

    def execute_sync(self, *args, **kwargs) -> list:
        """Return empty list synchronously."""
        logger.warning("Using empty list fallback")
        return []

