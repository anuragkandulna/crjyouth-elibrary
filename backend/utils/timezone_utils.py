"""
Simple timestamp utility functions for SQLite compatibility.
All timestamps are stored as naive datetime objects rounded to seconds.
"""

from datetime import datetime, timedelta
from typing import Optional


def utc_now() -> datetime:
    """
    Get current time as naive datetime, rounded to seconds.
    
    Returns:
        datetime: Current time rounded to seconds (no timezone info)
    """
    return datetime.now().replace(microsecond=0)


def utc_datetime(dt: Optional[datetime] = None) -> datetime:
    """
    Convert a datetime to naive datetime, rounded to seconds.
    
    Args:
        dt: Datetime to convert. If None, returns current time.
        
    Returns:
        datetime: Naive datetime rounded to seconds
    """
    if dt is None:
        return utc_now()
    
    # Handle string input
    if isinstance(dt, str):
        try:
            # Try to parse ISO format string
            if dt.endswith('Z'):
                dt = dt[:-1]  # Remove Z suffix
            dt = datetime.fromisoformat(dt)
        except Exception:
            try:
                # Try alternative parsing
                dt = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S')
            except Exception:
                try:
                    # Try parsing just date
                    dt = datetime.strptime(dt, '%Y-%m-%d')
                except Exception:
                    # Fallback to current time
                    return utc_now()
    
    # Remove timezone info if present and round to seconds
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    
    return dt.replace(microsecond=0)


def utc_from_timestamp(timestamp: float) -> datetime:
    """
    Create naive datetime from timestamp.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        datetime: Naive datetime rounded to seconds
    """
    return datetime.fromtimestamp(timestamp).replace(microsecond=0)


def add_time(dt: datetime, **kwargs) -> datetime:
    """
    Add time to a datetime.
    
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
    Get a datetime with only date components (year, month, day).
    Time is set to 00:00:00.
    
    Args:
        dt: Datetime to convert. If None, uses current time.
        
    Returns:
        datetime: Datetime with time set to 00:00:00
    """
    if dt is None:
        dt = utc_now()
    
    # Remove timezone info if present
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    
    # Return date only with time set to 00:00:00
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def add_days_to_date(dt: datetime, days: int) -> datetime:
    """
    Add days to a date-only datetime (preserves 00:00:00 time).
    
    Args:
        dt: Base datetime
        days: Number of days to add
        
    Returns:
        datetime: New datetime with added days
    """
    result = dt + timedelta(days=days)
    return result.replace(microsecond=0)


def format_datetime_for_display(dt: datetime) -> str:
    """
    Format datetime for display (DD-MMM-YEAR format as per user preference).
    
    Args:
        dt: Datetime to format
        
    Returns:
        str: Formatted datetime string
    """
    return dt.strftime('%d-%b-%Y')


def format_datetime_for_db(dt: datetime) -> str:
    """
    Format datetime for database storage (ISO format).
    
    Args:
        dt: Datetime to format
        
    Returns:
        str: ISO formatted datetime string
    """
    return dt.isoformat()


def parse_datetime_from_db(dt_str: str) -> datetime:
    """
    Parse datetime from database string.
    
    Args:
        dt_str: Datetime string from database
        
    Returns:
        datetime: Parsed datetime object
    """
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        try:
            return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            return utc_now()


def add_weeks_to_date(dt: datetime, weeks: int) -> datetime:
    """
    Add weeks to a datetime.
    
    Args:
        dt: Base datetime
        weeks: Number of weeks to add
        
    Returns:
        datetime: New datetime with added weeks
    """
    return add_time(dt, weeks=weeks)


def is_date_past_due(due_date: datetime, current_date: Optional[datetime] = None) -> bool:
    """
    Check if a date is past due (comparing only date components).
    
    Args:
        due_date: The due date to check
        current_date: Current date to compare against. If None, uses current date.
        
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
        current_date: Current date to compare against. If None, uses current date.
        
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
        current_date: Current date to compare against. If None, uses current date.
        
    Returns:
        int: Number of weeks overdue (0 if not overdue)
    """
    days_overdue = calculate_days_overdue(due_date, current_date)
    if days_overdue > 0:
        return max(1, (days_overdue + 6) // 7)  # Round up to full weeks
    return 0
