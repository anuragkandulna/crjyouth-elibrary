"""
Security-focused timezone verification utility.

Ensures timezone configuration is correct without requiring superuser privileges.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from utils.my_logger import CustomLogger
from constants.config import LOG_LEVEL
from constants.constants import APP_LOG_FILE


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=APP_LOG_FILE).get_logger()


class TimezoneSecurityError(Exception):
    """Raised when timezone configuration poses security risks."""
    pass


def verify_connection_timezone(session: Session) -> dict:
    """
    Verify database connection timezone without requiring elevated privileges.
    
    Args:
        session: Database session
        
    Returns:
        dict: Timezone verification results
        
    Raises:
        TimezoneSecurityError: If timezone configuration is unsafe
    """
    try:
        # Detect database type
        db_url = str(session.get_bind().url)
        is_sqlite = db_url.startswith('sqlite')
        
        if is_sqlite:
            # SQLite uses UTC by default and doesn't have timezone settings
            session_tz = "UTC"
            server_tz = "UTC (SQLite default)"
            
            # Test timestamp behavior
            test_time = session.execute(text("SELECT datetime('now')")).scalar()
            utc_time = session.execute(text("SELECT datetime('now', 'utc')")).scalar()
            
        else:
            # PostgreSQL timezone checks
            session_tz = session.execute(text("SELECT current_setting('timezone')")).scalar()
            
            try:
                server_tz = session.execute(text("SHOW timezone")).scalar()
            except Exception:
                server_tz = "unknown (non-privileged)"
            
            test_time = session.execute(text("SELECT now()")).scalar()
            utc_time = session.execute(text("SELECT now() AT TIME ZONE 'UTC'")).scalar()
        
        results = {
            "session_timezone": session_tz,
            "server_timezone": server_tz,
            "current_timestamp": test_time,
            "current_timestamp_utc": utc_time,
            "timezone_safe": session_tz and session_tz.upper() == 'UTC',
            "connection_override_working": session_tz and session_tz.upper() == 'UTC',
            "database_type": "SQLite" if is_sqlite else "PostgreSQL"
        }
        
        # Security validation
        if not results["timezone_safe"]:
            raise TimezoneSecurityError(
                f"Connection timezone is {session_tz}, expected UTC. "
                f"This could lead to timezone-related security vulnerabilities."
            )
        
        LOGGER.info(f"Timezone verification passed: session={session_tz} ({results['database_type']})")
        return results
        
    except Exception as ex:
        LOGGER.error(f"Timezone verification failed: {ex}")
        raise


def log_timezone_audit_info(session: Session) -> None:
    """
    Log timezone configuration for security audit purposes.
    
    Args:
        session: Database session
    """
    try:
        verification = verify_connection_timezone(session)
        
        LOGGER.info("=== TIMEZONE SECURITY AUDIT ===")
        LOGGER.info(f"Database Type: {verification['database_type']}")
        LOGGER.info(f"Session Timezone: {verification['session_timezone']}")
        LOGGER.info(f"Server Timezone: {verification['server_timezone']}")
        LOGGER.info(f"Connection Override Working: {verification['connection_override_working']}")
        LOGGER.info(f"Security Status: {'SECURE' if verification['timezone_safe'] else 'VULNERABLE'}")
        LOGGER.info("===============================")
        
    except Exception as ex:
        LOGGER.error(f"Timezone audit logging failed: {ex}")


def startup_timezone_check(session: Session) -> None:
    """
    Perform timezone security check during application startup.
    
    Args:
        session: Database session
        
    Raises:
        TimezoneSecurityError: If timezone configuration is unsafe
    """
    try:
        verification = verify_connection_timezone(session)
        log_timezone_audit_info(session)
        
        if not verification["timezone_safe"]:
            raise TimezoneSecurityError(
                "Application startup failed: Unsafe timezone configuration detected. "
                "Check database connection settings."
            )
            
        LOGGER.info("Timezone security check passed - Application startup safe")
        
    except Exception as ex:
        LOGGER.critical(f"Timezone security check FAILED during startup: {ex}")
        raise 