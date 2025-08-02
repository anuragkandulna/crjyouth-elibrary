"""
Timezone utility functions for consistent datetime handling across the application.

All timestamps are stored as timezone-aware UTC and rounded to seconds for consistency.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime, rounded to seconds.
    
    Returns:
        datetime: Current UTC time with timezone info, rounded to seconds
    """
    return datetime.now(timezone.utc).replace(microsecond=0)


def utc_datetime(dt: Optional[datetime] = None) -> datetime:
    """
    Convert a datetime to timezone-aware UTC, rounded to seconds.
    
    Args:
        dt: Datetime to convert. If None, returns current UTC time.
        
    Returns:
        datetime: Timezone-aware UTC datetime rounded to seconds
    """
    if dt is None:
        return utc_now()
    
    # If already timezone-aware, convert to UTC
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    else:
        # Assume naive datetime is UTC
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Round to seconds for consistency
    return dt.replace(microsecond=0)


def utc_from_timestamp(timestamp: float) -> datetime:
    """
    Create timezone-aware UTC datetime from timestamp.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        datetime: Timezone-aware UTC datetime rounded to seconds
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).replace(microsecond=0)


def add_time(dt: datetime, **kwargs) -> datetime:
    """
    Add time to a datetime while maintaining timezone awareness.
    
    Args:
        dt: Base datetime
        **kwargs: Time delta arguments (days, hours, minutes, seconds, etc.)
        
    Returns:
        datetime: New datetime with added time, rounded to seconds
    """
    result = dt + timedelta(**kwargs)
    return result.replace(microsecond=0)


def utc_date_only(dt: Optional[datetime] = None) -> datetime:
    """
    Get a UTC datetime with only date components (year, month, day).
    Time is set to 00:00:00 UTC.
    
    Args:
        dt: Datetime to convert. If None, uses current UTC time.
        
    Returns:
        datetime: UTC datetime with time set to 00:00:00
    """
    if dt is None:
        dt = utc_now()
    
    # Convert to UTC if needed
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    else:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Return date only with time set to 00:00:00
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def add_days_to_date(dt: datetime, days: int) -> datetime:
    """
    Add days to a date-only datetime (preserves 00:00:00 time).
    
    Args:
        dt: Base datetime (should be date-only with 00:00:00 time)
        days: Number of days to add
        
    Returns:
        datetime: New datetime with added days, maintaining 00:00:00 time
    """
    result = dt + timedelta(days=days)
    return result.replace(hour=0, minute=0, second=0, microsecond=0)


def add_weeks_to_date(dt: datetime, weeks: int) -> datetime:
    """
    Add weeks to a date-only datetime (preserves 00:00:00 time).
    
    Args:
        dt: Base datetime (should be date-only with 00:00:00 time)
        weeks: Number of weeks to add
        
    Returns:
        datetime: New datetime with added weeks, maintaining 00:00:00 time
    """
    return add_days_to_date(dt, weeks * 7)


def is_date_past_due(due_date: datetime, current_date: Optional[datetime] = None) -> bool:
    """
    Check if a date is past due (comparing only date components).
    
    Args:
        due_date: The due date to check
        current_date: Current date to compare against. If None, uses current UTC date.
        
    Returns:
        bool: True if current date is after due date
    """
    if current_date is None:
        current_date = utc_date_only()
    else:
        current_date = utc_date_only(current_date)
    
    due_date = utc_date_only(due_date)
    return current_date > due_date


def calculate_days_overdue(due_date: datetime, current_date: Optional[datetime] = None) -> int:
    """
    Calculate number of days overdue (comparing only date components).
    
    Args:
        due_date: The due date
        current_date: Current date to compare against. If None, uses current UTC date.
        
    Returns:
        int: Number of days overdue (0 if not overdue)
    """
    if current_date is None:
        current_date = utc_date_only()
    else:
        current_date = utc_date_only(current_date)
    
    due_date = utc_date_only(due_date)
    
    if current_date > due_date:
        return (current_date - due_date).days
    return 0


def calculate_weeks_overdue(due_date: datetime, current_date: Optional[datetime] = None) -> int:
    """
    Calculate number of weeks overdue (rounded up).
    
    Args:
        due_date: The due date
        current_date: Current date to compare against. If None, uses current UTC date.
        
    Returns:
        int: Number of weeks overdue (0 if not overdue)
    """
    days_overdue = calculate_days_overdue(due_date, current_date)
    if days_overdue > 0:
        return max(1, (days_overdue + 6) // 7)  # Round up to full weeks
    return 0
