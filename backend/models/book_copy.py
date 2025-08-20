from sqlalchemy import String, Boolean, ForeignKey, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from uuid import uuid4
from models.base import Base
from utils.my_logger import CustomLogger
from constants.constants import APP_LOG_FILE
from constants.config import LOG_LEVEL
from models.exceptions import DuplicateBookCopyError, BookCopyNotFound, BookNotFoundError, OfficeNotFoundError
from models.book import Book
from models.office import Office

LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=APP_LOG_FILE).get_logger()


class BookCopy(Base):
    __tablename__ = 'book_copies'

    copy_uuid: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    copy_id: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    book_id: Mapped[str] = mapped_column(ForeignKey('books.book_id'), nullable=False)
    branch_code: Mapped[int] = mapped_column(ForeignKey('offices.code'), nullable=False)
    copy_number: Mapped[int] = mapped_column(nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    book = relationship("Book", back_populates="copies")
    branch = relationship("Office", backref="book_copies")


    @classmethod
    def get_next_copy_number(cls, session: Session, book_id: str) -> int:
        stmt = select(func.max(cls.copy_number)).where(cls.book_id == book_id)
        result = session.execute(stmt).scalar_one_or_none()
        return (result or 0) + 1


    @classmethod
    def generate_copy_id(cls, branch_code: int, book_id: str, copy_number: int) -> str:
        return f"{branch_code:02}{book_id}{copy_number:03}"


    @classmethod
    def create_copy(
        cls, session: Session,
        book_id: str, branch_code: int
    ) -> "BookCopy":
        stmt = select(Book).where(Book.book_id == book_id)
        book = session.execute(stmt).scalar_one_or_none()
        if not book:
            raise BookNotFoundError(f"Invalid book_id '{book_id}'")

        stmt = select(Office).where(Office.code == branch_code)
        branch = session.execute(stmt).scalar_one_or_none()
        if not branch:
            raise OfficeNotFoundError(f"Invalid branch_code '{branch_code}'")

        copy_number = cls.get_next_copy_number(session, book_id)
        copy_id = cls.generate_copy_id(branch_code, book_id, copy_number)

        stmt = select(cls).where(cls.copy_id == copy_id)
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            LOGGER.error(f"Book Copy already exists with id: {existing.copy_id}")
            raise DuplicateBookCopyError(f"Book Copy already exists with id: {existing.copy_id}")

        new_copy = cls(
            copy_id=copy_id,
            book_id=book_id,
            branch_code=branch_code,
            copy_number=copy_number,
            is_available=True
        )
        session.add(new_copy)
        session.commit()
        LOGGER.info(f"BookCopy '{new_copy.copy_id}' added successfully.")
        return new_copy


    def mark_as_borrowed(self, session: Session):
        if not self.is_available:
            raise ValueError(f"BookCopy '{self.copy_id}' is already borrowed.")
        self.is_available = False
        session.commit()
        LOGGER.info(f"BookCopy '{self.copy_id}' marked as borrowed.")


    def mark_as_returned(self, session: Session):
        self.is_available = True
        session.commit()
        LOGGER.info(f"BookCopy '{self.copy_id}' marked as returned.")


    def __repr__(self) -> str:
        return f"<BookCopy(book_id='{self.book_id}', copy_id='{self.copy_id}')>"


    @staticmethod
    def view_copy(session: Session, copy_id: str) -> dict:
        stmt = select(BookCopy).where(BookCopy.copy_id == copy_id)
        copy = session.execute(stmt).scalar_one_or_none()
        if not copy:
            raise BookCopyNotFound("Book copy not found.")

        return {
            "Book Title": copy.book.title,
            "Book ID": copy.book_id,
            "Copy ID": copy.copy_id,
            "Branch Code": copy.branch_code,
            "Copy Number": copy.copy_number,
            "Available": copy.is_available
        }


    @staticmethod
    def edit_copy(session: Session, copy_id: str, **kwargs) -> None:
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
        stmt = select(BookCopy).where(BookCopy.copy_id == copy_id)
        copy = session.execute(stmt).scalar_one_or_none()
        if not copy:
            raise BookCopyNotFound("Book copy not found.")

        session.delete(copy)
        session.commit()
        LOGGER.info(f"Book Copy '{copy.copy_id}' deleted successfully.")
