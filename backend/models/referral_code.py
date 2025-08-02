# models/referral_code.py
from sqlalchemy import Integer, String, Boolean, ForeignKey, select, TIMESTAMP
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, Session, relationship
from models.base import Base
from utils.timezone_utils import utc_now
from utils.my_logger import CustomLogger
from constants.constants import OPS_LOG_FILE
from constants.config import LOG_LEVEL
from models.exceptions import ReferralCodeNotFoundError, ReferralCodeValidationError, DuplicateReferralError
from typing import Optional


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


class ReferralCode(Base):
    __tablename__ = "referral_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code_owner: Mapped[str] = mapped_column(String(15), ForeignKey('users.user_id'), nullable=False)
    invited_phone: Mapped[str] = mapped_column(String(15), nullable=False)  # Phone number of invited user
    assigned_office: Mapped[str] = mapped_column(String(5), ForeignKey('library_offices.office_code'), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_now, nullable=False)

    # Relationships
    owner = relationship(
        "LibraryUser",
        back_populates="referral_codes_created",
        primaryjoin="ReferralCode.code_owner == LibraryUser.user_id"
    )
    office = relationship(
        "LibraryOffice",
        primaryjoin="ReferralCode.assigned_office == LibraryOffice.office_code"
    )


    @classmethod
    def create_code(cls, session: Session, owner: str, invited_phone: str, assigned_office: str) -> "ReferralCode":
        """
        Create and persist a new referral code record.
        
        Args:
            session: Database session
            owner: User UUID of the code owner (inviter)
            invited_phone: Phone number of the invited user
            
        Returns:
            ReferralCode: Created referral code
            
        Raises:
            ReferralCodeValidationError: If validation fails
            DuplicateReferralError: If referral already exists for this phone
        """
        # Check if referral already exists for this phone number
        stmt = select(cls).where(
            cls.invited_phone == invited_phone,
            cls.is_active == True
        )
        existing = session.execute(stmt).scalar_one_or_none()
        
        if existing:
            LOGGER.error(f"Active referral already exists for phone ending with {invited_phone[-2:]}")
            raise DuplicateReferralError(f"Active referral already exists for phone ending with {invited_phone[-2:]}")

        # Create new referral code
        referral = cls(
            code_owner=owner,
            invited_phone=invited_phone,
            is_active=True,
            assigned_office=assigned_office
        )
        
        session.add(referral)
        session.commit()
        
        LOGGER.info(f"Referral code {referral.id} created for phone ending with {invited_phone[-2:]}")
        return referral


    @classmethod
    def use_code(cls, session: Session, referral_id: int, invited_phone: str) -> "ReferralCode":
        """
        Mark usage of a referral code by validating the invited user's phone number.
        
        Args:
            session: Database session
            referral_id: Referral code ID
            invited_phone: Phone number of the invited user
            
        Returns:
            ReferralCode: Updated referral code or None if invalid
            
        Raises:
            ReferralCodeNotFoundError: If referral code not found
            ReferralCodeValidationError: If validation fails
        """
        stmt = select(cls).where(cls.id == referral_id)
        existing = session.execute(stmt).scalar_one_or_none()
        if not existing:
            LOGGER.error(f"Referral code {referral_id} not found")
            raise ReferralCodeNotFoundError("Referral code not found")

        if not existing.is_active:
            LOGGER.error(f"Referral code {referral_id} is not active")
            raise ReferralCodeValidationError("Referral code is not active")

        # Check if phone number matches
        if existing.invited_phone != invited_phone:
            LOGGER.error(f"Phone number mismatch for referral {referral_id}")
            raise ReferralCodeValidationError("Phone number does not match referral code.")

        # Deactivate the referral code (single use)
        existing.is_active = False
        
        session.commit()
        LOGGER.info(f"Referral code {referral_id} used by phone ending with {invited_phone[-2:]}")


    @classmethod
    def get_referral_by_phone(cls, session: Session, phone_number: str) -> Optional["ReferralCode"]:
        """
        Get active referral code by invited user's phone number.
        
        Args:
            session: Database session
            phone_number: Phone number of invited user
            
        Returns:
            ReferralCode: Active referral code or None if not found
        """
        stmt = select(cls).where(
            cls.invited_phone == phone_number,
            cls.is_active == True
        )
        existing = session.execute(stmt).scalar_one_or_none()
        
        if existing:
            LOGGER.info(f"Found active referral code {existing.id} for phone ending with {phone_number[-2:]}")
        else:
            LOGGER.info(f"No active referral code found for phone ending with {phone_number[-2:]}")
            
        return existing


    @classmethod
    def deactivate_code(cls, session: Session, referral_id: int) -> None:
        """
        Deactivate a referral code.
        
        Args:
            session: Database session
            referral_id: Referral code ID
            
        Raises:
            ReferralCodeNotFoundError: If referral code not found
        """
        stmt = select(cls).where(cls.id == referral_id)
        existing = session.execute(stmt).scalar_one_or_none()
        if not existing:
            LOGGER.error(f"Referral code {referral_id} not found.")
            raise ReferralCodeNotFoundError("Referral code not found.")

        existing.is_active = False
        session.commit()
        LOGGER.info(f"Referral code {referral_id} deactivated.")


    def __repr__(self) -> str:
        return f"<ReferralCode(id={self.id}, owner='{self.code_owner}', active={self.is_active})>"
