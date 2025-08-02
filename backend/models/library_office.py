from sqlalchemy.orm import Mapped, mapped_column, Session
from sqlalchemy import Integer, String, select, Boolean
from models.base import Base
from utils.my_logger import CustomLogger
from constants.constants import OPS_LOG_FILE
from constants.config import LOG_LEVEL
from models.exceptions import DuplicateOfficeError, OfficeNotFoundError, OfficeValidationError
from typing import Optional
from models.library_user import LibraryUser
from models.library_transaction import LibraryTransaction


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


class LibraryOffice(Base):
    __tablename__ = "library_offices"

    office_code: Mapped[str] = mapped_column(String(5), primary_key=True)
    office_tag: Mapped[str] = mapped_column(String(3), nullable=False)
    office_num: Mapped[int] = mapped_column(Integer, nullable=False)
    address: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[str] = mapped_column(String(50), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


    @staticmethod
    def generate_office_code(office_tag: str, office_num: int) -> str:
        """
        Generate 5-character office code: XXXNN
        Where:
        - XXX: office tag (3 characters, uppercase)
        - NN: office number (2 digits, 01-99)
        
        Args:
            office_tag: 3-character office tag
            office_num: Office number (1-99)
            
        Returns:
            str: 5-character office code
            
        Raises:
            OfficeValidationError: If parameters are invalid
        """
        # Validate office tag
        if len(office_tag) != 3:
            LOGGER.error(f"Office tag {office_tag} must be exactly 3 characters long")
            raise OfficeValidationError("Office tag must be exactly 3 characters long")
        
        if not office_tag.isalpha():
            LOGGER.error(f"Office tag {office_tag} must contain only alphabetic characters")
            raise OfficeValidationError("Office tag must contain only alphabetic characters")
        
        # Validate office number
        if office_num < 1 or office_num > 99:
            LOGGER.error(f"Office number {office_num} must be between 1 and 99")
            raise OfficeValidationError("Office number must be between 1 and 99")
        
        # Convert tag to uppercase and format number
        tag_upper = office_tag.upper()
        num_str = f"{office_num:02d}"
        
        return f"{tag_upper}{num_str}"


    def __repr__(self) -> str:
        return f"<LibraryOffice(office_code='{self.office_code}', city='{self.city}', pincode='{self.pincode}')>"


    @classmethod
    def create_office(cls, session: Session, office_tag: str, office_num: int,
                     address: str, city: str, state: str, country: str, pincode: str) -> "LibraryOffice":
        """
        Create a new library office.
        
        Args:
            session: Database session
            office_tag: 3-character office tag
            office_num: Office number (1-99)
            address: Office address
            city: City
            state: State
            country: Country
            pincode: Postal code
            
        Returns:
            LibraryOffice: Created office
            
        Raises:
            OfficeValidationError: If validation fails
            DuplicateOfficeError: If office code already exists
        """
        # Generate office code
        office_code = cls.generate_office_code(office_tag, office_num)

        # Check if office code already exists
        stmt = select(cls).where(cls.office_code == office_code)
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            LOGGER.error(f"Office code {office_code} already exists.")
            raise DuplicateOfficeError(f"Office code {office_code} already exists.")

        # Create new office
        office = cls(
            office_code=office_code,
            office_tag=office_tag.upper(),
            office_num=office_num,
            address=address,
            city=city,
            state=state,
            country=country,
            pincode=pincode
        )

        session.add(office)
        session.commit()
        LOGGER.info(f"Library office {office_code} created successfully")
        return office


    @classmethod
    def view_office(cls, session: Session, office_code: str) -> dict:
        """
        View office details.
        
        Args:
            session: Database session
            office_code: Office code to view
            
        Returns:
            dict: Office details
            
        Raises:
            OfficeNotFoundError: If office not found
        """
        stmt = select(cls).where(cls.office_code == office_code)
        office = session.execute(stmt).scalar_one_or_none()
        if not office:
            LOGGER.error(f"Office {office_code} not found.")
            raise OfficeNotFoundError("Office not found.")
        
        return {
            "office_code": office.office_code,
            "office_tag": office.office_tag,
            "office_num": office.office_num,
            "address": office.address,
            "city": office.city,
            "state": office.state,
            "country": office.country,
            "pincode": office.pincode
        }


    @classmethod
    def edit_office(cls, session: Session, office_code: str, **kwargs) -> None:
        """
        Edit office details.
        
        Args:
            session: Database session
            office_code: Office code to edit
            **kwargs: Fields to update
            
        Raises:
            OfficeNotFoundError: If office not found
            OfficeValidationError: If validation fails
        """
        stmt = select(cls).where(cls.office_code == office_code)
        existing = session.execute(stmt).scalar_one_or_none()
        if not existing:
            LOGGER.error(f"Office {office_code} not found for editing.")
            raise OfficeNotFoundError("Office not found")

        # Handle special case for office_tag and office_num
        for key in ['office_tag', 'office_num']:
            if key in kwargs:
                LOGGER.warning(f"Office {office_code} cannot be updated with {key}.")
                kwargs.pop(key)

        # Update other fields
        for key, value in kwargs.items():
            setattr(existing, key, value)

        session.commit()
        LOGGER.info(f"Office '{existing.office_code}' - {kwargs.keys()} updated successfully.")


    @classmethod
    def delete_office(cls, session: Session, office_code: str) -> None:
        """
        Delete a library office.
        
        Args:
            session: Database session
            office_code: Office code to delete
            
        Raises:
            OfficeNotFoundError: If office not found
            OfficeValidationError: If office has associated data
        """
        stmt = select(cls).where(cls.office_code == office_code)
        existing = session.execute(stmt).scalar_one_or_none()
        if not existing:
            LOGGER.error(f"Office {office_code} not found for deletion.")
            raise OfficeNotFoundError("Office not found")

        # Check for associated users
        stmt = select(LibraryUser).where(LibraryUser.registered_at_office == office_code)
        users = session.execute(stmt).scalars().all()
        if users:
            LOGGER.error(f"Cannot delete office with {len(users)} registered users.")
            raise OfficeValidationError(f"Cannot delete office with {len(users)} registered users.")

        # Check for associated transactions
        stmt = select(LibraryTransaction).where(LibraryTransaction.office_code == office_code)
        transactions = session.execute(stmt).scalars().all()
        if transactions:
            LOGGER.error(f"Cannot delete office with {len(transactions)} associated transactions.")
            raise OfficeValidationError(f"Cannot delete office with {len(transactions)} associated transactions.")

        # Soft delete office
        existing.is_active = False
        session.commit()
        LOGGER.info(f"Office {office_code} deactivated successfully")


    @classmethod
    def get_all_offices(cls, session: Session) -> list:
        """
        Get all library offices.
        
        Args:
            session: Database session
            
        Returns:
            list: List of office details
        """
        stmt = select(cls).order_by(cls.office_code)
        offices = session.execute(stmt).scalars().all()
        return [cls.view_office(session, office.office_code) for office in offices]
