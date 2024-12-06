from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from datetime import datetime, timezone
from models.base import Base

class BookCopy(Base):
    __tablename__ = 'book_copies'

    copy_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    book_id: Mapped[str] = mapped_column(ForeignKey('books.book_id'), nullable=False)
    branch_code: Mapped[str] = mapped_column(String(3), nullable=False)
    author_code: Mapped[str] = mapped_column(String(4), nullable=False)
    book_number: Mapped[int] = mapped_column(nullable=False)
    copy_number: Mapped[int] = mapped_column(nullable=False)
    donated_by: Mapped[str] = mapped_column(String(100), nullable=True)
    added_on: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    book = relationship("Book", backref="copies")

    def __init__(self, session: Session, book, branch_code: str,
                 donated_by: str = None, is_available: bool = True,
                 added_on: datetime = None):
        self.book_id = book.book_id
        self.branch_code = branch_code.upper()
        self.author_code = book.author[:4].upper()
        self.book_number = book.book_number
        self.donated_by = donated_by
        self.is_available = is_available
        self.added_on = added_on or datetime.now(timezone.utc)

        self.copy_number = self.get_next_copy_number(session)
        self.copy_id = self.generate_copy_id()

    def get_next_copy_number(self, session: Session) -> int:
        result = session.query(func.max(BookCopy.copy_number))\
            .filter_by(book_id=self.book_id).scalar()
        return (result or 0) + 1

    def generate_copy_id(self) -> str:
        return f"{self.branch_code}-{self.author_code}-{self.book_number:03}-{self.copy_number:04}"

    def mark_as_borrowed(self):
        if not self.is_available:
            raise Exception(f"BookCopy {self.copy_id} is already borrowed.")
        self.is_available = False

    def mark_as_returned(self):
        self.is_available = True
