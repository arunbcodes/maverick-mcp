"""
Validation Utility Functions.

Common validation functions used across the codebase.
These return tuples of (is_valid, error_message) for easy integration.
"""

import logging
import re
from datetime import date, datetime
from typing import Optional, Union

logger = logging.getLogger(__name__)

# Common currency codes (ISO 4217)
KNOWN_CURRENCY_CODES = {
    "USD",
    "EUR",
    "GBP",
    "JPY",
    "CHF",
    "CAD",
    "AUD",
    "NZD",
    "INR",
    "CNY",
    "HKD",
    "SGD",
    "KRW",
    "MXN",
    "BRL",
    "ZAR",
}


def validate_symbol(
    symbol: str,
    min_length: int = 1,
    max_length: int = 20,
    pattern: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """
    Validate stock ticker symbol.

    Args:
        symbol: Stock symbol to validate
        min_length: Minimum symbol length
        max_length: Maximum symbol length
        pattern: Optional regex pattern to match

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_symbol("AAPL")
        (True, None)
        >>> validate_symbol("")
        (False, 'Symbol cannot be empty')
    """
    if not symbol:
        return False, "Symbol cannot be empty"

    if len(symbol) < min_length:
        return False, f"Symbol must be at least {min_length} characters"

    if len(symbol) > max_length:
        return False, f"Symbol must be at most {max_length} characters"

    if pattern and not re.match(pattern, symbol.upper()):
        return False, "Symbol does not match required pattern"

    return True, None


def validate_date_range(
    start_date: Union[str, datetime, date],
    end_date: Union[str, datetime, date],
    max_days: Optional[int] = None,
) -> tuple[bool, Optional[str]]:
    """
    Validate date range.

    Args:
        start_date: Start date
        end_date: End date
        max_days: Optional maximum days between dates

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_date_range("2024-01-01", "2024-01-31")
        (True, None)
        >>> validate_date_range("2024-01-31", "2024-01-01")
        (False, 'End date must be after start date')
    """
    try:
        start = _to_date(start_date)
        end = _to_date(end_date)
    except Exception as e:
        return False, f"Invalid date format: {e}"

    if start > end:
        return False, "End date must be after start date"

    if max_days:
        days = (end - start).days
        if days > max_days:
            return False, f"Date range cannot exceed {max_days} days (got {days})"

    return True, None


def validate_positive_number(
    value: Union[int, float], allow_zero: bool = False
) -> tuple[bool, Optional[str]]:
    """
    Validate positive number.

    Args:
        value: Number to validate
        allow_zero: Whether to allow zero

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_positive_number(10)
        (True, None)
        >>> validate_positive_number(-5)
        (False, 'Value must be positive')
    """
    try:
        num = float(value)
    except (ValueError, TypeError):
        return False, f"Value must be a number, got {type(value).__name__}"

    if allow_zero:
        if num < 0:
            return False, "Value must be non-negative"
    else:
        if num <= 0:
            return False, "Value must be positive"

    return True, None


def validate_in_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    inclusive: bool = True,
) -> tuple[bool, Optional[str]]:
    """
    Validate number is in range.

    Args:
        value: Number to validate
        min_value: Minimum allowed value (None for no minimum)
        max_value: Maximum allowed value (None for no maximum)
        inclusive: Whether range is inclusive

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_in_range(5, 1, 10)
        (True, None)
        >>> validate_in_range(15, 1, 10)
        (False, 'Value must be <= 10')
    """
    try:
        num = float(value)
    except (ValueError, TypeError):
        return False, "Value must be a number"

    if min_value is not None:
        if inclusive and num < min_value:
            return False, f"Value must be >= {min_value}"
        elif not inclusive and num <= min_value:
            return False, f"Value must be > {min_value}"

    if max_value is not None:
        if inclusive and num > max_value:
            return False, f"Value must be <= {max_value}"
        elif not inclusive and num >= max_value:
            return False, f"Value must be < {max_value}"

    return True, None


