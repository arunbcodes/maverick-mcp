"""
Maverick Core Utilities.

Common utility functions for date/time operations, data processing,
type conversions, and other shared functionality.
"""

from maverick_core.utils.conversion import (
    decimal_from_dict,
    float_from_dict,
    get_with_default,
    int_from_dict,
    round_price,
    to_decimal,
    to_decimal_or_none,
    to_float,
    to_float_or_none,
    to_int,
)
from maverick_core.utils.datetime_utils import (
    DateLike,
    add_days,
    add_months,
    days_between,
    end_of_day,
    end_of_month,
    format_date,
    is_weekday,
    is_weekend,
    now_utc,
    parse_date,
    start_of_day,
    start_of_month,
    time_ago,
    to_date,
    to_datetime,
    today_utc,
)

__all__ = [
    # Date/Time utilities
    "DateLike",
    "now_utc",
    "today_utc",
    "to_datetime",
    "to_date",
    "format_date",
    "parse_date",
    "add_days",
    "add_months",
    "days_between",
    "is_weekend",
    "is_weekday",
    "start_of_day",
    "end_of_day",
    "start_of_month",
    "end_of_month",
    "time_ago",
    # Type conversion utilities
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

