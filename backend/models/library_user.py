from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, select, Float, Boolean
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session, foreign
from sqlalchemy.sql import func
from datetime import datetime
import random
import uuid
from typing import Optional
from models.base import Base
from models.status_codes import StatusCode
from models.spiritual_maturity_level import SpiritualMaturityLevel
from utils.security import generate_password_hash, check_password_hash, verify_strong_password
from utils.timezone_utils import utc_now
from utils.my_logger import CustomLogger
from constants.constants import OPS_LOG_FILE
from constants.config import LOG_LEVEL
from models.exceptions import DuplicateUserError, UserNotFoundError, WeakPasswordError, SpiritualMaturityLevelNotFound, DuplicateUserIdError, OfficeNotFoundError


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


class LibraryUser(Base):
    __tablename__ = 'users'

    user_uuid: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(30), nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(120), unique=True, nullable=True)
    phone_number: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    registration_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_now, nullable=False)
    role: Mapped[int] = mapped_column(ForeignKey('user_roles.rank'), default=3, nullable=False)
    membership_type: Mapped[int] = mapped_column(ForeignKey('library_memberships.rank'), default=5, nullable=False)
    account_status: Mapped[str] = mapped_column(ForeignKey('status_codes.code'), default='UNVERIFIED', nullable=False)
    borrowed_books: Mapped[list] = mapped_column(JSON, default=list)
    fines_due: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    spiritual_maturity: Mapped[int] = mapped_column(Integer, ForeignKey("spiritual_maturity_levels.weight"), default=5, nullable=False)
    is_founder: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    
    # Address fields
    address_line_1: Mapped[str] = mapped_column(String(100), nullable=False)
    address_line_2: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[str] = mapped_column(String(50), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    registered_at_office: Mapped[str] = mapped_column(String(5), ForeignKey('library_offices.office_code'), nullable=False)

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
    maturity_level = relationship(
        "SpiritualMaturityLevel",
        primaryjoin=foreign(spiritual_maturity) == SpiritualMaturityLevel.weight,
        viewonly=True
)
    registration_office = relationship(
        "LibraryOffice",
        primaryjoin="LibraryUser.registered_at_office == LibraryOffice.office_code",
        viewonly=True
    )
    referral_codes_created = relationship(
        "ReferralCode",
        back_populates="owner",
        primaryjoin="LibraryUser.user_id == ReferralCode.code_owner"
    )

    @staticmethod
    def generate_user_id(office_tag: str, registration_date: datetime, sequence_number: Optional[int] = None) -> str:
        """
        Generate 15-character user ID: XXXMMYYNNNNNNNN
        Where:
        - XXX: office tag (3 characters, uppercase)
        - MM: month of registration (2 digits)
        - YY: year of registration (2 digits)
        - NNNNNNNN: 8-digit sequence number (randomly generated or provided)
        """
        # Validate office tag
        if len(office_tag) != 3:
            raise ValueError("Office tag must be exactly 3 characters long")
        
        if not office_tag.isalpha():
            raise ValueError("Office tag must contain only alphabetic characters")
        
        # Convert tag to uppercase
        tag_upper = office_tag.upper()
        
        # Extract month and year from registration date
        month = f"{registration_date.month:02d}"
        year = f"{registration_date.year % 100:02d}"
        
        # Generate or use provided sequence number (8 digits, > 10000000 and <= 99999999)
        if sequence_number is not None:
            if sequence_number <= 10000000 or sequence_number > 99999999:
                raise ValueError("Sequence number must be greater than 10000000 and less than or equal to 99999999")
            seq_num = f"{sequence_number:08d}"
        else:
            seq_num = f"{random.randint(10000000, 99999999):08d}"
        
        return f"{tag_upper}{month}{year}{seq_num}"


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
                    address_line_1: str, city: str, state: str, country: str, postal_code: str,
                    registered_at_office: str,
                    address_line_2: Optional[str] = None,
                    role: int = 3, spiritual_maturity: int = 5, membership_type: int = 5,
                    sequence_number: Optional[int] = None) -> "LibraryUser":
        """
        Create a new user in database with duplicate user ID protection.
        
        This method includes automatic duplicate handling:
        - For random sequence generation: Retries up to 5 times if user ID already exists
        - For provided sequence numbers: Raises DuplicateUserIdError immediately if duplicate found
        - Validates all other constraints (email/phone uniqueness, password strength, etc.)
        
        Raises:
            DuplicateUserError: If email or phone number already exists
            DuplicateUserIdError: If generated user ID already exists (after retries for random generation)
            WeakPasswordError: If password doesn't meet security requirements
            SpiritualMaturityLevelNotFound: If spiritual maturity level is invalid
        """
        # Verify if password meets security policy requirements
        is_strong, reason = verify_strong_password(
            password1=password, first_name=first_name,
            last_name=last_name, email=email or '', phone_number=phone_number
        )
        if not is_strong:
            LOGGER.error(f"Weak password for user '{first_name} {last_name}': {reason}")
            raise WeakPasswordError(reason)

        # Check if user with same email or phone number exists
        if email:
            stmt = select(cls).where((cls.email == email) | (cls.phone_number == phone_number))
        else:
            stmt = select(cls).where(cls.phone_number == phone_number)
        existing = session.execute(stmt).scalar_one_or_none()

        if existing:
            LOGGER.error(f"User with email or phone number already exists with id {existing.user_id}")
            raise DuplicateUserError("User with email or phone number already exists.")

        if spiritual_maturity <= 2:
            LOGGER.error(f"User with spiritual maturity 2 and below cannot be created.")
            raise SpiritualMaturityLevelNotFound(f"User with spiritual maturity 2 and below cannot be created.")

        # Get data for user creation
        registration_timestamp = utc_now()
        office_tag = registered_at_office[:3].upper()
        
        # Generate unique user ID with duplicate checking
        max_attempts = 5
        user_id = None
        for attempt in range(max_attempts):
            # Generate user ID
            candidate_id = cls.generate_user_id(office_tag, registration_timestamp, sequence_number)
            
            # Check if this user ID already exists
            existing_user_stmt = select(cls).where(cls.user_id == candidate_id)
            existing_user_with_id = session.execute(existing_user_stmt).scalar_one_or_none()
            
            if not existing_user_with_id:
                # User ID is unique, we can use it
                user_id = candidate_id
                break
            else:
                LOGGER.warning(f"Generated user ID {candidate_id} already exists, attempt {attempt + 1}/{max_attempts}")
                # If sequence_number was provided, we can't retry with random generation
                if sequence_number is not None:
                    LOGGER.error(f"Provided sequence number {sequence_number} resulted in duplicate user ID {candidate_id}")
                    raise DuplicateUserIdError(f"User ID {candidate_id} already exists. Cannot create user with provided sequence number.")
                # For random generation, continue to next attempt
        
        if user_id is None:
            LOGGER.error(f"Failed to generate unique user ID after {max_attempts} attempts")
            raise DuplicateUserIdError(f"Failed to generate unique user ID after {max_attempts} attempts. Please try again.")
        
        new_user = cls(
            user_uuid=str(uuid.uuid4()),
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            password_hash=generate_password_hash(password),
            registration_date=registration_timestamp,
            role=role,
            membership_type=membership_type,
            spiritual_maturity=spiritual_maturity,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            registered_at_office=registered_at_office
        )
        session.add(new_user)
        session.commit()
        LOGGER.info(f"New user {new_user} created successfully.")
        return new_user


    @staticmethod
    def view_user(session: Session, email: Optional[str], phone_number: str) -> dict:
        """
        View user details.
        """
        if email:
            stmt = select(LibraryUser).where((LibraryUser.email == email) | (LibraryUser.phone_number == phone_number), LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
        else:
            stmt = select(LibraryUser).where(LibraryUser.phone_number == phone_number, LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
        existing = session.execute(stmt).scalar_one_or_none()
        
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
            "Spiritual Maturity": existing.maturity_level.title,
            "Founder": existing.is_founder,
            "Address Line 1": existing.address_line_1,
            "Address Line 2": existing.address_line_2,
            "City": existing.city,
            "State": existing.state,
            "Country": existing.country,
            "Postal Code": existing.postal_code,
            "Registered at Office": existing.registered_at_office
        }


    @staticmethod
    def edit_user(session: Session, **kwargs) -> None:
        """
        Edit user details.
        """
        if kwargs.get("email"):
            stmt = select(LibraryUser).where(LibraryUser.email == kwargs["email"], LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
        elif kwargs.get("phone_number"):
            stmt = select(LibraryUser).where(LibraryUser.phone_number == kwargs["phone_number"], LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
        else:
            LOGGER.error("Missing 'email' or 'phone_number' key in search parameters.")
            raise KeyError("Missing 'email' or 'phone_number' key in search parameters.")
        existing = session.execute(stmt).scalar_one_or_none()

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
    def update_user_password(session: Session, email: Optional[str], phone_number: str, password: str) -> None:
        """
        Update user password only.
        """
        if email:
            stmt = select(LibraryUser).where((LibraryUser.email == email) | (LibraryUser.phone_number == phone_number), LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
        else:
            stmt = select(LibraryUser).where(LibraryUser.phone_number == phone_number, LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
        existing = session.execute(stmt).scalar_one_or_none()

        if not existing:
            LOGGER.error("User does not exist or is inactive.")
            raise UserNotFoundError("User does not exist or is inactive.")

        # Verify if password meets security policy requirements
        is_strong, reason = verify_strong_password(
            password1=password, first_name=existing.first_name,
            last_name=existing.last_name, email=existing.email or '', phone_number=existing.phone_number
        )
        if not is_strong:
            LOGGER.error(f"Weak password for user '{existing.user_id}': {reason}")
            raise WeakPasswordError(reason)
        
        # Hash and change password
        existing.password_hash = generate_password_hash(password)
        session.commit()
        LOGGER.info(f"Password updated for user '{existing.user_id}' successfully.")


    @staticmethod
    def delete_user(session: Session, email: Optional[str], phone_number: str) -> None:
        """
        Soft delete a user.
        """
        if email:
            stmt = select(LibraryUser).where((LibraryUser.email == email) | (LibraryUser.phone_number == phone_number), LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
        else:
            stmt = select(LibraryUser).where(LibraryUser.phone_number == phone_number, LibraryUser.account_status.in_(['ACTIVE', 'BLOCKED']))
        existing = session.execute(stmt).scalar_one_or_none()

        if not existing:
            LOGGER.error("User does not exist or is inactive.")
            raise UserNotFoundError("User does not exist or is inactive.")

        # set account status as inactive
        existing.account_status = 'INACTIVE'
        session.commit()
        LOGGER.info(f"User '{existing.user_id}' - '{existing.first_name} {existing.last_name}' deactivated successfully.")
