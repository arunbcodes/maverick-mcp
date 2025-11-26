"""
Configuration interfaces.

This module defines abstract interfaces for configuration access.
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IConfigProvider(Protocol):
    """
    Interface for configuration access.

    This interface defines the contract for accessing application configuration
    in a type-safe manner.

    Implemented by: Each package's config module
    """

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key (dot notation supported, e.g., "database.host")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        ...

    def get_str(self, key: str, default: str = "") -> str:
        """
        Get string configuration value.

        Args:
            key: Configuration key
            default: Default value

        Returns:
            String configuration value
        """
        ...

    def get_int(self, key: str, default: int = 0) -> int:
        """
        Get integer configuration value.

        Args:
            key: Configuration key
            default: Default value

        Returns:
            Integer configuration value
        """
        ...

    def get_float(self, key: str, default: float = 0.0) -> float:
        """
        Get float configuration value.

        Args:
            key: Configuration key
            default: Default value

        Returns:
            Float configuration value
        """
        ...

    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get boolean configuration value.

        Args:
            key: Configuration key
            default: Default value

        Returns:
            Boolean configuration value
        """
        ...

    def get_list(self, key: str, default: list | None = None) -> list:
        """
        Get list configuration value.

        Args:
            key: Configuration key
            default: Default value

        Returns:
            List configuration value
        """
        ...

    def get_dict(self, key: str, default: dict | None = None) -> dict:
        """
        Get dictionary configuration value.

        Args:
            key: Configuration key
            default: Default value

        Returns:
            Dictionary configuration value
        """
        ...

    def get_section(self, section: str) -> dict[str, Any]:
        """
        Get entire configuration section.

        Args:
            section: Section name

        Returns:
            Dictionary with all section values
        """
        ...

    def has(self, key: str) -> bool:
        """
        Check if configuration key exists.

        Args:
            key: Configuration key

        Returns:
            True if key exists
        """
        ...

    def get_all(self) -> dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Dictionary with all configuration
        """
        ...
