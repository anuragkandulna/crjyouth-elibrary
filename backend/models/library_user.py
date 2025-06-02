from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy.sql import func
from datetime import datetime
import random
import uuid
from typing import Optional
from models.base import Base
from models.user_role import UserRole
from models.library_membership import LibraryMembership
from models.status_codes import StatusCode
from utils.security import generate_password_hash, check_password_hash, verify_strong_password
from utils.my_logger import CustomLogger
from constants.constants import OPS_LOG_FILE
from constants.config import LOG_LEVEL
from models.exceptions import DuplicateUserError, UserNotFoundError, WeakPasswordError


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


class LibraryUser(Base):
    __tablename__ = 'users'

    user_uuid: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(30), nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=True)
    phone_number: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    registration_date: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    role: Mapped[int] = mapped_column(ForeignKey('user_roles.rank'), default=3, nullable=False)
    membership_type: Mapped[int] = mapped_column(ForeignKey('library_memberships.rank'), default=5, nullable=False)
    account_status: Mapped[str] = mapped_column(ForeignKey('status_codes.code'), default='ACTIVE', nullable=False)
    borrowed_books: Mapped[list] = mapped_column(JSON, default=list)
    fines_due: Mapped[float] = mapped_column(default=0.0)
    is_pastor: Mapped[bool] = mapped_column(default=False)
    is_founder: Mapped[bool] = mapped_column(default=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)

    user_status = relationship("StatusCode", backref="acc_status")
    user_role = relationship(
        "UserRole",
        back_populates="users", 
        primaryjoin="LibraryUser.role == UserRole.rank"
    )
    user_membership = relationship(
        "LibraryMembership", 
        back_populates="users", 
        primaryjoin="LibraryUser.membership_type == LibraryMembership.rank"
    )


    @staticmethod
    def generate_user_id() -> int:
        """
        Generate 8-digit user ID: 1-00-00-000 to 9-99-99-999
        """
        return random.randint(10000000, 99999999)


    def check_password(self, password: str) -> bool:
        """
        Verify password by comparing hash.
        """
        return check_password_hash(self.password_hash, password)


    def check_permission(self, action: str) -> bool:
        """
        Check if user_role has a valid permission.
        """
        if self.user_role and action in self.user_role.permissions:
            return True
        return False


    def __repr__(self) -> str:
        return f"<LibraryUser(user_id='{self.user_id}', name='{self.first_name} {self.last_name}', active='{self.account_status}')>"


    # ------------------ CRUD Operations ------------------ #
    @classmethod
    def create_user(cls, session: Session, first_name: str, last_name: str,
                    email: Optional[str], phone_number: str, password: str,
                    role: int = 3, membership_type: int = 5) -> "LibraryUser":
        """
        Create a new user in database.
        """
        # Verify if password meets security policy requirements
        is_strong, reason = verify_strong_password(
            password1=password, first_name=first_name,
            last_name=last_name, email=email, phone_number=phone_number
        )
        if not is_strong:
            LOGGER.error(f"Weak password for user '{first_name} {last_name}': {reason}")
            raise WeakPasswordError(reason)

        # Check if user with same email or phone number exists
        stmt = select(cls).where((cls.email == email) | (cls.phone_number == phone_number)) if email else select(cls).where(cls.phone_number == phone_number)
        existing = session.execute(stmt).scalar_one_or_none()

        if existing:
            LOGGER.error(f"User with email or phone number already exists with id {existing.user_id}")
            raise DuplicateUserError("User with email or phone number already exists.")

        new_user = cls(
            user_uuid=str(uuid.uuid4()),
            user_id=cls.generate_user_id(),
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            password_hash=generate_password_hash(password),
            role=role,
            membership_type=membership_type
        )
        session.add(new_user)
        session.commit()
        LOGGER.info(f"New user {new_user} created successfully.")
        return new_user


    @staticmethod
    def view_user(session: Session, email: Optional[str], phone_number: Optional[str]) -> dict:
        """
        View user details.
        """
        if email:
            existing = session.query(LibraryUser).filter(
                (LibraryUser.email == email),
                (LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
            ).first()
        elif phone_number:
            existing = session.query(LibraryUser).filter(
                (LibraryUser.phone_number == phone_number),
                (LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
            ).first()
        else:
            LOGGER.error("Missing 'email' or 'phone_number' key in search parameters.")
            raise KeyError("Missing 'email' or 'phone_number' key in search parameters.")

        if not existing:
            LOGGER.error("User does not exist or is inactive.")
            raise UserNotFoundError("User does not exist or is inactive.")

        return {
            "User ID": existing.user_id,
            "First Name": existing.first_name,
            "Last Name": existing.last_name,
            "Email": existing.email,
            "Phone": existing.phone_number,
            "Role": existing.role,
            "Membership": existing.membership_type,
            "Status": existing.account_status,
            "Pastor": existing.is_pastor,
            "Founder": existing.is_founder
        }


    @staticmethod
    def edit_user(session: Session, **kwargs) -> None:
        """
        Edit user details.
        """
        if kwargs.get("email"):
            existing = session.query(LibraryUser).filter(
                (LibraryUser.email == kwargs["email"]),
                (LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
            ).first()
        elif kwargs.get("phone_number"):
            existing = session.query(LibraryUser).filter(
                (LibraryUser.phone_number == kwargs["phone_number"]),
                (LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
            ).first()
        else:
            LOGGER.error("Missing 'email' or 'phone_number' key in search parameters.")
            raise KeyError("Missing 'email' or 'phone_number' key in search parameters.")

        if not existing:
            LOGGER.error("User does not exist or is inactive.")
            raise UserNotFoundError("User does not exist or is inactive.")

        if "password" in kwargs:
            LOGGER.warning("Password cannot be change by this way.")
            kwargs.pop("password")

        for key, value in kwargs.items():
            setattr(existing, key, value)

        session.commit()
        LOGGER.info(f"User '{existing.user_id}' - {kwargs.keys()} updated successfully.")


    @staticmethod
    def update_user_password(session: Session, email: Optional[str], phone_number: Optional[str], password: str) -> None:
        """
        Update user password only.
        """
        if email:
            existing = session.query(LibraryUser).filter(
                (LibraryUser.email == email),
                (LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
            ).first()
        elif phone_number:
            existing = session.query(LibraryUser).filter(
                (LibraryUser.phone_number == phone_number),
                (LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
            ).first()
        else:
            LOGGER.error("Missing 'email' or 'phone_number' key in search parameters.")
            raise KeyError("Missing 'email' or 'phone_number' key in search parameters.")

        if not existing:
            LOGGER.error("User does not exist or is inactive.")
            raise UserNotFoundError("User does not exist or is inactive.")

        # Verify if password meets security policy requirements
        is_strong, reason = verify_strong_password(
            password1=password, first_name=existing.first_name,
            last_name=existing.last_name, email=existing.email, phone_number=existing.phone_number
        )
        if not is_strong:
            LOGGER.error(f"Weak password for user '{existing.user_id}': {reason}")
            raise WeakPasswordError(reason)
        
        # Hash and change password
        existing.password_hash = generate_password_hash(password)
        session.commit()
        LOGGER.info(f"Password updated for user '{existing.user_id}' successfully.")


    @staticmethod
    def delete_user(session: Session, email: Optional[str], phone_number: Optional[str]) -> None:
        """
        Soft delete a user.
        """
        if email:
            existing = session.query(LibraryUser).filter(
                (LibraryUser.email == email),
                (LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
            ).first()
        elif phone_number:
            existing = session.query(LibraryUser).filter(
                (LibraryUser.phone_number == phone_number),
                (LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
            ).first()
        else:
            LOGGER.error("Missing 'email' or 'phone_number' key in search parameters.")
            raise KeyError("Missing 'email' or 'phone_number' key in search parameters.")

        if not existing:
            LOGGER.error("User does not exist or is inactive.")
            raise UserNotFoundError("User does not exist or is inactive.")

        # set account status as inactive
        existing.account_status = 'INACTIVE'
        session.commit()
        LOGGER.info(f"User '{existing.user_id}' - '{existing.first_name} {existing.last_name}' deactivated successfully.")