def validate_email(email: str) -> tuple[bool, Optional[str]]:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_email("user@example.com")
        (True, None)
        >>> validate_email("invalid-email")
        (False, 'Invalid email format')
    """
    if not email:
        return False, "Email cannot be empty"

    # Basic email regex
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(pattern, email):
        return False, "Invalid email format"

    return True, None


def validate_url(url: str, require_https: bool = False) -> tuple[bool, Optional[str]]:
    """
    Validate URL format.

    Args:
        url: URL to validate
        require_https: Whether to require HTTPS protocol

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_url("https://example.com")
        (True, None)
        >>> validate_url("invalid-url")
        (False, 'Invalid URL format')
    """
    if not url:
        return False, "URL cannot be empty"

    # Basic URL regex
    if require_https:
        pattern = r"^https://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$"
        if not re.match(pattern, url):
            return False, "Invalid HTTPS URL format"
    else:
        pattern = r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$"
        if not re.match(pattern, url):
            return False, "Invalid URL format"

    return True, None


def validate_not_empty(
    value: str, field_name: str = "Value"
) -> tuple[bool, Optional[str]]:
    """
    Validate string is not empty.

    Args:
        value: String to validate
        field_name: Name of field for error message

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_not_empty("test", "Username")
        (True, None)
        >>> validate_not_empty("", "Username")
        (False, 'Username cannot be empty')
    """
    if not value or not value.strip():
        return False, f"{field_name} cannot be empty"

    return True, None


def validate_min_length(
    value: str, min_length: int, field_name: str = "Value"
) -> tuple[bool, Optional[str]]:
    """
    Validate minimum string length.

    Args:
        value: String to validate
        min_length: Minimum required length
        field_name: Name of field for error message

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(value) < min_length:
        return False, f"{field_name} must be at least {min_length} characters"

    return True, None


def validate_max_length(
    value: str, max_length: int, field_name: str = "Value"
) -> tuple[bool, Optional[str]]:
    """
    Validate maximum string length.

    Args:
        value: String to validate
        max_length: Maximum allowed length
        field_name: Name of field for error message

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(value) > max_length:
        return False, f"{field_name} must be at most {max_length} characters"

    return True, None


def validate_one_of(
    value: str,
    allowed_values: list[str],
    case_sensitive: bool = True,
    field_name: str = "Value",
) -> tuple[bool, Optional[str]]:
    """
    Validate value is in allowed list.

    Args:
        value: Value to validate
        allowed_values: List of allowed values
        case_sensitive: Whether comparison is case-sensitive
        field_name: Name of field for error message

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_one_of("USD", ["USD", "INR", "EUR"])
        (True, None)
        >>> validate_one_of("GBP", ["USD", "INR", "EUR"])
        (False, 'Value must be one of: USD, INR, EUR')
    """
    check_value = value if case_sensitive else value.upper()
    check_list = allowed_values if case_sensitive else [v.upper() for v in allowed_values]

    if check_value not in check_list:
        return False, f"{field_name} must be one of: {', '.join(allowed_values)}"

    return True, None


def validate_percentage(
    value: Union[int, float], allow_negative: bool = False
) -> tuple[bool, Optional[str]]:
    """
    Validate percentage value (0-100).

    Args:
        value: Percentage to validate
        allow_negative: Whether to allow negative percentages

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_percentage(50)
        (True, None)
        >>> validate_percentage(150)
        (False, 'Percentage must be between 0 and 100')
    """
    try:
        num = float(value)
    except (ValueError, TypeError):
        return False, "Percentage must be a number"

    if allow_negative:
        if num < -100 or num > 100:
            return False, "Percentage must be between -100 and 100"
    else:
        if num < 0 or num > 100:
            return False, "Percentage must be between 0 and 100"

    return True, None


def validate_currency_code(code: str) -> tuple[bool, Optional[str]]:
    """
    Validate ISO 4217 currency code format.

    Args:
        code: Currency code to validate

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_currency_code("USD")
        (True, None)
        >>> validate_currency_code("US")
        (False, 'Currency code must be 3 letters')
    """
    if not code:
        return False, "Currency code cannot be empty"

    if len(code) != 3:
        return False, "Currency code must be 3 letters"

    if not code.isalpha():
        return False, "Currency code must contain only letters"

    if not code.isupper():
        return False, "Currency code must be uppercase"

    if code not in KNOWN_CURRENCY_CODES:
        logger.warning(
            f"Currency code '{code}' is not in known list (but format is valid)"
        )

    return True, None


def _to_date(value: Union[str, datetime, date]) -> date:
    """Convert value to date object."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d").date()
    raise TypeError(f"Cannot convert {type(value).__name__} to date")


__all__ = [
    "validate_symbol",
    "validate_date_range",
    "validate_positive_number",
    "validate_in_range",
    "validate_email",
    "validate_url",
    "validate_not_empty",
    "validate_min_length",
    "validate_max_length",
    "validate_one_of",
    "validate_percentage",
    "validate_currency_code",
]

