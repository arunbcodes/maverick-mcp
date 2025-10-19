"""
Date/Time Utility Functions

Common date and time operations used across the codebase.
"""

import logging
from datetime import datetime, date, timedelta, time, timezone
from typing import Union, Optional

import pandas as pd
import pytz

logger = logging.getLogger(__name__)

# Type alias for date-like objects
DateLike = Union[datetime, date, pd.Timestamp, str]


def now_utc() -> datetime:
    """
    Get current UTC datetime.
    
    Returns:
        Current datetime in UTC with timezone info
        
    Example:
        >>> now = now_utc()
        >>> now.tzinfo
        datetime.timezone.utc
    """
    return datetime.now(timezone.utc)


def today_utc() -> date:
    """
    Get today's date in UTC.
    
    Returns:
        Current date in UTC
    """
    return now_utc().date()


def to_datetime(dt: DateLike, tz: Optional[str] = None) -> datetime:
    """
    Convert various date-like objects to datetime.
    
    Args:
        dt: Date-like object (datetime, date, pd.Timestamp, or ISO string)
        tz: Optional timezone name (e.g., 'US/Eastern', 'Asia/Kolkata')
            If None, returns timezone-naive datetime
            
    Returns:
        datetime object
        
    Example:
        >>> to_datetime("2024-01-15")
        datetime.datetime(2024, 1, 15, 0, 0)
        >>> to_datetime("2024-01-15", tz="US/Eastern")
        datetime.datetime(2024, 1, 15, 0, 0, tzinfo=<DstTzInfo 'US/Eastern' ...>)
    """
    # Convert to pandas Timestamp first (handles most formats)
    if isinstance(dt, str):
        ts = pd.to_datetime(dt)
    elif isinstance(dt, pd.Timestamp):
        ts = dt
    elif isinstance(dt, datetime):
        ts = pd.Timestamp(dt)
    elif isinstance(dt, date):
        ts = pd.Timestamp(dt)
    else:
        raise TypeError(f"Cannot convert {type(dt)} to datetime")
    
    # Convert to datetime
    result = ts.to_pydatetime()
    
    # Handle timezone
    if tz:
        timezone_obj = pytz.timezone(tz)
        if result.tzinfo is None:
            result = timezone_obj.localize(result)
        else:
            result = result.astimezone(timezone_obj)
    else:
        # Remove timezone info if present
        if result.tzinfo is not None:
            result = result.replace(tzinfo=None)
    
    return result


def to_date(dt: DateLike) -> date:
    """
    Convert date-like object to date.
    
    Args:
        dt: Date-like object
        
    Returns:
        date object
        
    Example:
        >>> to_date("2024-01-15")
        datetime.date(2024, 1, 15)
        >>> to_date(datetime(2024, 1, 15, 14, 30))
        datetime.date(2024, 1, 15)
    """
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return dt
    
    dt_obj = to_datetime(dt)
    return dt_obj.date()


def format_date(dt: DateLike, format_str: str = "%Y-%m-%d") -> str:
    """
    Format date-like object as string.
    
    Args:
        dt: Date-like object
        format_str: Format string (default: ISO format YYYY-MM-DD)
        
    Returns:
        Formatted date string
        
    Example:
        >>> format_date("2024-01-15", "%B %d, %Y")
        'January 15, 2024'
    """
    dt_obj = to_datetime(dt)
    return dt_obj.strftime(format_str)


def parse_date(date_str: str, format_str: Optional[str] = None) -> datetime:
    """
    Parse date string to datetime.
    
    Args:
        date_str: Date string
        format_str: Expected format (if None, tries to auto-detect)
        
    Returns:
        datetime object
        
    Example:
        >>> parse_date("2024-01-15")
        datetime.datetime(2024, 1, 15, 0, 0)
        >>> parse_date("01/15/2024", "%m/%d/%Y")
        datetime.datetime(2024, 1, 15, 0, 0)
    """
    if format_str:
        return datetime.strptime(date_str, format_str)
    else:
        return to_datetime(date_str)


def add_days(dt: DateLike, days: int) -> datetime:
    """
    Add days to a date.
    
    Args:
        dt: Date-like object
        days: Number of days to add (negative to subtract)
        
    Returns:
        datetime object
        
    Example:
        >>> add_days("2024-01-15", 7)
        datetime.datetime(2024, 1, 22, 0, 0)
    """
    dt_obj = to_datetime(dt)
    return dt_obj + timedelta(days=days)


