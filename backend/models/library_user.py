from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import random
from typing import Optional
from models.base import Base
from models.user_role import UserRole
from models.library_membership import LibraryMembership
from models.status_codes import StatusCode
from utils.security import generate_password_hash, check_password_hash 
from utils.my_logger import CustomLogger


LOGGER = CustomLogger(__name__, level=20, log_file='crjyouth_operations.log').get_logger()


class LibraryUser(Base):
    __tablename__ = 'users'

    user_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(30), nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(15), unique=True, nullable=True)
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
        return f"<LibraryUser(user_id='{self.user_id}', name='{self.first_name} {self.last_name}', active={self.account_status})>"


    # ------------------ CRUD Operations ------------------ #
    @classmethod
    def create_user(cls, session: Session,
                    first_name: str, last_name: str,
                    email: str, phone_number: Optional[str], password: str,
                    role: int = 3, membership_type: int = 5) -> "LibraryUser":
        """
        Create a new user in database.
        """
        # Check if user with same email or phone number exists
        if phone_number:
            existing = session.query(cls).filter(
                (cls.email == email) | (cls.phone_number == phone_number)
            ).first()
        else:
            existing = session.query(cls).filter(
                (cls.email == email)
            ).first()

        if existing:
            LOGGER.error(f"User with email or phone number already exists. User ID: {existing.user_id}")
            raise ValueError(f"User with email or phone number already exists. User ID: {existing.user_id}")

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
        LOGGER.info(f"User '{new_user.user_id}' - '{new_user.first_name} {new_user.last_name}' created successfully.")
        return new_user


    @staticmethod
    def view_user(session: Session, email: str) -> dict:
        """
        View user details.
        """
        existing = session.query(LibraryUser).filter(
            (LibraryUser.email == email),
            (LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
        ).first()
        if not existing:
            LOGGER.error("User does not exist or is inactive.")
            raise ValueError("User does not exist or is inactive.")

        return {
            "User UUID": existing.user_uuid,
            "User ID": existing.user_id,
            "Name": f"{existing.first_name} {existing.last_name}",
            "Email": existing.email,
            "Phone": existing.phone_number,
            "Role": existing.role,
            "Membership": existing.membership_type,
            "Status": existing.account_status,
            "Pastor": existing.is_pastor,
            "Founder": existing.is_founder
        }


    @staticmethod
    def edit_user(session: Session, email: str, **kwargs) -> None:
        """
        Edit user details.
        """
        existing = session.query(LibraryUser).filter(
            (LibraryUser.email == email),
            (LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
        ).first()
        if not existing:
            LOGGER.error("User does not exist or is inactive.")
            raise ValueError("User does not exist or is inactive.")

        for key, value in kwargs.items():
            if key == "password":
                setattr(existing, key, generate_password_hash(value))  
            elif hasattr(existing, key):
                setattr(existing, key, value)

        session.commit()
        LOGGER.info(f"User '{existing.user_id}' - '{existing.first_name} {existing.last_name}' updated successfully.")


    @staticmethod
    def delete_user(session: Session, email: str) -> None:
        """
        Soft delete a user.
        """
        existing = session.query(LibraryUser).filter(
            (LibraryUser.email == email),
            (LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
        ).first()
        if not existing:
            LOGGER.error("User does not exist or is inactive.")
            raise ValueError("User does not exist or is inactive.")

        existing.account_status = 'INACTIVE'  # Soft delete
        session.commit()
        LOGGER.info(f"User '{existing.user_id}' - '{existing.first_name} {existing.last_name}' deactivated successfully.")
