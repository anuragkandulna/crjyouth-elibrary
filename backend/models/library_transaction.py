from sqlalchemy import String, Integer, Boolean, DateTime, Float, ForeignKey, BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from datetime import datetime, timedelta
import random
import uuid
from constants.constants import TOKEN_PRICES, DEFAULT_EXTENSION_FEE, DEFAULT_DAMAGE_FEE, EXTENSION_DAYS, OPS_LOG_FILE
from models.base import Base
from models.library_user import LibraryUser
from models.book_copy import BookCopy
from utils.my_logger import CustomLogger


LOGGER = CustomLogger(__name__, level=20, log_file=OPS_LOG_FILE).get_logger()


class LibraryTransaction(Base):
    __tablename__ = "library_transactions"

    transaction_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    ticket_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'), nullable=True)
    librarian_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'), nullable=False)
    copy_id: Mapped[str] = mapped_column(ForeignKey('book_copies.copy_id'), nullable=True)
    status: Mapped[str] = mapped_column(ForeignKey('status_codes.code'), nullable=False)
    particulars: Mapped[str] = mapped_column(String(255), nullable=False)
    token_type: Mapped[str] = mapped_column(String(5), nullable=False)  # Store 'S1' or 'S2'
    token_price: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    # updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=True)
    borrow_date: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    return_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    fine_incurred: Mapped[float] = mapped_column(Float, default=0.0)
    
    # is_returned: Mapped[bool] = mapped_column(Boolean, default=False)
    # is_extended: Mapped[bool] = mapped_column(Boolean, default=False)
    # is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    # is_d: Mapped[bool] = mapped_column(Boolean, default=False)

    customer = relationship("LibraryUser", backref="borrow_transactions")
    librarian = relationship("LibraryUser", backref="borrow_transactions")
    book_copy = relationship("BookCopy", backref="borrow_transactions")


    def __repr__(self) -> str:
        return f"<LibraryTransaction(transaction_id={self.transaction_id}, token_type={self.token_type}, approved={self.is_approved})>"


    @staticmethod
    def generate_transaction_id() -> int:
        return random.randint(10000000, 99999999)


    @classmethod
    def create_new_transaction(cls, session: Session, user: LibraryUser, token_type: str) -> "LibraryTransaction":
        """
        Create a new transaction.
        """
        if token_type not in TOKEN_PRICES:
            LOGGER.error(f"Invalid token type '{token_type}' by user {user.user_id}.")
            raise ValueError(f"Invalid token type. Allowed: {list(TOKEN_PRICES.keys())}")

        active_borrows = session.query(cls).filter_by(user_id=user.user_id, is_returned=False, is_approved=True).count()
        if active_borrows >= user.membership.borrowing_limit:
            LOGGER.error(f"Borrowing limit reached for user {user.user_id}.")
            raise ValueError("Borrowing limit reached.")

        token_price = TOKEN_PRICES[token_type]

        transaction = cls(
            transaction_uuid=str(uuid.uuid4()),
            transaction_id=cls.generate_transaction_id(),
            user_id=user.user_id,
            token_type=token_type,
            token_price=token_price,
            is_approved=False
        )

        session.add(transaction)
        session.commit()
        LOGGER.info(f"Transaction {transaction.transaction_id} created with token '{token_type}' ({token_price}).")
        return transaction


    @classmethod
    def approve_transaction(cls, session: Session, transaction_id: int, copy: BookCopy, new_token_type: str = None) -> None:
        """
        Approve a transaction.
        """
        transaction = session.query(cls).filter_by(transaction_id=transaction_id, is_approved=False).first()
        if not transaction:
            LOGGER.error(f"Transaction {transaction_id} not found for approval.")
            raise ValueError("Transaction not found or already approved.")

        if new_token_type:
            if new_token_type not in TOKEN_PRICES:
                LOGGER.error(f"Invalid new token type '{new_token_type}' during approval.")
                raise ValueError(f"Invalid token type. Allowed: {list(TOKEN_PRICES.keys())}")
            transaction.token_type = new_token_type
            transaction.token_price = TOKEN_PRICES[new_token_type]
            LOGGER.info(f"Token type changed to '{new_token_type}' for transaction {transaction_id}.")

        transaction.copy_id = copy.copy_id
        transaction.borrow_date = datetime.now()
        transaction.due_date = transaction.borrow_date + timedelta(days=EXTENSION_DAYS)
        transaction.is_approved = True

        copy.mark_as_borrowed()

        session.commit()
        LOGGER.info(f"Transaction {transaction_id} approved. BookCopy {copy.copy_id} assigned.")


    @classmethod
    def return_book(cls, session: Session, transaction_id: int, damage=False, lost=False, admin_override=False) -> None:
        """
        Return borrowed book and claculate fine.
        """
        transaction = session.query(cls).filter_by(transaction_id=transaction_id, is_returned=False, is_approved=True).first()
        if not transaction:
            raise ValueError("Transaction not found.")

        user = transaction.user
        book_copy = transaction.book_copy
        today = datetime.now()
        fine = 0.0

        if today > transaction.due_date:
            fine += 10.0 * (today - transaction.due_date).days

        if damage:
            fine += min(book_copy.price, DEFAULT_DAMAGE_FEE)

        if lost:
            fine += book_copy.price

        if admin_override and (user.is_pastor or user.is_founder):
            fine = 0.0

        transaction.return_date = today
        transaction.fine_incurred = fine
        transaction.is_returned = True

        book_copy.mark_as_returned()

        session.commit()
        LOGGER.info(f"Book returned for transaction {transaction_id}. Fine: {fine}.")


    @classmethod
    def extend_due_date(cls, session: Session, transaction_id: int) -> None:
        """
        Extend a book once.
        """
        transaction = session.query(cls).filter_by(transaction_id=transaction_id, is_returned=False, is_approved=True).first()
        if not transaction:
            raise ValueError("Transaction not found.")

        if transaction.is_extended:
            raise ValueError("Borrow already extended once.")

        transaction.due_date += timedelta(days=EXTENSION_DAYS)
        transaction.token_price += DEFAULT_EXTENSION_FEE
        transaction.is_extended = True

        session.commit()
        LOGGER.info(f"Due date extended for transaction {transaction_id}.")


    @classmethod
    def view_transaction(cls, session: Session, transaction_id: int) -> dict:
        """
        View transaction details.
        """
        transaction = session.query(cls).filter_by(transaction_id=transaction_id).first()
        if not transaction:
            raise ValueError("Transaction not found.")

        return {
            "Borrow ID": transaction.transaction_id,
            "User ID": transaction.user_id,
            "Copy ID": transaction.copy_id,
            "Token Type": transaction.token_type,
            "Token Price": transaction.token_price,
            "Borrowed On": transaction.borrow_date.isoformat() if transaction.borrow_date else None,
            "Due Date": transaction.due_date.isoformat() if transaction.due_date else None,
            "Returned On": transaction.return_date.isoformat() if transaction.return_date else None,
            "Fine Incurred": transaction.fine_incurred,
            "Is Returned": transaction.is_returned,
            "Is Approved": transaction.is_approved,
            "Is Extended": transaction.is_extended
        }
