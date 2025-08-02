from sqlalchemy import String, Integer, Boolean, DateTime, Float, ForeignKey, func, Text, select
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from datetime import datetime
import uuid
from typing import Optional
from constants.constants import OPS_LOG_FILE
from models.base import Base
from utils.timezone_utils import utc_now
from models.library_user import LibraryUser
from utils.my_logger import CustomLogger
from constants.config import LOG_LEVEL
from models.exceptions import (
    DuplicateTransactionError, TransactionNotFoundError, TransactionValidationError
)


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


class LibraryTransaction(Base):
    __tablename__ = "library_transactions"

    transaction_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    ticket_id: Mapped[str] = mapped_column(String(15), primary_key=True)
    ticket_serial: Mapped[int] = mapped_column(Integer, nullable=False)
    office_code: Mapped[str] = mapped_column(String(5), ForeignKey('library_offices.office_code'), nullable=False)
    customer_id: Mapped[Optional[str]] = mapped_column(ForeignKey('users.user_id'), nullable=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    librarian_id: Mapped[Optional[str]] = mapped_column(ForeignKey('users.user_id'), nullable=True)
    copy_id: Mapped[Optional[str]] = mapped_column(ForeignKey('book_copies.copy_id'), nullable=True)
    status: Mapped[str] = mapped_column(ForeignKey('status_codes.code'), nullable=False)
    particulars: Mapped[str] = mapped_column(String(255), nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Ticket lifecycle dates (full timestamps)
    ticket_created_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_now, nullable=False)
    ticket_updated_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    ticket_closed_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    # Book transaction dates (date-only, time set to 00:00:00 UTC)
    book_borrow_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    book_due_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    book_return_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    # Extension tracking
    is_extended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Fine tracking
    fine_incurred: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fine_forgiven: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fine_forgiven_by: Mapped[Optional[str]] = mapped_column(ForeignKey('users.user_id'), nullable=True)
    fine_forgiven_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    # Created by tracking
    created_by_customer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    office = relationship(
        "LibraryOffice",
        foreign_keys=[office_code],
        backref="transactions"
    )

    customer = relationship(
        "LibraryUser",
        foreign_keys=[customer_id],
        backref="transactions_as_customer"
    )

    librarian = relationship(
        "LibraryUser",
        foreign_keys=[librarian_id],
        backref="transactions_as_librarian"
    )

    fine_forgiven_by_user = relationship(
        "LibraryUser",
        foreign_keys=[fine_forgiven_by],
        backref="fines_forgiven"
    )

    book_copy = relationship(
        "BookCopy",
        foreign_keys=[copy_id],
        backref="transactions"
    )


    def __repr__(self) -> str:
        return f"<LibraryTransaction(ticket_id={self.ticket_id}, status={self.status})>"


    @staticmethod
    def generate_ticket_id(office_code: str, current_year: int, serial_number: int, 
                          provided_ticket_id: Optional[str] = None) -> str:
        """
        Generate 15-character ticket ID: XXXXXYYNNNNNNNN
        Where:
        - XXXXX: office code (5 characters)
        - YY: current year (2 digits)
        - NNNNNNNN: 8-digit serial number
        
        Args:
            office_code: 5-character office code
            current_year: Current year (4 digits)
            serial_number: 8-digit serial number
            provided_ticket_id: If provided, validates and returns this ID
            
        Returns:
            str: 15-character ticket ID
            
        Raises:
            TransactionValidationError: If provided ticket ID is invalid
        """
        if provided_ticket_id:
            # Validate provided ticket ID format
            if len(provided_ticket_id) != 15:
                raise TransactionValidationError("Ticket ID must be exactly 15 characters long")
            
            if not provided_ticket_id[:5] == office_code:
                raise TransactionValidationError(f"Ticket ID must start with office code {office_code}")
            
            try:
                year_part = int(provided_ticket_id[5:7])
                serial_part = int(provided_ticket_id[7:15])
                
                expected_year = current_year % 100
                if year_part != expected_year:
                    raise TransactionValidationError(f"Ticket ID year must be {expected_year}")
                
                if serial_part < 1 or serial_part > 99999999:
                    raise TransactionValidationError("Serial number must be between 1 and 99999999")
                    
            except ValueError:
                raise TransactionValidationError("Invalid ticket ID format")
            
            return provided_ticket_id
        
        # Generate new ticket ID
        if serial_number < 1 or serial_number > 99999999:
            raise TransactionValidationError("Serial number must be between 1 and 99999999")
        
        year_str = f"{current_year % 100:02d}"
        serial_str = f"{serial_number:08d}"
        
        return f"{office_code}{year_str}{serial_str}"


    @classmethod
    def get_next_serial_number(cls, session: Session, office_code: str, year: int) -> int:
        """
        Get the next serial number for the given office and year.
        
        Args:
            session: Database session
            office_code: Office code
            year: Year
            
        Returns:
            int: Next serial number (1-based)
        """
        # Find the highest serial number for this office and year
        year_suffix = f"{year % 100:02d}"
        
        stmt = select(func.max(cls.ticket_serial)).where(
            cls.office_code == office_code,
            cls.ticket_id.like(f"{office_code}{year_suffix}%")
        )
        
        result = session.execute(stmt).scalar()
        next_serial = (result or 0) + 1
        
        if next_serial > 99999999:
            LOGGER.error(f"Serial number overflow for office {office_code} year {year}")
            raise TransactionValidationError(f"Maximum transactions exceeded for office {office_code} in year {year}")
        
        return next_serial


    @classmethod
    def create_transaction(cls, session: Session, customer: LibraryUser, copy_id: str, 
                         particulars: str, provided_ticket_id: Optional[str] = None) -> "LibraryTransaction":
        """
        Create a new transaction ticket by customer (CRUD operation).
        
        Args:
            session: Database session
            customer: Customer creating the ticket
            copy_id: Book copy ID to borrow
            particulars: Description of the transaction
            provided_ticket_id: Optional specific ticket ID to use
            
        Returns:
            LibraryTransaction: Created transaction
            
        Raises:
            TransactionValidationError: If validation fails
            DuplicateTransactionError: If ticket ID already exists
        """
        try:
            # Basic validation
            if not customer or not customer.user_id:
                LOGGER.error("Invalid customer provided for ticket creation")
                raise TransactionValidationError("Invalid customer")

            office_code = customer.registered_at_office
            current_year = utc_now().year
            
            # Generate ticket ID
            if provided_ticket_id:
                # Check if ticket ID already exists
                existing_ticket = session.query(cls).filter_by(ticket_id=provided_ticket_id).first()
                if existing_ticket:
                    LOGGER.error(f"Ticket ID {provided_ticket_id} already exists")
                    raise DuplicateTransactionError(f"Ticket ID {provided_ticket_id} already exists")
                
                ticket_id = cls.generate_ticket_id(office_code, current_year, 0, provided_ticket_id)
                # Extract serial number from provided ticket ID
                ticket_serial = int(provided_ticket_id[7:15])
            else:
                ticket_serial = cls.get_next_serial_number(session, office_code, current_year)
                ticket_id = cls.generate_ticket_id(office_code, current_year, ticket_serial)

            transaction = cls(
                transaction_uuid=str(uuid.uuid4()),
                ticket_id=ticket_id,
                ticket_serial=ticket_serial,
                office_code=office_code,
                customer_id=customer.user_id,
                customer_name=f"{customer.first_name} {customer.last_name}",
                copy_id=copy_id,
                status='PENDING',
                particulars=particulars,
                created_by_customer=True,
                librarian_id=None  # Will be assigned when approved
            )

            session.add(transaction)
            session.commit()
            LOGGER.info(f"Transaction ticket {transaction.ticket_id} created by customer {customer.user_id}")
            return transaction

        except Exception as ex:
            session.rollback()
            if isinstance(ex, (TransactionValidationError, DuplicateTransactionError)):
                raise
            LOGGER.error(f"Failed to create ticket by customer {customer.user_id if customer else 'unknown'}: {ex}")
            raise TransactionValidationError(f"Failed to create transaction ticket: {str(ex)}")


    @classmethod
    def create_staff_transaction(cls, session: Session, librarian: LibraryUser, office_code: str,
                               customer_id: Optional[str], customer_name: str, copy_id: Optional[str], 
                               particulars: str, provided_ticket_id: Optional[str] = None) -> "LibraryTransaction":
        """
        Create a new transaction ticket by staff (CRUD operation).
        
        Args:
            session: Database session
            librarian: Staff member creating the ticket
            office_code: Office where ticket is created
            customer_id: Optional customer ID
            customer_name: Customer name
            copy_id: Optional book copy ID
            particulars: Description of the transaction
            provided_ticket_id: Optional specific ticket ID to use
            
        Returns:
            LibraryTransaction: Created transaction
            
        Raises:
            TransactionValidationError: If validation fails
            DuplicateTransactionError: If ticket ID already exists
        """
        try:
            # Basic validation
            if not librarian or not librarian.user_id:
                LOGGER.error("Invalid librarian provided for ticket creation")
                raise TransactionValidationError("Invalid librarian")

            current_year = utc_now().year
            
            # Generate ticket ID
            if provided_ticket_id:
                # Check if ticket ID already exists
                existing_ticket = session.query(cls).filter_by(ticket_id=provided_ticket_id).first()
                if existing_ticket:
                    LOGGER.error(f"Ticket ID {provided_ticket_id} already exists")
                    raise DuplicateTransactionError(f"Ticket ID {provided_ticket_id} already exists")
                
                ticket_id = cls.generate_ticket_id(office_code, current_year, 0, provided_ticket_id)
                # Extract serial number from provided ticket ID
                ticket_serial = int(provided_ticket_id[7:15])
            else:
                ticket_serial = cls.get_next_serial_number(session, office_code, current_year)
                ticket_id = cls.generate_ticket_id(office_code, current_year, ticket_serial)

            transaction = cls(
                transaction_uuid=str(uuid.uuid4()),
                ticket_id=ticket_id,
                ticket_serial=ticket_serial,
                office_code=office_code,
                customer_id=customer_id,
                customer_name=customer_name,
                librarian_id=librarian.user_id,
                copy_id=copy_id,
                status='APPROVED' if copy_id else 'PENDING',
                particulars=particulars,
                created_by_customer=False
            )

            session.add(transaction)
            session.commit()
            LOGGER.info(f"Transaction ticket {transaction.ticket_id} created by staff {librarian.user_id}")
            return transaction

        except Exception as ex:
            session.rollback()
            if isinstance(ex, (TransactionValidationError, DuplicateTransactionError)):
                raise
            LOGGER.error(f"Failed to create ticket by staff {librarian.user_id if librarian else 'unknown'}: {ex}")
            raise TransactionValidationError(f"Failed to create transaction ticket: {str(ex)}")


    @classmethod
    def view_transaction(cls, session: Session, ticket_id: str) -> dict:
        """
        View transaction details (CRUD operation).
        
        Args:
            session: Database session
            ticket_id: Ticket ID to view
            
        Returns:
            dict: Transaction details
            
        Raises:
            TransactionNotFoundError: If transaction not found
        """
        try:
            transaction = session.query(cls).filter_by(ticket_id=ticket_id).first()
            if not transaction:
                LOGGER.error(f"Transaction {ticket_id} not found")
                raise TransactionNotFoundError("Transaction not found")

            return {
                "ticket_id": transaction.ticket_id,
                "ticket_serial": transaction.ticket_serial,
                "transaction_uuid": transaction.transaction_uuid,
                "office_code": transaction.office_code,
                "customer_id": transaction.customer_id,
                "customer_name": transaction.customer_name,
                "librarian_id": transaction.librarian_id,
                "copy_id": transaction.copy_id,
                "status": transaction.status,
                "particulars": transaction.particulars,
                "remarks": transaction.remarks,
                "created_by_customer": transaction.created_by_customer,
                "ticket_created_date": transaction.ticket_created_date.isoformat(),
                "ticket_updated_date": transaction.ticket_updated_date.isoformat(),
                "ticket_closed_date": transaction.ticket_closed_date.isoformat() if transaction.ticket_closed_date else None,
                "book_borrow_date": transaction.book_borrow_date.date().isoformat() if transaction.book_borrow_date else None,
                "book_due_date": transaction.book_due_date.date().isoformat() if transaction.book_due_date else None,
                "book_return_date": transaction.book_return_date.date().isoformat() if transaction.book_return_date else None,
                "is_extended": transaction.is_extended,
                "fine_incurred": transaction.fine_incurred,
                "fine_forgiven": transaction.fine_forgiven,
                "fine_forgiven_by": transaction.fine_forgiven_by,
                "fine_forgiven_date": transaction.fine_forgiven_date.isoformat() if transaction.fine_forgiven_date else None
            }

        except Exception as ex:
            if isinstance(ex, TransactionNotFoundError):
                raise
            LOGGER.error(f"Failed to view transaction {ticket_id}: {ex}")
            raise TransactionValidationError(f"Failed to view transaction: {str(ex)}")


    @classmethod
    def edit_transaction(cls, session: Session, ticket_id: str, **updates) -> None:
        """
        Generic edit transaction (CRUD operation).
        
        Args:
            session: Database session
            ticket_id: Ticket ID to edit
            **updates: Fields to update
            
        Raises:
            TransactionNotFoundError: If transaction not found
            TransactionValidationError: If validation fails
        """
        try:
            transaction = session.query(cls).filter_by(ticket_id=ticket_id).first()
            if not transaction:
                LOGGER.error(f"Transaction {ticket_id} not found for editing")
                raise TransactionNotFoundError("Transaction not found")

            # Update fields
            for key, value in updates.items():
                if hasattr(transaction, key):
                    setattr(transaction, key, value)
                else:
                    LOGGER.warning(f"Unknown field '{key}' ignored during transaction update")

            session.commit()
            LOGGER.info(f"Transaction {ticket_id} updated with fields: {list(updates.keys())}")

        except Exception as ex:
            session.rollback()
            if isinstance(ex, TransactionNotFoundError):
                raise
            LOGGER.error(f"Failed to edit transaction {ticket_id}: {ex}")
            raise TransactionValidationError(f"Failed to edit transaction: {str(ex)}")


    @classmethod
    def close_transaction(cls, session: Session, ticket_id: str, 
                         closed_by: str, close_reason: str = "COMPLETED") -> None:
        """
        Generic close transaction (CRUD operation).
        
        Args:
            session: Database session
            ticket_id: Ticket ID to close
            closed_by: User ID who closed the transaction
            close_reason: Reason for closure
            
        Raises:
            TransactionNotFoundError: If transaction not found
            TransactionValidationError: If validation fails
        """
        try:
            transaction = session.query(cls).filter_by(ticket_id=ticket_id).first()
            if not transaction:
                LOGGER.error(f"Transaction {ticket_id} not found for closing")
                raise TransactionNotFoundError("Transaction not found")

            # Close transaction
            transaction.status = 'CLOSED'
            transaction.ticket_closed_date = utc_now()
            transaction.remarks = f"{transaction.remarks or ''} [CLOSED: {close_reason}]"

            session.commit()
            LOGGER.info(f"Transaction {ticket_id} closed by {closed_by} with reason: {close_reason}")

        except Exception as ex:
            session.rollback()
            if isinstance(ex, TransactionNotFoundError):
                raise
            LOGGER.error(f"Failed to close transaction {ticket_id}: {ex}")
            raise TransactionValidationError(f"Failed to close transaction: {str(ex)}")
