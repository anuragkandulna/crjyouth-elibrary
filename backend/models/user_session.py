from sqlalchemy import String, Boolean, DateTime, ForeignKey, select, update, delete
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from models.base import Base
from models.library_user import LibraryUser


class UserSession(Base):
    __tablename__ = "user_sessions"

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_uuid: Mapped[str] = mapped_column(ForeignKey("library_users.user_uuid"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(100), nullable=False)
    user_agent: Mapped[str] = mapped_column(String(200), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_refreshed: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("LibraryUser", back_populates="sessions")


    @staticmethod
    def create_session(session: Session, user_uuid: str, device_id: str,
                       user_agent: str = None, ip_address: str = None,
                       ttl_minutes: int = 720) -> "UserSession":
        """
        Creates a new session for the given user.
        """
        now = datetime.now(timezone.utc)
        new_session = UserSession(
            user_uuid=user_uuid,
            device_id=device_id,
            user_agent=user_agent,
            ip_address=ip_address,
            created_at=now,
            expires_at=now + timedelta(minutes=ttl_minutes),
            last_refreshed=now
        )
        session.add(new_session)
        session.commit()
        return new_session


    @staticmethod
    def get_active_sessions(session: Session, user_uuid: str) -> list:
        """
        Get all active sessions of the user.
        """
        stmt = select(UserSession).where(
            UserSession.user_uuid == user_uuid,
            UserSession.is_active.is_(True)
        )
        return list(session.scalars(stmt).all())


    @staticmethod
    def refresh_session(session: Session, session_id: str) -> None:
        """
        Update the last_refreshed timestamp and extend expiry.
        """
        stmt = select(UserSession).where(
            UserSession.session_id == session_id,
            UserSession.is_active.is_(True)
        )
        db_session = session.scalar(stmt)

        if db_session:
            now = datetime.now(timezone.utc)
            db_session.last_refreshed = now
            db_session.expires_at = now + timedelta(minutes=720)
            session.commit()


    @staticmethod
    def invalidate_session(session: Session, session_id: str) -> bool:
        """
        Mark a single session inactive (e.g., device logout).
        """
        stmt = select(UserSession).where(
            UserSession.session_id == session_id,
            UserSession.is_active.is_(True)
        )
        db_session = session.scalar(stmt)

        if not db_session:
            return False

        db_session.is_active = False
        session.commit()
        return True

    @staticmethod
    def deactivate_all_sessions(session: Session, user_uuid: str) -> int:
        """
        Mark all active sessions of a user as inactive.
        """
        stmt = (
            update(UserSession)
            .where(UserSession.user_uuid == user_uuid, UserSession.is_active.is_(True))
            .values(is_active=False)
        )
        result = session.execute(stmt)
        session.commit()
        return result.rowcount

    @staticmethod
    def cleanup_expired_sessions(session: Session) -> int:
        """
        Delete sessions that have expired more than 1 day ago.
        """
        threshold = datetime.now(timezone.utc) - timedelta(days=1)
        stmt = delete(UserSession).where(UserSession.expires_at < threshold)
        result = session.execute(stmt)
        session.commit()
        return result.rowcount

    def __repr__(self):
        return f"<UserSession(session_id='{self.session_id}', user_uuid='{self.user_uuid}', device='{self.device_id}', active={self.is_active})>"
