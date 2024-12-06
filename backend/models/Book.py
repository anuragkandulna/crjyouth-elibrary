from sqlalchemy import String, Integer, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from datetime import datetime
import uuid
from constants.books import LANGUAGES, BOOK_TYPE
from models.base import Base

class Book(Base):
    __tablename__ = 'books'

    book_id: Mapped[str] = mapped_column(String(8), primary_key=True, default=lambda: str(uuid.uuid4())[:8])
    book_number: Mapped[int] = mapped_column(nullable=False)
    isbn: Mapped[int] = mapped_column(unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    first_publication_year: Mapped[int] = mapped_column(nullable=False)
    latest_publication_year: Mapped[int] = mapped_column(nullable=False)
    language: Mapped[str] = mapped_column(String(30), nullable=False)
    is_restricted: Mapped[bool] = mapped_column(Boolean, default=False)

    def __init__(self, session: Session, isbn: int, title: str, author: str, type: str, language: str,
                 first_publication_year: int = None, latest_publication_year: int = None,
                 is_restricted: bool = False):

        now = datetime.now().year
        self.book_id = str(uuid.uuid4())[:8]
        self.isbn = isbn
        self.title = title
        self.author = author
        self.type = type if type in BOOK_TYPE else "Other"
        self.language = language if language in LANGUAGES else "Unknown"
        self.first_publication_year = first_publication_year or now
        self.latest_publication_year = latest_publication_year or now
        self.is_restricted = is_restricted

        # Generate book_number serially per author
        self.book_number = self.get_next_book_number(session)

    def get_next_book_number(self, session: Session) -> int:
        max_number = session.query(func.max(Book.book_number)).filter_by(author=self.author).scalar()
        return (max_number or 0) + 1

    def get_details(self) -> dict:
        return {
            "Book Number": f"{self.book_number:03}",
            "ISBN": self.isbn,
            "Title": self.title,
            "Author": self.author,
            "Type": self.type,
            "First Publication Year": self.first_publication_year,
            "Latest Publication Year": self.latest_publication_year,
            "Language": self.language,
            "Restricted": self.is_restricted
        }
