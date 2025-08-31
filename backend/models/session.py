from sqlalchemy import String, Boolean, DateTime, ForeignKey, select, update, delete, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Optional, List
from models.base import Base
from utils.my_logger import CustomLogger
from utils.timezone_utils import utc_now, utc_datetime, add_time
from constants.constants import APP_LOG_FILE
from constants.config import LOG_LEVEL


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=APP_LOG_FILE).get_logger()


class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_uuid: Mapped[str] = mapped_column(ForeignKey("users.user_uuid"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_refreshed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("User")


    @staticmethod
    def create_session(session: Session, user_uuid: str, device_id: str,
                       user_agent: Optional[str] = None, ip_address: Optional[str] = None,
                       ttl_minutes: int = 720) -> "Session":
        """
        Creates a new session for the given user.
        """
        try:
            # Validate input parameters
            if not user_uuid or not device_id:
                raise ValueError("user_uuid and device_id are required")
            
            if len(device_id) > 255:
                raise ValueError("device_id too long (max 255 characters)")

            now = utc_datetime()
            new_session = Session(
                user_uuid=user_uuid,
                device_id=device_id,
                user_agent=user_agent,
                ip_address=ip_address,
                created_at=now,
                expires_at=add_time(now, minutes=ttl_minutes),
                last_refreshed=now
            )
            session.add(new_session)
            session.commit()
            LOGGER.info(f"New session created for user '{user_uuid}' on device '{device_id}' with {ttl_minutes} minutes TTL.")
            return new_session
            
        except Exception as ex:
            session.rollback()
            LOGGER.error(f"Failed to create session for user '{user_uuid}': {ex}")
            raise


    @staticmethod
    def get_active_sessions(session: Session, user_uuid: str) -> List["Session"]:
        """
        Get all active sessions of the user.
        """
        try:
            now = utc_now()
            stmt = select(Session).where(
                Session.user_uuid == user_uuid,
                Session.is_active.is_(True),
                Session.expires_at > now
            )
            active_sessions = list(session.scalars(stmt).all())
            LOGGER.debug(f"Retrieved {len(active_sessions)} active sessions for user '{user_uuid}'.")
            return active_sessions
            
        except Exception as ex:
            LOGGER.error(f"Failed to retrieve active sessions for user '{user_uuid}': {ex}")
            return []


    @staticmethod
    def get_session_by_id(session: Session, session_id: str) -> Optional["Session"]:
        """
        Get a session by its ID.
        """
        try:
            stmt = select(Session).where(Session.session_id == session_id)
            return session.scalar(stmt)
        except Exception as ex:
            LOGGER.error(f"Failed to retrieve session '{session_id}': {ex}")
            return None


    @staticmethod
    def refresh_session(session: Session, session_id: str, ttl_minutes: int = 720) -> bool:
        """
        Update the last_refreshed timestamp and extend expiry.
        """
        try:
            stmt = select(Session).where(
                Session.session_id == session_id,
                Session.is_active.is_(True)
            )
            db_session = session.scalar(stmt)

            if db_session:
                now = utc_now()
                
                # Simple datetime comparison
                expires_at = db_session.expires_at
                
                # Check if session hasn't expired
                if expires_at <= now:
                    LOGGER.warning(f"Attempted to refresh expired session '{session_id}'.")
                    return False
                
                db_session.last_refreshed = now
                db_session.expires_at = add_time(now, minutes=ttl_minutes)
                session.commit()
                LOGGER.info(f"Session '{session_id}' refreshed for user '{db_session.user_uuid}' with {ttl_minutes} minutes TTL.")
                return True
            else:
                LOGGER.warning(f"Attempted to refresh non-existent or inactive session '{session_id}'.")
                return False
                
        except Exception as ex:
            session.rollback()
            LOGGER.error(f"Failed to refresh session '{session_id}': {ex}")
            return False


    @staticmethod
    def invalidate_session(session: Session, session_id: str) -> bool:
        """
        Mark a single session inactive (e.g., device logout).
        """
        try:
            stmt = select(Session).where(
                Session.session_id == session_id,
                Session.is_active.is_(True)
            )
            db_session = session.scalar(stmt)

            if not db_session:
                LOGGER.warning(f"Attempted to invalidate non-existent or already inactive session '{session_id}'.")
                return False

            db_session.is_active = False
            session.commit()
            LOGGER.info(f"Session '{session_id}' invalidated for user '{db_session.user_uuid}'.")
            return True
            
        except Exception as ex:
            session.rollback()
            LOGGER.error(f"Failed to invalidate session '{session_id}': {ex}")
            return False


    @staticmethod
    def deactivate_all_sessions(session: Session, user_uuid: str) -> int:
        """
        Mark all active sessions of a user as inactive.
        """
        try:
            stmt = (
                update(Session)
                .where(Session.user_uuid == user_uuid, Session.is_active.is_(True))
                .values(is_active=False)
            )
            result = session.execute(stmt)
            session.commit()
            LOGGER.info(f"Deactivated {result.rowcount} sessions for user '{user_uuid}'.")
            return result.rowcount
            
        except Exception as ex:
            session.rollback()
            LOGGER.error(f"Failed to deactivate sessions for user '{user_uuid}': {ex}")
            return 0


    def is_expired(self) -> bool:
        """
        Check if this session has expired.
        """
        return self.expires_at <= utc_now()


    def time_until_expiry(self) -> Optional[timedelta]:
        """
        Get time remaining until session expires.
        """
        if self.is_expired():
            return None
        return self.expires_at - utc_now()


    def __repr__(self):
        return f"<Session(session_id='{self.session_id}', user_uuid='{self.user_uuid}', device='{self.device_id}', active={self.is_active})>"


    @staticmethod
    def create_session_with_limits(session: Session, user_uuid: str, device_id: str, user_agent: str, ttl_minutes: int = 240) -> Optional["Session"]:
        """
        Create a new session with limit management
        Returns the created session or None if creation failed
        """
        try:
            from utils.session_manager import SessionManager
            
            # Check and manage session limits before creating new session
            SessionManager.manage_session_limits(session, user_uuid, device_id, user_agent)
            
            # Create the new session
            new_session = Session.create_session(session, user_uuid, device_id, user_agent, ttl_minutes)
            
            if new_session:
                # Handle timezone-naive datetime objects
                try:
                    expires_at_str = new_session.expires_at.isoformat()
                except Exception:
                    expires_at_str = str(new_session.expires_at)
                    
                SessionManager.log_session_event("create", {
                    "user_uuid": user_uuid,
                    "session_id": new_session.session_id,
                    "device_id": device_id,
                    "user_agent": user_agent
                }, {
                    "ttl_minutes": ttl_minutes,
                    "expires_at": expires_at_str
                })
            
            return new_session
            
        except Exception as ex:
            LOGGER.error(f"Failed to create session with limits for user {user_uuid}: {ex}")
            return None


    @staticmethod
    def get_session_by_device_and_agent(session: Session, user_uuid: str, device_id: str, user_agent: str) -> Optional["Session"]:
        """Get active session by device_id and user_agent"""
        try:
            now = utc_now()
            stmt = select(Session).where(
                Session.user_uuid == user_uuid,
                Session.device_id == device_id,
                Session.user_agent == user_agent,
                Session.expires_at > now,
                Session.is_active.is_(True)
            )
            return session.scalar(stmt)
        except Exception as ex:
            LOGGER.error(f"Failed to retrieve session by device and agent for user '{user_uuid}': {ex}")
            return None


    @staticmethod
    def invalidate_all_user_sessions(session: Session, user_uuid: str) -> int:
        """Invalidate all active sessions for a user"""
        try:
            now = utc_now()
            stmt = select(Session).where(
                Session.user_uuid == user_uuid,
                Session.expires_at > now,
                Session.is_active.is_(True)
            )
            active_sessions = list(session.scalars(stmt).all())
            
            count = 0
            for sess in active_sessions:
                sess.is_active = False
                count += 1
                LOGGER.info(f"Invalidated session {sess.session_id} for user {user_uuid}")
            
            session.commit()
            return count
            
        except Exception as ex:
            session.rollback()
            LOGGER.error(f"Failed to invalidate all sessions for user '{user_uuid}': {ex}")
            return 0
