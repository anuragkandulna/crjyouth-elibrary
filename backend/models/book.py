from sqlalchemy import String, Integer, Boolean, JSON, Float, ForeignKey, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from uuid import uuid4
from typing import Optional
from constants.constants import OPS_LOG_FILE
from models.base import Base
from utils.my_logger import CustomLogger
from constants.config import LOG_LEVEL
from models.exceptions import DuplicateBookError, BookNotFoundError


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


class Book(Base):
    __tablename__ = 'books'

    book_uuid: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    book_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    book_number: Mapped[int] = mapped_column(nullable=False)
    isbn: Mapped[str] = mapped_column(String(13), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    author_code: Mapped[Optional[str]] = mapped_column(ForeignKey("authors.code"), nullable=True, index=True)
    publisher_code: Mapped[str] = mapped_column(ForeignKey("publishers.code"), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # contents: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # price: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(ForeignKey("book_categories.name"), nullable=False)
    language: Mapped[str] = mapped_column(ForeignKey("book_languages.language"), nullable=False)
    # base_difficulty: Mapped[int] = mapped_column(ForeignKey("subject_difficulty_tiers.tier"), nullable=False)
    publication_year: Mapped[int] = mapped_column(Integer, nullable=True)
    # is_restricted_book: Mapped[bool] = mapped_column(Boolean, default=False)

    author = relationship("Author", back_populates="books")
    publisher = relationship("Publisher", back_populates="books")
    copies = relationship("BookCopy", back_populates="book", cascade="all, delete")
    # subject_difficulty = relationship("SubjectDifficultyTier", back_populates="books")
    categories = relationship("BookCategory", back_populates="books")
    book_language = relationship("BookLanguage", back_populates="books")


    @classmethod
    def get_next_book_number(cls, session: Session, author_code: Optional[str], publisher_code: str) -> int:
        """
        Get the next book number for a given author or publisher.
        """
        if author_code:
            stmt = select(func.max(cls.book_number)).where(cls.author_code == author_code)
            max_number = session.execute(stmt).scalar_one_or_none()
        else:
            stmt = select(func.max(cls.book_number)).where(cls.publisher_code == publisher_code)
            max_number = session.execute(stmt).scalar_one_or_none()
        return (max_number or 0) + 1


    @classmethod
    def generate_book_id(cls, code: str, book_number: int) -> str:
        """
        Generate a unique human-readable book ID.
        """
        return f"{code}-{book_number:03}"


    @classmethod
    def create_book(
        cls, session: Session,
        isbn: str, title: str,
        author_code: Optional[str], publisher_code: str,
        description: Optional[str], contents: Optional[dict], price: float,
        category: str, language: str, base_difficulty: int, first_publication_year: int,
        is_restricted_book: bool = False
    ) -> "Book":
        """
        Create a new book entry in the database after validation.
        """
        book_number = cls.get_next_book_number(session, author_code, publisher_code)
        id_prefix = author_code if author_code else publisher_code
        book_id = cls.generate_book_id(id_prefix, book_number)

        # Check if author already exists
        stmt = select(cls).where((cls.isbn == isbn) | (cls.book_id == book_id))
        existing = session.execute(stmt).scalar_one_or_none()

        if existing:
            LOGGER.error(f"Skipped book creation: Book with ISBN '{isbn}' or ID '{book_id}' already exists.")
            raise DuplicateBookError(f"Book with ISBN or Book id already exists: {existing.book_id}")

        new_book = cls(
            book_id=book_id,
            book_number=book_number,
            isbn=isbn,
            title=title,
            author_code=author_code,
            publisher_code=publisher_code,
            description=description,
            contents=contents,
            price=price,
            category=category,
            language=language,
            base_difficulty=base_difficulty,
            first_publication_year=first_publication_year,
            is_restricted_book=is_restricted_book
        )

        session.add(new_book)
        session.commit()
        LOGGER.info(f"New Book {new_book} created successfully.")
        return new_book


    def __repr__(self) -> str:
        return f"<Book(book_id='{self.book_id}', ISBN='{self.isbn}', title='{self.title}')>"


    @staticmethod
    def get_details(session: Session, book_id: str) -> dict:
        """
        Retrieve and return details of a book by its book_id.
        """
        stmt = select(Book).where(Book.book_id == book_id)
        book = session.execute(stmt).scalar_one_or_none()
        if not book:
            raise BookNotFoundError("Book not found.")

        return {
            "Book UUID": book.book_uuid,
            "Book ID": book.book_id,
            "Language": book.language,
            "Category": book.category,
            "Book Number": f"{book.book_number:03}",
            "ISBN": book.isbn,
            "Title": book.title,
            "Description": book.description,
            "Contents": book.contents,
            "Price": book.price,
            "Author Code": book.author_code,
            "Publisher Code": book.publisher_code,
            "Language": book.language,
            "Subject Difficulty": book.base_difficulty,
            "First Publication Year": book.first_publication_year,
            "Restricted": book.is_restricted_book
        }


    @staticmethod
    def edit_book(session: Session, book_id: str, **kwargs) -> None:
        """
        Edit book fields using keyword arguments.
        """
        stmt = select(Book).where(Book.book_id == book_id)
        book = session.execute(stmt).scalar_one_or_none()
        if not book:
            raise BookNotFoundError("Book not found.")

        for key, value in kwargs.items():
            if hasattr(book, key):
                setattr(book, key, value)

        session.commit()
        LOGGER.info(f"Book '{book.book_id}' - {kwargs.keys()} updated successfully.")


    @staticmethod
    def delete_book(session: Session, book_id: str) -> None:
        """
        Permanently delete a book by its book_id.
        """
        stmt = select(Book).where(Book.book_id == book_id)
        book = session.execute(stmt).scalar_one_or_none()
        if not book:
            raise BookNotFoundError("Book not found.")

        session.delete(book)
        session.commit()
        LOGGER.info(f"Book '{book.title}' deleted successfully.")
