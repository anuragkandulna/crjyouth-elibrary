from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, select, SmallInteger
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, Session
from datetime import datetime
from typing import Optional
import random
import uuid

from models.base import Base
from utils.security import generate_password_hash, check_password_hash, verify_strong_password
from utils.timezone_utils import utc_now
from utils.my_logger import CustomLogger
from constants.constants import OPS_LOG_FILE, LIBRARY_ROLES
from constants.config import LOG_LEVEL
from models.exceptions import (
    DuplicateUserError, UserNotFoundError, WeakPasswordError, DuplicateUserIdError
)

LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


class User(Base):
    __tablename__ = 'users'

    user_uuid: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(30), nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    registration_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_now, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    account_status: Mapped[str] = mapped_column(ForeignKey('status_codes.code'), default='UNVERIFIED', nullable=False)
    user_role: Mapped[int] = mapped_column(SmallInteger, default=3, nullable=False)


    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, name={self.first_name} {self.last_name})>"


    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


    def is_admin(self) -> bool:
        return self.user_role == 1


    def is_moderator(self) -> bool: 
        return self.user_role in (1, 2)


    def is_member(self) -> bool:
        return self.user_role in (1, 2, 3)


    @staticmethod
    def generate_user_id(seed: Optional[int] = None) -> int:
        if seed and 1000 <= seed <= 999999:
            return seed
        return random.randint(100000, 999999)


    @classmethod
    def create_user(cls, session: Session, first_name: str, last_name: str,
                    email: str, phone_number: str, password: str,
                    seed_user_id: Optional[int] = None) -> "User":

        is_strong, reason = verify_strong_password(
            password1=password, first_name=first_name,
            last_name=last_name, email=email, phone_number=phone_number
        )
        if not is_strong:
            LOGGER.error(f"Weak password for {email}: {reason}")
            raise WeakPasswordError(reason)

        stmt = select(cls).where((cls.email == email) | (cls.phone_number == phone_number))
        if session.execute(stmt).scalar_one_or_none():
            LOGGER.error(f"Duplicate email or phone: {email}, {phone_number}")
            raise DuplicateUserError("User with email or phone number already exists.")

        max_attempts = 5
        for attempt in range(max_attempts):
            candidate_id = cls.generate_user_id(seed_user_id)
            id_check = session.execute(select(cls).where(cls.user_id == candidate_id)).scalar_one_or_none()
            if not id_check:
                break
            LOGGER.warning(f"User ID {candidate_id} already exists (attempt {attempt+1})")
            if seed_user_id:
                raise DuplicateUserIdError(f"User ID {candidate_id} already exists.")
        else:
            LOGGER.error("Failed to generate unique user ID after multiple attempts")
            raise DuplicateUserIdError("Failed to generate unique user ID after multiple attempts.")

        new_user = cls(
            user_id=candidate_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            password_hash=generate_password_hash(password)
        )
        session.add(new_user)
        session.commit()
        LOGGER.info(f"User created: {new_user}")
        return new_user


    @staticmethod
    def view_user(session: Session, email: Optional[str], phone_number: str) -> dict:
        stmt = select(User).where(
            ((User.email == email) | (User.phone_number == phone_number)) if email else (User.phone_number == phone_number),
            User.account_status.in_(['ACTIVE', 'BLOCKED'])
        )
        user = session.execute(stmt).scalar_one_or_none()
        if not user:
            LOGGER.error(f"User not found for email={email}, phone={phone_number}")
            raise UserNotFoundError("User does not exist or is inactive.")
        LOGGER.info(f"Viewed user: {user.user_id}")
        return {
            "User ID": user.user_id,
            "Name": f"{user.first_name} {user.last_name}",
            "Email": user.email,
            "Phone": user.phone_number,
            "Status": user.account_status,
            "Role": LIBRARY_ROLES[user.user_role]
        }


    @staticmethod
    def edit_user(session: Session, **kwargs) -> None:
        identifier = kwargs.get("email") or kwargs.get("phone_number")
        if not identifier:
            LOGGER.error("Missing identifier in edit_user")
            raise KeyError("Missing 'email' or 'phone_number' key in parameters.")

        stmt = select(User).where(
            ((User.email == kwargs["email"]) | (User.phone_number == kwargs["phone_number"])) if kwargs.get("email")
            else (User.phone_number == kwargs["phone_number"]),
            User.account_status.in_(['ACTIVE', 'BLOCKED'])
        )
        user = session.execute(stmt).scalar_one_or_none()
        if not user:
            LOGGER.error(f"User not found for edit: {identifier}")
            raise UserNotFoundError("User does not exist or is inactive.")

        if "password" in kwargs:
            LOGGER.warning(f"Password update blocked for user {user.user_id}")
            kwargs.pop("password")

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        session.commit()
        LOGGER.info(f"User updated: {user.user_id} fields={list(kwargs.keys())}")


    @staticmethod
    def update_user_password(session: Session, email: Optional[str], phone_number: str, password: str) -> None:
        stmt = select(User).where(
            ((User.email == email) | (User.phone_number == phone_number)) if email else (User.phone_number == phone_number),
            User.account_status.in_(['ACTIVE', 'BLOCKED'])
        )
        user = session.execute(stmt).scalar_one_or_none()
        if not user:
            LOGGER.error(f"User not found for password reset: {email}, {phone_number}")
            raise UserNotFoundError("User does not exist or is inactive.")

        is_strong, reason = verify_strong_password(
            password1=password, first_name=user.first_name,
            last_name=user.last_name, email=user.email or '', phone_number=user.phone_number
        )
        if not is_strong:
            LOGGER.error(f"Weak password for user {user.user_id}: {reason}")
            raise WeakPasswordError(reason)

        user.password_hash = generate_password_hash(password)
        session.commit()
        LOGGER.info(f"Password updated for user: {user.user_id}")


    @staticmethod
    def delete_user(session: Session, email: Optional[str], phone_number: str) -> None:
        stmt = select(User).where(
            ((User.email == email) | (User.phone_number == phone_number)) if email else (User.phone_number == phone_number),
            User.account_status.in_(['ACTIVE', 'BLOCKED'])
        )
        user = session.execute(stmt).scalar_one_or_none()
        if not user:
            LOGGER.error(f"User not found for delete: {email}, {phone_number}")
            raise UserNotFoundError("User does not exist or is inactive.")

        user.account_status = 'INACTIVE'
        session.commit()
        LOGGER.info(f"User deactivated: {user.user_id}")