def add_months(dt: DateLike, months: int) -> datetime:
    """
    Add months to a date.
    
    Args:
        dt: Date-like object
        months: Number of months to add (negative to subtract)
        
    Returns:
        datetime object
        
    Example:
        >>> add_months("2024-01-15", 3)
        datetime.datetime(2024, 4, 15, 0, 0)
    """
    dt_obj = to_datetime(dt)
    
    # Calculate new month and year
    new_month = dt_obj.month + months
    new_year = dt_obj.year
    
    while new_month > 12:
        new_month -= 12
        new_year += 1
    
    while new_month < 1:
        new_month += 12
        new_year -= 1
    
    # Handle day overflow (e.g., Jan 31 + 1 month = Feb 28/29)
    max_day = 31
    if new_month in [4, 6, 9, 11]:
        max_day = 30
    elif new_month == 2:
        if (new_year % 4 == 0 and new_year % 100 != 0) or (new_year % 400 == 0):
            max_day = 29
        else:
            max_day = 28
    
    new_day = min(dt_obj.day, max_day)
    
    return dt_obj.replace(year=new_year, month=new_month, day=new_day)


def days_between(start: DateLike, end: DateLike) -> int:
    """
    Calculate days between two dates.
    
    Args:
        start: Start date
        end: End date
        
    Returns:
        Number of days between dates (positive if end > start)
        
    Example:
        >>> days_between("2024-01-01", "2024-01-15")
        14
    """
    start_dt = to_date(start)
    end_dt = to_date(end)
    return (end_dt - start_dt).days


def is_weekend(dt: DateLike) -> bool:
    """
    Check if date is a weekend (Saturday or Sunday).
    
    Args:
        dt: Date-like object
        
    Returns:
        True if weekend
        
    Example:
        >>> is_weekend("2024-01-13")  # Saturday
        True
        >>> is_weekend("2024-01-15")  # Monday
        False
    """
    dt_obj = to_datetime(dt)
    return dt_obj.weekday() >= 5


def is_weekday(dt: DateLike) -> bool:
    """
    Check if date is a weekday (Monday-Friday).
    
    Args:
        dt: Date-like object
        
    Returns:
        True if weekday
    """
    return not is_weekend(dt)


def start_of_day(dt: DateLike, tz: Optional[str] = None) -> datetime:
    """
    Get start of day (00:00:00).
    
    Args:
        dt: Date-like object
        tz: Optional timezone
        
    Returns:
        datetime at start of day
        
    Example:
        >>> start_of_day("2024-01-15")
        datetime.datetime(2024, 1, 15, 0, 0, 0)
    """
    dt_obj = to_datetime(dt, tz=tz)
    return dt_obj.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: DateLike, tz: Optional[str] = None) -> datetime:
    """
    Get end of day (23:59:59.999999).
    
    Args:
        dt: Date-like object
        tz: Optional timezone
        
    Returns:
        datetime at end of day
        
    Example:
        >>> end_of_day("2024-01-15")
        datetime.datetime(2024, 1, 15, 23, 59, 59, 999999)
    """
    dt_obj = to_datetime(dt, tz=tz)
    return dt_obj.replace(hour=23, minute=59, second=59, microsecond=999999)


def start_of_month(dt: DateLike) -> datetime:
    """
    Get start of month (first day at 00:00:00).
    
    Args:
        dt: Date-like object
        
    Returns:
        datetime at start of month
        
    Example:
        >>> start_of_month("2024-01-15")
        datetime.datetime(2024, 1, 1, 0, 0, 0)
    """
    dt_obj = to_datetime(dt)
    return dt_obj.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def end_of_month(dt: DateLike) -> datetime:
    """
    Get end of month (last day at 23:59:59).
    
    Args:
        dt: Date-like object
        
    Returns:
        datetime at end of month
    """
    dt_obj = to_datetime(dt)
    
    # Move to next month, then back one day
    next_month = add_months(dt_obj, 1)
    first_of_next = start_of_month(next_month)
    last_of_current = add_days(first_of_next, -1)
    
    return last_of_current.replace(hour=23, minute=59, second=59, microsecond=999999)


def time_ago(dt: DateLike) -> str:
    """
    Get human-readable time ago string.
    
    Args:
        dt: Date-like object
        
    Returns:
        Human-readable string (e.g., "2 hours ago", "3 days ago")
        
    Example:
        >>> time_ago(now_utc() - timedelta(hours=2))
        '2 hours ago'
    """
    dt_obj = to_datetime(dt)
    now = now_utc().replace(tzinfo=None)
    
    diff = now - dt_obj
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"


__all__ = [
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
]

