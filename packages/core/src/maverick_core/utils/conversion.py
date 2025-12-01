"""
Type Conversion Utilities.

Provides safe conversion functions for financial data types,
handling None values, invalid inputs, and precision requirements.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


def to_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    """
    Safely convert value to Decimal.

    Handles None, floats, ints, strings, and existing Decimals.
    Uses string conversion to avoid float precision issues.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Decimal representation of the value

    Examples:
        >>> to_decimal(123.45)
        Decimal('123.45')
        >>> to_decimal(None)
        Decimal('0')
        >>> to_decimal("invalid", Decimal("1"))
        Decimal('1')
    """
    if value is None:
        return default

    if isinstance(value, Decimal):
        return value

    try:
        # Convert to string first to avoid float precision issues
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def to_decimal_or_none(value: Any) -> Decimal | None:
    """
    Safely convert value to Decimal, returning None for invalid/None values.

    Useful for optional fields like pe_ratio where None is meaningful.

    Args:
        value: Value to convert

    Returns:
        Decimal representation or None

    Examples:
        >>> to_decimal_or_none(123.45)
        Decimal('123.45')
        >>> to_decimal_or_none(None)
        None
    """
    if value is None:
        return None

    if isinstance(value, Decimal):
        return value

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def to_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float.

    Handles None, Decimals, ints, strings, and existing floats.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Float representation of the value

    Examples:
        >>> to_float(Decimal("123.45"))
        123.45
        >>> to_float(None)
        0.0
        >>> to_float("invalid", 1.0)
        1.0
    """
    if value is None:
        return default

    if isinstance(value, float):
        return value

    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def to_float_or_none(value: Any) -> float | None:
    """
    Safely convert value to float, returning None for invalid/None values.

    Args:
        value: Value to convert

    Returns:
        Float representation or None

    Examples:
        >>> to_float_or_none(Decimal("123.45"))
        123.45
        >>> to_float_or_none(None)
        None
    """
    if value is None:
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def to_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to integer.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Integer representation of the value

    Examples:
        >>> to_int("123")
        123
        >>> to_int(None)
        0
        >>> to_int("invalid", -1)
        -1
    """
    if value is None:
        return default

    if isinstance(value, int) and not isinstance(value, bool):
        return value

    try:
        return int(float(value))  # Handle "123.45" -> 123
    except (ValueError, TypeError):
        return default


def round_price(value: Any, decimals: int = 2, default: float = 0.0) -> float:
    """
    Round a price value to specified decimal places.

    Combines to_float conversion with rounding in one step.

    Args:
        value: Value to round
        decimals: Number of decimal places
        default: Default if conversion fails

    Returns:
        Rounded float value

    Examples:
        >>> round_price(123.456789)
        123.46
        >>> round_price(Decimal("99.999"), 2)
        100.0
    """
    float_val = to_float(value, default)
    return round(float_val, decimals)


def get_with_default(
    data: dict[str, Any],
    key: str,
    default: Any = None,
    alt_keys: list[str] | None = None,
) -> Any:
    """
    Get value from dict with fallback to alternate keys.

    Useful when field names vary between data sources.

    Args:
        data: Dictionary to get value from
        key: Primary key to look for
        default: Default if not found
        alt_keys: Alternative keys to try

    Returns:
        Value from dict or default

    Examples:
        >>> d = {"rsi_14": 65, "rsi": 60}
        >>> get_with_default(d, "rsi_14", 0, ["rsi"])
        65
        >>> get_with_default(d, "RSI", 0, ["rsi_14", "rsi"])
        65
    """
    if key in data:
        return data[key]

    if alt_keys:
        for alt_key in alt_keys:
            if alt_key in data:
                return data[alt_key]

    return default


def decimal_from_dict(
    data: dict[str, Any],
    key: str,
    default: Decimal = Decimal("0"),
    alt_keys: list[str] | None = None,
) -> Decimal:
    """
    Extract and convert a value from dict to Decimal.

    Combines get_with_default and to_decimal.

    Args:
        data: Dictionary to get value from
        key: Primary key to look for
        default: Default Decimal value
        alt_keys: Alternative keys to try

    Returns:
        Decimal value

    Examples:
        >>> d = {"price": "123.45"}
        >>> decimal_from_dict(d, "price")
        Decimal('123.45')
    """
    value = get_with_default(data, key, None, alt_keys)
    return to_decimal(value, default)


def float_from_dict(
    data: dict[str, Any],
    key: str,
    default: float = 0.0,
    alt_keys: list[str] | None = None,
) -> float:
    """
    Extract and convert a value from dict to float.

    Combines get_with_default and to_float.

    Args:
        data: Dictionary to get value from
        key: Primary key to look for
        default: Default float value
        alt_keys: Alternative keys to try

    Returns:
        Float value

    Examples:
        >>> d = {"rsi_14": "65.5", "rsi": 60}
        >>> float_from_dict(d, "rsi_14", 0.0, ["rsi"])
        65.5
    """
    value = get_with_default(data, key, None, alt_keys)
    return to_float(value, default)


def int_from_dict(
    data: dict[str, Any],
    key: str,
    default: int = 0,
    alt_keys: list[str] | None = None,
) -> int:
    """
    Extract and convert a value from dict to int.

    Combines get_with_default and to_int.

    Args:
        data: Dictionary to get value from
        key: Primary key to look for
        default: Default int value
        alt_keys: Alternative keys to try

    Returns:
        Integer value

    Examples:
        >>> d = {"volume": "1000000"}
        >>> int_from_dict(d, "volume")
        1000000
    """
    value = get_with_default(data, key, None, alt_keys)
    return to_int(value, default)


__all__ = [
    "to_decimal",
    "to_decimal_or_none",
    "to_float",
    "to_float_or_none",
    "to_int",
    "round_price",
    "get_with_default",
    "decimal_from_dict",
    "float_from_dict",
    "int_from_dict",
]
