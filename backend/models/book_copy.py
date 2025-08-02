from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, Float, func, select
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional
from models.base import Base
from utils.timezone_utils import utc_now
from models.book import Book
from models.library_office import LibraryOffice
from utils.my_logger import CustomLogger
from constants.constants import OPS_LOG_FILE
from constants.config import LOG_LEVEL
from models.exceptions import DuplicateBookCopyError, BookCopyNotFound, BookNotFoundError, LibraryOfficeNotFound


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


class BookCopy(Base):
    __tablename__ = 'book_copies'

    copy_uuid: Mapped[str] = mapped_column(String(36), unique=True, default=lambda: str(uuid4()))
    copy_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    book_id: Mapped[str] = mapped_column(ForeignKey('books.book_id'), nullable=False, index=True)
    branch_code: Mapped[str] = mapped_column(ForeignKey('library_offices.office_code'), nullable=False, index=True)
    copy_number: Mapped[int] = mapped_column(nullable=False)
    current_publication_year: Mapped[int] = mapped_column(Integer, nullable=False)
    contributer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    added_on: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_now)
    copy_difficulty: Mapped[str] = mapped_column(ForeignKey("subject_difficulty_tiers.tier"), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    book = relationship(
        "Book",
        back_populates="copies",
        foreign_keys=[book_id],
        primaryjoin="Book.book_id == BookCopy.book_id"
    )

    branch = relationship(
        "LibraryOffice",
        backref="book_copies",
        foreign_keys=[branch_code],
        primaryjoin="LibraryOffice.office_code == BookCopy.branch_code"
    )


    @classmethod
    def get_next_copy_number(cls, session: Session, book_id: str) -> int:
        """
        Return next copy number of a book.
        """
        stmt = select(func.max(cls.copy_number)).where(cls.book_id == book_id)
        result = session.execute(stmt).scalar_one_or_none()
        return (result or 0) + 1


    @classmethod
    def generate_copy_id(cls, branch_code: str, book_id: str, copy_number: int) -> str:
        """
        Generate unique copy id of a book: LOC01-BH-001-0001
        """
        return f"{branch_code}-{book_id}-{copy_number:04}"


    @classmethod
    def create_copy(
        cls, session: Session,
        book_id: str, branch_code: str,
        current_publication_year: int,
        contributer: Optional[str] = None, 
        copy_difficulty: int = -1
    ) -> "BookCopy":
        """
        Create a book copy in database.
        """
        # Validate book_id
        stmt = select(Book).where(Book.book_id == book_id)
        book = session.execute(stmt).scalar_one_or_none()
        if not book:
            raise BookNotFoundError(f"Invalid book_id '{book_id}'")

        # Validate branch_code
        stmt = select(LibraryOffice).where(LibraryOffice.office_code == branch_code)
        branch = session.execute(stmt).scalar_one_or_none()
        if not branch:
            raise LibraryOfficeNotFound(f"Invalid branch_code '{branch_code}'")

        copy_number = cls.get_next_copy_number(session, book_id)
        copy_id = cls.generate_copy_id(branch_code.upper(), book_id, copy_number)
        book_difficulty = book.base_difficulty
        new_copy_difficulty = book_difficulty if copy_difficulty <= 0 else copy_difficulty

        # Check if copy already exists
        stmt = select(cls).where(cls.copy_id == copy_id)
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            LOGGER.error(f"Book Copy already exists with id: {existing.copy_id}")
            raise DuplicateBookCopyError(f"Book Copy already exists with id: {existing.copy_id}")

        new_copy = cls(
            copy_id=copy_id,
            book_id=book_id,
            branch_code=branch_code.upper(),
            copy_number=copy_number,
            current_publication_year=current_publication_year,
            contributer=contributer,
            is_available=True,
            copy_difficulty=new_copy_difficulty,
            added_on=datetime.now(timezone.utc).date()
        )
        session.add(new_copy)
        session.commit()
        LOGGER.info(f"BookCopy '{new_copy.copy_id}' added successfully.")
        return new_copy


    def mark_as_borrowed(self, session: Session):
        """
        Mark book copy as borrowed.
        """
        if not self.is_available:
            raise ValueError(f"BookCopy '{self.copy_id}' is already borrowed.")
        self.is_available = False
        session.commit()
        LOGGER.info(f"BookCopy '{self.copy_id}' marked as borrowed.")


    def mark_as_returned(self, session: Session):
        """
        Mark book copy as returned.
        """
        self.is_available = True
        session.commit()
        LOGGER.info(f"BookCopy '{self.copy_id}' marked as returned.")


    def __repr__(self) -> str:
        return f"<BookCopy(title='{self.book.title}', book_id='{self.book_id}', copy_id='{self.copy_id}')>"


    @staticmethod
    def view_copy(session: Session, copy_id: str) -> dict:
        """
        View book copy details.
        """
        stmt = select(BookCopy).where(BookCopy.copy_id == copy_id)
        copy = session.execute(stmt).scalar_one_or_none()
        if not copy:
            raise BookCopyNotFound("Book copy not found.")

        return {
            "Book Title": copy.book.title,
            "Book Author": copy.book.author,
            "Book ISBN": copy.book.isbn,
            "Book ID": copy.book_id,
            "Copy ID": copy.copy_id,
            "Branch Code": copy.branch_code,
            "Copy Number": copy.copy_number,
            "Available": copy.is_available,
            "Contributed By": copy.contributer,
            "Subject Difficulty": copy.copy_difficulty,
            "Added On": copy.added_on.isoformat(),
            "Current Publication Year": copy.current_publication_year
        }


    @staticmethod
    def edit_copy(session: Session, copy_id: str, **kwargs) -> None:
        """
        Edit book copy details.
        """
        stmt = select(BookCopy).where(BookCopy.copy_id == copy_id)
        copy = session.execute(stmt).scalar_one_or_none()
        if not copy:
            raise BookCopyNotFound("Book copy not found.")

        for key, value in kwargs.items():
            if hasattr(copy, key):
                setattr(copy, key, value)

        session.commit()
        LOGGER.info(f"Book Copy '{copy.copy_id}' - {kwargs.keys()} updated successfully.")


    @staticmethod
    def delete_copy(session: Session, copy_id: str) -> None:
        """
        Delete a book copy.
        """
        stmt = select(BookCopy).where(BookCopy.copy_id == copy_id)
        copy = session.execute(stmt).scalar_one_or_none()
        if not copy:
            raise BookCopyNotFound("Book copy not found.")

        session.delete(copy)
        session.commit()
        LOGGER.info(f"Book Copy '{copy.copy_id}' deleted successfully.")
