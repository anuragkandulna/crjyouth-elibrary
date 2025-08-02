from sqlalchemy import String, Boolean, select, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from models.base import Base
from utils.my_logger import CustomLogger
from constants.config import LOG_LEVEL
from constants.constants import OPS_LOG_FILE
from models.exceptions import BookCategoryNotFoundError


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


class BookCategory(Base):
    __tablename__ = "book_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    books = relationship("Book", back_populates="categories")


    @classmethod
    def create_category(cls, session: Session, name: str, description: str) -> "BookCategory":
        """
        Create a new book category. If it exists but is inactive, reactivate it.
        """
        stmt = select(cls).where(cls.name == name)
        existing = session.execute(stmt).scalar_one_or_none()

        if existing:
            if not existing.is_active:
                existing.is_active = True
                existing.description = description
                session.commit()
            return existing

        new_category = cls(name=name, description=description)
        session.add(new_category)
        session.commit()
        LOGGER.info(f"Book category {new_category} created successfully.")
        return new_category


    @classmethod
    def delete_category(cls, session: Session, name: str) -> None:
        """
        Soft delete a book category by setting is_active to False.
        """
        stmt = select(cls).where(cls.name == name, cls.is_active.is_(True))
        category = session.execute(stmt).scalar_one_or_none()

        if not category:
            LOGGER.error(f"Book category '{name}' not found.")
            raise BookCategoryNotFoundError(f"Book category '{name}' not found.")

        category.is_active = False
        session.commit()
        LOGGER.info(f"Book category '{name}' deleted successfully.")


    def __repr__(self) -> str:
        return f"<BookCategory(name='{self.name}', active={self.is_active})>"
