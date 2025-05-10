from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from datetime import datetime, timezone
from models.base import Base
from models.book import Book
from models.library_office import LibraryOffice
from utils.my_logger import CustomLogger
from constants.constants import OPS_LOG_FILE
from constants.config import LOG_LEVEL


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


class BookCopy(Base):
    __tablename__ = 'book_copies'

    copy_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    book_id: Mapped[str] = mapped_column(ForeignKey('books.book_id'), nullable=False)
    branch_code: Mapped[str] = mapped_column(ForeignKey('library_offices.office_code'), nullable=False)
    copy_number: Mapped[int] = mapped_column(nullable=False)
    current_publication_year: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    donated_by: Mapped[str] = mapped_column(String(100), nullable=True)
    added_on: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
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
        result = session.query(func.max(cls.copy_number)).filter_by(book_id=book_id).scalar()
        return (result or 0) + 1


    @classmethod
    def generate_copy_id(cls, branch_code: str, book_id: str, copy_number: int) -> str:
        """
        Generate unique copy id of a book: LOC01-BH-001-0001
        """
        return f"{branch_code}-{book_id}-{copy_number:04}"


    @classmethod
    def create_copy(cls, session: Session,
                    book_id: str, branch_code: str,
                    price: float, current_publication_year: int,
                    donated_by: str = None, is_available: bool = True,
                    added_on: datetime = None) -> "BookCopy":
        """
        Create a book copy in database.
        """
        # Validate book_id
        book = session.query(Book).filter_by(book_id=book_id).first()
        if not book:
            raise ValueError(f"Invalid book_id '{book_id}'")

        # Validate branch_code
        branch = session.query(LibraryOffice).filter_by(office_code=branch_code).first()
        if not branch:
            raise ValueError(f"Invalid branch_code '{branch_code}'")

        copy_number = cls.get_next_copy_number(session, book_id)
        copy_id = cls.generate_copy_id(branch_code.upper(), book_id, copy_number)

        # Check if copy already exists
        existing = session.query(cls).filter_by(copy_id=copy_id).first()
        if existing:
            LOGGER.warning(f"Skipped copy creation: BookCopy with ID '{copy_id}' already exists.")
            return existing

        new_copy = cls(
            copy_id=copy_id,
            book_id=book_id,
            branch_code=branch_code.upper(),
            copy_number=copy_number,
            current_publication_year=current_publication_year,
            price=price,
            donated_by=donated_by,
            is_available=is_available,
            added_on=added_on or datetime.now(timezone.utc)
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
        return f"<BookCopy(copy_id='{self.copy_id}', book_id='{self.book_id}', branch_code='{self.branch_code}', copy_number='{self.copy_number}')>"


    @staticmethod
    def view_copy(session: Session, copy_id: str) -> dict:
        """
        View book copy details.
        """
        copy = session.query(BookCopy).filter_by(copy_id=copy_id).first()
        if not copy:
            raise ValueError("Book copy not found.")
        return {
            "Copy ID": copy.copy_id,
            "Book ID": copy.book_id,
            "Branch Code": copy.branch_code,
            "Copy Number": copy.copy_number,
            "Price": copy.price,
            "Available": copy.is_available,
            "Donated By": copy.donated_by,
            "Added On": copy.added_on.isoformat(),
            "Current Publication Year": copy.current_publication_year
        }


    @staticmethod
    def edit_copy(session: Session, copy_id: str, **kwargs) -> None:
        """
        Edit book copy details.
        """
        copy = session.query(BookCopy).filter_by(copy_id=copy_id).first()
        if not copy:
            raise ValueError("Book copy not found.")

        for key, value in kwargs.items():
            if hasattr(copy, key):
                setattr(copy, key, value)

        session.commit()
        LOGGER.info(f"BookCopy '{copy.copy_id}' updated successfully.")


    @staticmethod
    def delete_copy(session: Session, copy_id: str) -> None:
        """
        Delete a book copy.
        """
        copy = session.query(BookCopy).filter_by(copy_id=copy_id).first()
        if not copy:
            raise ValueError("Book copy not found.")

        session.delete(copy)
        session.commit()
        LOGGER.info(f"BookCopy '{copy.copy_id}' deleted successfully.")
