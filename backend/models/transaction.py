from sqlalchemy import String, Integer, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from datetime import datetime
from uuid import uuid4
import random
from typing import Optional
from constants.constants import APP_LOG_FILE
from models.base import Base
from utils.timezone_utils import utc_now
from models.user import User
from utils.my_logger import CustomLogger
from constants.config import LOG_LEVEL
from models.exceptions import (
    DuplicateTransactionError, TransactionNotFoundError, TransactionValidationError
)

LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=APP_LOG_FILE).get_logger()


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_uuid: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    ticket_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    office_code: Mapped[int] = mapped_column(Integer, ForeignKey('offices.code'), nullable=False)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id'), nullable=False)
    librarian_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.user_id'), nullable=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    copy_id: Mapped[Optional[str]] = mapped_column(ForeignKey('book_copies.copy_id'), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    particulars: Mapped[str] = mapped_column(String(255), nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ticket_updated_date: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    book_borrow_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    book_due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    book_return_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fine_incurred: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    customer = relationship("User", foreign_keys=[customer_id], backref="transactions_as_customer")
    librarian = relationship("User", foreign_keys=[librarian_id], backref="transactions_as_librarian")
    book_copy = relationship("BookCopy", foreign_keys=[copy_id], backref="transactions")


    def __repr__(self) -> str:
        return f"<Transaction(ticket_id={self.ticket_id}, status={self.status})>"


    @staticmethod
    def generate_ticket_id(seed: Optional[int] = None) -> int:
        if seed and 1000 <= seed <= 999999:
            return seed
        return random.randint(100000, 999999)


    @classmethod
    def create_transaction(cls, session: Session, customer: User, copy_id: str,
                           particulars: str, ticket_seed: Optional[int] = None) -> "Transaction":
        try:
            if not customer or not customer.user_id:
                raise TransactionValidationError("Invalid customer")

            office_code = customer.registered_at_office
            ticket_id = cls.generate_ticket_id(ticket_seed)

            # Check uniqueness
            existing = session.query(cls).filter_by(ticket_id=ticket_id).first()
            if existing:
                raise DuplicateTransactionError(f"Ticket ID {ticket_id} already exists")

            transaction = cls(
                ticket_id=ticket_id,
                office_code=office_code,
                customer_id=customer.user_id,
                customer_name=f"{customer.first_name} {customer.last_name}",
                copy_id=copy_id,
                status="PENDING",
                particulars=particulars
            )

            session.add(transaction)
            session.commit()
            LOGGER.info(f"Transaction {ticket_id} created by customer {customer.user_id}")
            return transaction

        except Exception as ex:
            session.rollback()
            LOGGER.error(f"Failed to create ticket: {ex}")
            raise TransactionValidationError("Could not create transaction")


    @classmethod
    def claim_transaction(cls, session: Session, ticket_id: int, librarian_id: int, remarks: Optional[str] = None) -> None:
        transaction = session.query(cls).filter_by(ticket_id=ticket_id).first()
        if not transaction:
            raise TransactionNotFoundError("Transaction not found")

        transaction.librarian_id = librarian_id
        transaction.status = "CLAIMED"
        if remarks:
            transaction.remarks = remarks

        session.commit()
        LOGGER.info(f"Transaction {ticket_id} claimed by librarian {librarian_id}")


    @classmethod
    def view_transaction(cls, session: Session, ticket_id: int) -> dict:
        transaction = session.query(cls).filter_by(ticket_id=ticket_id).first()
        if not transaction:
            raise TransactionNotFoundError("Transaction not found")

        return {
            "ticket_id": transaction.ticket_id,
            "transaction_uuid": transaction.transaction_uuid,
            "office_code": transaction.office_code,
            "customer_id": transaction.customer_id,
            "customer_name": transaction.customer_name,
            "librarian_id": transaction.librarian_id,
            "copy_id": transaction.copy_id,
            "status": transaction.status,
            "particulars": transaction.particulars,
            "remarks": transaction.remarks,
            "updated": transaction.ticket_updated_date.isoformat(),
            "borrowed": transaction.book_borrow_date.isoformat() if transaction.book_borrow_date else None,
            "due": transaction.book_due_date.isoformat() if transaction.book_due_date else None,
            "returned": transaction.book_return_date.isoformat() if transaction.book_return_date else None,
            "fine": transaction.fine_incurred
        }


    @classmethod
    def edit_transaction(cls, session: Session, ticket_id: int, **updates) -> None:
        transaction = session.query(cls).filter_by(ticket_id=ticket_id).first()
        if not transaction:
            raise TransactionNotFoundError("Transaction not found")

        for key, value in updates.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)

        session.commit()
        LOGGER.info(f"Transaction {ticket_id} updated with: {list(updates.keys())}")


    @classmethod
    def close_transaction(cls, session: Session, ticket_id: int, reason: str = "COMPLETED") -> None:
        transaction = session.query(cls).filter_by(ticket_id=ticket_id).first()
        if not transaction:
            raise TransactionNotFoundError("Transaction not found")

        transaction.status = "CLOSED"
        transaction.remarks = (transaction.remarks or "") + f" [CLOSED: {reason}]"
        session.commit()
        LOGGER.info(f"Transaction {ticket_id} closed. Reason: {reason}")
