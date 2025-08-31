"""
Session Management Utilities
Handles session limits, eviction strategies, and logging
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc

from models.session import Session
from models.user import User
from constants.config import SESSION_CONFIG
from utils.timezone_utils import utc_now, utc_datetime

LOGGER = logging.getLogger(__name__)


class SessionManager:
    """Manages session creation, limits, and eviction strategies"""
    
    @staticmethod
    def get_active_sessions(db_session: DBSession, user_uuid: str) -> List[Session]:
        """Get all active sessions for a user"""
        now = utc_now()
        return db_session.query(Session).filter(
            Session.user_uuid == user_uuid,
            Session.expires_at > now,
            Session.is_active == True
        ).order_by(desc(Session.last_refreshed)).all()
    
    @staticmethod
    def get_device_sessions(db_session: DBSession, user_uuid: str, device_id: str) -> List[Session]:
        """Get active sessions for a specific device"""
        now = utc_now()
        return db_session.query(Session).filter(
            Session.user_uuid == user_uuid,
            Session.device_id == device_id,
            Session.expires_at > now,
            Session.is_active == True
        ).order_by(desc(Session.last_refreshed)).all()
    
    @staticmethod
    def find_lru_session(sessions: List[Session]) -> Optional[Session]:
        """Find the least recently used session"""
        if not sessions:
            return None
        return min(sessions, key=lambda s: s.last_refreshed)
    
    @staticmethod
    def log_session_event(event_type: str, session_data: Dict, metadata: Optional[Dict] = None):
        """Log session events for monitoring and debugging"""
        # Handle timezone-naive datetime objects
        try:
            timestamp = utc_now().isoformat()
        except Exception:
            timestamp = str(utc_now())
            
        log_data = {
            "timestamp": timestamp,
            "event_type": event_type,
            "user_uuid": session_data.get("user_uuid"),
            "session_id": session_data.get("session_id"),
            "device_id": session_data.get("device_id"),
            "user_agent": session_data.get("user_agent"),
            "metadata": metadata or {}
        }
        
        LOGGER.info(f"Session event: {log_data}")
    
    @staticmethod
    def log_session_eviction(strategy: str, session: Session, reason: str = ""):
        """Log session eviction events"""
        # Handle timezone-naive datetime objects
        try:
            last_refreshed_str = session.last_refreshed.isoformat()
            expires_at_str = session.expires_at.isoformat()
        except Exception:
            last_refreshed_str = str(session.last_refreshed)
            expires_at_str = str(session.expires_at)
            
        SessionManager.log_session_event("eviction", {
            "user_uuid": session.user_uuid,
            "session_id": session.session_id,
            "device_id": session.device_id,
            "user_agent": session.user_agent
        }, {
            "strategy": strategy,
            "reason": reason,
            "last_refreshed": last_refreshed_str,
            "expires_at": expires_at_str
        })
    
    @staticmethod
    def manage_session_limits(db_session: DBSession, user_uuid: str, device_id: str, user_agent: str) -> bool:
        """
        Manage session limits and apply eviction strategy if needed
        Returns True if eviction was performed, False otherwise
        """
        active_sessions = SessionManager.get_active_sessions(db_session, user_uuid)
        max_sessions = SESSION_CONFIG["max_sessions_per_user"]
        
        if len(active_sessions) < max_sessions:
            return False
        
        LOGGER.info(f"Session limit reached for user {user_uuid}. Active sessions: {len(active_sessions)}")
        
        # Step 1: Per-device LRU (same device, different browsers)
        device_sessions = SessionManager.get_device_sessions(db_session, user_uuid, device_id)
        if len(device_sessions) > 1:
            oldest_device_session = SessionManager.find_lru_session(device_sessions)
            if oldest_device_session:
                Session.invalidate_session(db_session, oldest_device_session.session_id)
                SessionManager.log_session_eviction("per_device_lru", oldest_device_session, 
                                                  f"Device {device_id} has {len(device_sessions)} sessions")
                return True
        
        # Step 2: Global LRU (across all devices)
        oldest_global_session = SessionManager.find_lru_session(active_sessions)
        if oldest_global_session:
            Session.invalidate_session(db_session, oldest_global_session.session_id)
            SessionManager.log_session_eviction("global_lru", oldest_global_session, 
                                              f"Global limit reached: {len(active_sessions)} sessions")
            return True
        
        return False
    
    @staticmethod
    def cleanup_expired_sessions(db_session: DBSession) -> Dict:
        """Clean up expired sessions and return metrics"""
        now = utc_now()
        expired_sessions = db_session.query(Session).filter(
            Session.expires_at <= now,
            Session.is_active == True
        ).all()
        
        sessions_cleaned = 0
        users_affected = set()
        
        for session in expired_sessions:
            session.is_active = False
            users_affected.add(session.user_uuid)
            sessions_cleaned += 1
            
            # Handle timezone-naive datetime objects
            try:
                expired_at_str = session.expires_at.isoformat()
            except Exception:
                expired_at_str = str(session.expires_at)
                
            SessionManager.log_session_event("cleanup", {
                "user_uuid": session.user_uuid,
                "session_id": session.session_id,
                "device_id": session.device_id,
                "user_agent": session.user_agent
            }, {
                "reason": "expired",
                "expired_at": expired_at_str
            })
        
        db_session.commit()
        
        # Handle timezone-naive datetime objects
        try:
            cleanup_timestamp = now.isoformat()
        except Exception:
            cleanup_timestamp = str(now)
            
        metrics = {
            "sessions_cleaned": sessions_cleaned,
            "users_affected": len(users_affected),
            "cleanup_timestamp": cleanup_timestamp,
            "expired_sessions": [s.session_id for s in expired_sessions]
        }
        
        LOGGER.info(f"Session cleanup completed: {metrics}")
        return metrics
    
    @staticmethod
    def get_session_metrics(db_session: DBSession) -> Dict:
        """Get current session metrics for monitoring"""
        now = utc_now()
        
        total_active_sessions = db_session.query(Session).filter(
            Session.expires_at > now,
            Session.is_active == True
        ).count()
        
        total_expired_sessions = db_session.query(Session).filter(
            Session.expires_at <= now,
            Session.is_active == True
        ).count()
        
        # Get unique users with active sessions
        active_users = db_session.query(Session.user_uuid).filter(
            Session.expires_at > now,
            Session.is_active == True
        ).distinct().count()
        
        # Handle timezone-naive datetime objects
        try:
            timestamp = now.isoformat()
        except Exception:
            timestamp = str(now)
            
        return {
            "total_active_sessions": total_active_sessions,
            "total_expired_sessions": total_expired_sessions,
            "active_users": active_users,
            "timestamp": timestamp
        } 