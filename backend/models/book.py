from sqlalchemy import String, Integer, ForeignKey, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from uuid import uuid4
from typing import Optional
from constants.constants import APP_LOG_FILE
from models.base import Base
from utils.my_logger import CustomLogger
from constants.config import LOG_LEVEL
from models.exceptions import DuplicateBookError, BookNotFoundError

LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=APP_LOG_FILE).get_logger()


class Book(Base):
    __tablename__ = 'books'

    book_uuid: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    book_id: Mapped[str] = mapped_column(String(5), unique=True, nullable=False, index=True)
    book_number: Mapped[int] = mapped_column(nullable=False)
    isbn: Mapped[str] = mapped_column(String(13), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    author_code: Mapped[int] = mapped_column(ForeignKey("authors.code"), nullable=False)
    genre: Mapped[str] = mapped_column(ForeignKey("genres.name"), nullable=False)
    language: Mapped[str] = mapped_column(ForeignKey("languages.language"), nullable=False)

    author = relationship("Author", back_populates="books")
    copies = relationship("BookCopy", back_populates="book", cascade="all, delete")
    genres = relationship("Genre", back_populates="books")
    book_language = relationship("Language", back_populates="books")


    @classmethod
    def get_next_book_number(cls, session: Session, author_code: int) -> int:
        stmt = select(func.max(cls.book_number)).where(cls.author_code == author_code)
        max_number = session.execute(stmt).scalar_one_or_none()
        return (max_number or 0) + 1


    @classmethod
    def generate_book_id(cls, author_code: int, book_number: int) -> str:
        return f"{author_code:02}{book_number:03}"  


    @classmethod
    def create_book(
        cls, session: Session,
        isbn: str, title: str,
        author_code: int,
        genre: str, language: str
    ) -> "Book":
        book_number = cls.get_next_book_number(session, author_code)
        book_id = cls.generate_book_id(author_code, book_number)

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
            genre=genre,
            language=language
        )

        session.add(new_book)
        session.commit()
        LOGGER.info(f"New Book {new_book} created successfully.")
        return new_book


    def __repr__(self) -> str:
        return f"<Book(book_id='{self.book_id}', ISBN='{self.isbn}', title='{self.title}')>"


    @staticmethod
    def get_details(session: Session, book_id: str) -> dict:
        stmt = select(Book).where(Book.book_id == book_id)
        book = session.execute(stmt).scalar_one_or_none()
        if not book:
            raise BookNotFoundError("Book not found.")

        return {
            "Book UUID": book.book_uuid,
            "Book ID": book.book_id,
            "Book Number": f"{book.book_number:03}",
            "ISBN": book.isbn,
            "Title": book.title,
            "Language": book.language,
            "Genre": book.genre,
            "Author Code": book.author_code
        }


    @staticmethod
    def edit_book(session: Session, book_id: str, **kwargs) -> None:
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
        stmt = select(Book).where(Book.book_id == book_id)
        book = session.execute(stmt).scalar_one_or_none()
        if not book:
            raise BookNotFoundError("Book not found.")

        session.delete(book)
        session.commit()
        LOGGER.info(f"Book '{book.title}' deleted successfully.")
