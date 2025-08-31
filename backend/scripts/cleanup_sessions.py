#!/usr/bin/env python3
"""
Session Cleanup Script
Runs as a standalone script to clean up expired sessions
Can be scheduled as a cron job to run every hour
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import json

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.sqlite_database import get_db_session
from utils.session_manager import SessionManager
from utils.timezone_utils import utc_now
from constants.config import SESSION_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), '..', 'logs', 'cleanup_metrics.log')),
        logging.StreamHandler(sys.stdout)
    ]
)

LOGGER = logging.getLogger(__name__)


def cleanup_expired_sessions():
    """Main cleanup function"""
    start_time = utc_now()
    LOGGER.info("Starting session cleanup job")
    
    try:
        with get_db_session() as session:
            # Clean up expired sessions
            metrics = SessionManager.cleanup_expired_sessions(session)
            
            # Get current session metrics
            current_metrics = SessionManager.get_session_metrics(session)
            
            # Handle timezone-naive datetime objects
            try:
                start_time_str = start_time.isoformat()
                end_time_str = utc_now().isoformat()
            except Exception:
                start_time_str = str(start_time)
                end_time_str = str(utc_now())
            
            # Combine metrics
            cleanup_report = {
                **metrics,
                **current_metrics,
                "cleanup_duration_seconds": (utc_now() - start_time).total_seconds(),
                "cleanup_start_time": start_time_str,
                "cleanup_end_time": end_time_str
            }
            
            # Log the report
            LOGGER.info(f"Cleanup completed: {json.dumps(cleanup_report, indent=2)}")
            
            # Save metrics to file for daily summary
            save_metrics_to_file(cleanup_report)
            
            return cleanup_report
            
    except Exception as ex:
        LOGGER.error(f"Session cleanup failed: {ex}")
        # Handle timezone-naive datetime objects in error case
        try:
            start_time_str = start_time.isoformat()
            end_time_str = utc_now().isoformat()
        except Exception:
            start_time_str = str(start_time)
            end_time_str = str(utc_now())
            
        return {
            "error": str(ex),
            "cleanup_start_time": start_time_str,
            "cleanup_end_time": end_time_str
        }


def save_metrics_to_file(metrics):
    """Save metrics to a file for daily summary processing"""
    try:
        metrics_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(metrics_dir, exist_ok=True)
        
        metrics_file = os.path.join(metrics_dir, 'daily_cleanup_metrics.json')
        
        # Load existing metrics if file exists
        existing_metrics = []
        if os.path.exists(metrics_file):
            try:
                with open(metrics_file, 'r') as f:
                    existing_metrics = json.load(f)
            except json.JSONDecodeError:
                existing_metrics = []
        
        # Add new metrics
        existing_metrics.append(metrics)
        
        # Keep only last 24 entries (24 hours)
        if len(existing_metrics) > 24:
            existing_metrics = existing_metrics[-24:]
        
        # Save back to file
        with open(metrics_file, 'w') as f:
            json.dump(existing_metrics, f, indent=2)
            
    except Exception as ex:
        LOGGER.error(f"Failed to save metrics to file: {ex}")


def generate_daily_summary():
    """Generate a daily summary from collected metrics"""
    try:
        metrics_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'daily_cleanup_metrics.json')
        
        if not os.path.exists(metrics_file):
            LOGGER.warning("No metrics file found for daily summary")
            return
        
        with open(metrics_file, 'r') as f:
            daily_metrics = json.load(f)
        
        if not daily_metrics:
            LOGGER.warning("No metrics data found for daily summary")
            return
        
        # Calculate daily totals
        total_sessions_cleaned = sum(m.get('sessions_cleaned', 0) for m in daily_metrics)
        # Fix the set union issue - collect all session IDs first
        all_session_ids = []
        for m in daily_metrics:
            session_ids = m.get('expired_sessions', [])
            if isinstance(session_ids, list):
                all_session_ids.extend(session_ids)
        total_users_affected = len(set(all_session_ids))
        total_cleanup_runs = len(daily_metrics)
        avg_cleanup_duration = sum(m.get('cleanup_duration_seconds', 0) for m in daily_metrics) / total_cleanup_runs
        
        # Get current active sessions
        with get_db_session() as session:
            current_metrics = SessionManager.get_session_metrics(session)
        
        daily_summary = {
            "date": utc_now().date().isoformat(),
            "total_sessions_cleaned": total_sessions_cleaned,
            "total_users_affected": total_users_affected,
            "total_cleanup_runs": total_cleanup_runs,
            "average_cleanup_duration_seconds": round(avg_cleanup_duration, 2),
            "current_active_sessions": current_metrics.get('total_active_sessions', 0),
            "current_active_users": current_metrics.get('active_users', 0),
            "cleanup_efficiency": {
                "sessions_per_run": round(total_sessions_cleaned / total_cleanup_runs, 2) if total_cleanup_runs > 0 else 0,
                "users_per_run": round(total_users_affected / total_cleanup_runs, 2) if total_cleanup_runs > 0 else 0
            }
        }
        
        # Save daily summary
        summary_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'daily_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(daily_summary, f, indent=2)
        
        LOGGER.info(f"Daily summary generated: {json.dumps(daily_summary, indent=2)}")
        
        # Clear the metrics file for the next day
        with open(metrics_file, 'w') as f:
            json.dump([], f)
            
    except Exception as ex:
        LOGGER.error(f"Failed to generate daily summary: {ex}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Session cleanup script")
    parser.add_argument("--summary", action="store_true", help="Generate daily summary instead of cleanup")
    
    args = parser.parse_args()
    
    if args.summary:
        generate_daily_summary()
    else:
        cleanup_expired_sessions() 