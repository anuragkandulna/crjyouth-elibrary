from sqlalchemy import String, Boolean, select, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from models.base import Base
from utils.my_logger import CustomLogger
from constants.config import LOG_LEVEL
from constants.constants import APP_LOG_FILE
from models.exceptions import GenreNotFoundError


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=APP_LOG_FILE).get_logger()


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    books = relationship("Book", back_populates="genres")


    @classmethod
    def create_genre(cls, session: Session, name: str, description: str) -> "Genre":
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
        LOGGER.info(f"Genre {new_category} created successfully.")
        return new_category


    @classmethod
    def delete_genre(cls, session: Session, name: str) -> None:
        """
        Soft delete a book category by setting is_active to False.
        """
        stmt = select(cls).where(cls.name == name, cls.is_active.is_(True))
        category = session.execute(stmt).scalar_one_or_none()

        if not category:
            LOGGER.error(f"Genre '{name}' not found.")
            raise GenreNotFoundError(f"Genre '{name}' not found.")

        category.is_active = False
        session.commit()
        LOGGER.info(f"Genre '{name}' deleted successfully.")


    def __repr__(self) -> str:
        return f"<Genre(name='{self.name}', active={self.is_active})>"
