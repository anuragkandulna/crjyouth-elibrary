from sqlalchemy import String, Boolean, select, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from models.base import Base
from utils.my_logger import CustomLogger
from constants.config import LOG_LEVEL
from constants.constants import APP_LOG_FILE
from models.exceptions import LanguageNotFoundError


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=APP_LOG_FILE).get_logger()


class Language(Base):
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    language: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    books = relationship("Book", back_populates="book_language")


    @classmethod
    def create_language(cls, session: Session, language: str) -> "Language":
        """
        Create a new language. If it exists but is inactive, reactivate it.
        """
        stmt = select(cls).where(cls.language == language)
        existing = session.execute(stmt).scalar_one_or_none()

        if existing:
            if not existing.is_active:
                existing.is_active = True
                session.commit()
            return existing

        new_language = cls(language=language)
        session.add(new_language)
        session.commit()
        LOGGER.info(f"Language {new_language} created successfully.")
        return new_language


    @classmethod
    def delete_language(cls, session: Session, language: str) -> None:
        """
        Soft delete a language by setting is_active to False.
        """
        stmt = select(cls).where(cls.language == language, cls.is_active.is_(True))
        existing = session.execute(stmt).scalar_one_or_none()

        if not existing:
            LOGGER.error(f"Language {language} not found.")
            raise LanguageNotFoundError(f"Language {language} not found.")

        existing.is_active = False
        session.commit()
        LOGGER.info(f"Language {language} deleted successfully.")


    def __repr__(self) -> str:
        return f"<Language(language='{self.language}', active={self.is_active})>"
