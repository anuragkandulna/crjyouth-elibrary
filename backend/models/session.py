from sqlalchemy import String, Boolean, DateTime, ForeignKey, select, update, delete, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from datetime import datetime, timedelta, timezone
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
    device_id: Mapped[str] = mapped_column(String(100), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    last_refreshed: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
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
            
            if len(device_id) > 100:
                raise ValueError("device_id too long (max 100 characters)")

            now = utc_now()
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
    def is_session_valid(session: Session, session_id: str) -> bool:
        """
        Check if a session is valid (active and not expired).
        """
        try:
            now = utc_now()
            stmt = select(Session).where(
                Session.session_id == session_id,
                Session.is_active.is_(True),
                Session.expires_at > now
            )
            return session.scalar(stmt) is not None
        except Exception as ex:
            LOGGER.error(f"Failed to validate session '{session_id}': {ex}")
            return False


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
                
                # Check if session hasn't expired
                if db_session.expires_at <= now:
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


    @staticmethod
    def get_sessions_by_device(session: Session, user_uuid: str, device_id: str) -> List["Session"]:
        """
        Get all sessions for a specific user and device.
        """
        try:
            stmt = select(Session).where(
                Session.user_uuid == user_uuid,
                Session.device_id == device_id
            ).order_by(Session.created_at.desc())
            return list(session.scalars(stmt).all())
        except Exception as ex:
            LOGGER.error(f"Failed to retrieve sessions for user '{user_uuid}' on device '{device_id}': {ex}")
            return []


    @staticmethod
    def cleanup_expired_sessions(session: Session, days_threshold: int = 1) -> int:
        """
        Delete sessions that have expired more than specified days ago.
        """
        try:
            threshold = add_time(utc_now(), days=-days_threshold)
            stmt = delete(Session).where(Session.expires_at < threshold)
            result = session.execute(stmt)
            session.commit()
            LOGGER.info(f"Cleaned up {result.rowcount} expired sessions from database (older than {days_threshold} days).")
            return result.rowcount
            
        except Exception as ex:
            session.rollback()
            LOGGER.error(f"Failed to cleanup expired sessions: {ex}")
            return 0


    @staticmethod
    def count_active_sessions(session: Session, user_uuid: str) -> int:
        """
        Count active sessions for a user.
        """
        try:
            now = utc_now()
            stmt = select(func.count(Session.session_id)).where(
                Session.user_uuid == user_uuid,
                Session.is_active.is_(True),
                Session.expires_at > now
            )
            return session.scalar(stmt) or 0
        except Exception as ex:
            LOGGER.error(f"Failed to count active sessions for user '{user_uuid}': {ex}")
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
