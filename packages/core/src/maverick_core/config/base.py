"""
Base configuration utilities.

Provides utilities for loading configuration from environment variables
with type safety and defaults.
"""

from __future__ import annotations

import os
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


def clean_env_var(var_name: str, default: str | None = None) -> str | None:
    """
    Clean environment variable value to handle comments.

    Args:
        var_name: Environment variable name
        default: Default value if not set

    Returns:
        Cleaned environment variable value
    """
    value = os.getenv(var_name, default)
    if value and isinstance(value, str):
        # Remove any trailing comments (anything after # that's not inside quotes)
        return value.split("#", 1)[0].strip()
    return value


def get_env_int(var_name: str, default: int = 0) -> int:
    """
    Get integer environment variable.

    Args:
        var_name: Environment variable name
        default: Default value if not set or invalid

    Returns:
        Integer value
    """
    value = clean_env_var(var_name, str(default))
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default


def get_env_float(var_name: str, default: float = 0.0) -> float:
    """
    Get float environment variable.

    Args:
        var_name: Environment variable name
        default: Default value if not set or invalid

    Returns:
        Float value
    """
    value = clean_env_var(var_name, str(default))
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default


def get_env_bool(var_name: str, default: bool = False) -> bool:
    """
    Get boolean environment variable.

    Args:
        var_name: Environment variable name
        default: Default value if not set

    Returns:
        Boolean value
    """
    value = clean_env_var(var_name, str(default).lower())
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def get_env_list(
    var_name: str,
    default: list[str] | None = None,
    separator: str = ",",
) -> list[str]:
    """
    Get list from environment variable.

    Args:
        var_name: Environment variable name
        default: Default value if not set
        separator: Separator character (default: comma)

    Returns:
        List of strings
    """
    value = clean_env_var(var_name)
    if value is None:
        return default or []
    return [item.strip() for item in value.split(separator) if item.strip()]


class BaseConfigModel(BaseModel):
    """
    Base class for configuration models.

    Provides common functionality for configuration models including
    environment variable loading and serialization.

    Example:
        >>> class MyConfig(BaseConfigModel):
        ...     host: str = "localhost"
        ...     port: int = 8080
        >>>
        >>> config = MyConfig()
        >>> print(config.to_dict())
    """

    class Config:
        """Pydantic configuration."""

        extra = "allow"  # Allow extra fields for extensibility
        validate_default = True

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump()

    @classmethod
    def from_env(cls, prefix: str = "") -> "BaseConfigModel":
        """
        Create configuration from environment variables.

        Args:
            prefix: Environment variable prefix (e.g., "MAVERICK_")

        Returns:
            Configuration instance
        """
        # Get field names and try to load from env
        values = {}
        for field_name, field_info in cls.model_fields.items():
            env_name = f"{prefix}{field_name.upper()}"
            env_value = os.getenv(env_name)
            if env_value is not None:
                values[field_name] = env_value
        return cls(**values)


__all__ = [
    "BaseConfigModel",
    "clean_env_var",
    "get_env_int",
    "get_env_float",
    "get_env_bool",
    "get_env_list",
]

