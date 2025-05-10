from sqlalchemy import String, Integer, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from datetime import datetime
import uuid
from typing import Optional
from constants.constants import LANGUAGES, BOOK_TYPE, OPS_LOG_FILE
from models.base import Base
from models.author import Author
from models.publisher import Publisher
from utils.my_logger import CustomLogger
from constants.config import LOG_LEVEL


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


class Book(Base):
    __tablename__ = 'books'

    book_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    book_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    book_number: Mapped[int] = mapped_column(nullable=False)
    isbn: Mapped[int] = mapped_column(unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    author_code: Mapped[Optional[str]] = mapped_column(ForeignKey("authors.code"), nullable=True)
    publisher_code: Mapped[str] = mapped_column(ForeignKey("publishers.code"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    language: Mapped[str] = mapped_column(String(30), nullable=False)
    first_publication_year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_restricted_book: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pastoral_book: Mapped[bool] = mapped_column(Boolean, default=False)

    author = relationship("Author", back_populates="books")
    publisher = relationship("Publisher", back_populates="books")
    copies = relationship("BookCopy", back_populates="book")


    @staticmethod
    def validate_type(book_type: str) -> str:
        """
        Validate a book type.
        """
        return book_type if book_type in BOOK_TYPE else "Other"


    @staticmethod
    def validate_language(language: str) -> str:
        """
        Validate a language.
        """
        return language if language in LANGUAGES else "Unknown"


    @classmethod
    def get_next_book_number(cls, session: Session, author_code: Optional[str], publisher_code: str) -> int:
        if author_code:
            max_number = session.query(func.max(cls.book_number)).filter_by(author_code=author_code).scalar()
        else:
            max_number = session.query(func.max(cls.book_number)).filter_by(publisher_code=publisher_code).scalar()
        return (max_number or 0) + 1


    @classmethod
    def generate_book_id(cls, code: str, book_number: int) -> str:
        """
        Generate a unique book id for a book.
        """
        return f"{code}-{book_number:03}"


    @classmethod
    def create_book(cls, session: Session,
                    isbn: int, title: str,
                    author_code: Optional[str], publisher_code: str,
                    type: str, language: str, first_publication_year: int = None,
                    is_restricted_book: bool = False, is_pastoral_book: bool = False) -> "Book":
        """
        Create a new book in database.
        """
        now = datetime.now().year
        book_number = cls.get_next_book_number(session, author_code, publisher_code)
        id_prefix = author_code if author_code else publisher_code
        book_id = cls.generate_book_id(id_prefix, book_number)

        # Check for duplicate ISBN or book_id
        existing = session.query(cls).filter(
            (cls.isbn == isbn) | (cls.book_id == book_id)
        ).first()
        if existing:
            LOGGER.warning(f"Skipped book creation: Book with ISBN '{isbn}' or ID '{book_id}' already exists.")
            return existing

        new_book = cls(
            book_uuid=str(uuid.uuid4()),
            book_id=book_id,
            book_number=book_number,
            isbn=isbn,
            title=title,
            author_code=author_code,
            publisher_code=publisher_code,
            type=cls.validate_type(type),
            language=cls.validate_language(language),
            first_publication_year=first_publication_year or now,
            is_restricted_book=is_restricted_book,
            is_pastoral_book=is_pastoral_book
        )
        session.add(new_book)
        session.commit()
        LOGGER.info(f"Book '{new_book.title}' added successfully with Book ID: {new_book.book_id}.")
        return new_book


    def __repr__(self) -> str:
        return f"<Book(book_id='{self.book_id}', title='{self.title}', author_code='{self.author_code}', publisher_code='{self.publisher_code}')>"


    @staticmethod
    def get_details(session: Session, book_id: str) -> dict:
        """
        Get details of a book.
        """
        book = session.query(Book).filter_by(book_id=book_id).first()
        if not book:
            raise ValueError("Book not found.")

        return {
            "Book UUID": book.book_uuid,
            "Book ID": book.book_id,
            "Language": book.language,
            "Book Number": f"{book.book_number:03}",
            "ISBN": book.isbn,
            "Title": book.title,
            "Author Code": book.author_code,
            "Publisher Code": book.publisher_code,
            "Type": book.type,
            "First Publication Year": book.first_publication_year,
            "Restricted": book.is_restricted_book,
            "Pastoral Book": book.is_pastoral_book
        }


    @staticmethod
    def edit_book(session: Session, book_id: str, **kwargs) -> None:
        """
        Edit book details.
        """
        book = session.query(Book).filter_by(book_id=book_id).first()
        if not book:
            raise ValueError("Book not found.")

        for key, value in kwargs.items():
            if key == 'language':
                setattr(book, key, Book.validate_language(value))
            elif key == 'type':
                setattr(book, key, Book.validate_type(value))
            elif hasattr(book, key):
                setattr(book, key, value)

        session.commit()
        LOGGER.info(f"Book '{book.title}' updated successfully.")


    @staticmethod
    def delete_book(session: Session, book_id: str) -> None:
        """
        Delete a book permanently from database.
        """
        book = session.query(Book).filter_by(book_id=book_id).first()
        if not book:
            raise ValueError("Book not found.")

        session.delete(book)
        session.commit()
        LOGGER.info(f"Book '{book.title}' deleted successfully.")
