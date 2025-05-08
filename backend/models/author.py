from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy import String, Integer
from models.base import Base
from utils.my_logger import CustomLogger
from constants.constants import OPS_LOG_FILE


LOGGER = CustomLogger(__name__, level=20, log_file=OPS_LOG_FILE).get_logger()


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    books = relationship("Book", back_populates="author")


    def __repr__(self) -> str:
        return f"<Author(id='{self.id}', code='{self.code}', name='{self.name}')>"


    @classmethod
    def create_author(cls, session: Session, code: str, name: str) -> "Author":
        """
        Create a new author into database.
        """
        # Check if author already exists        
        existing = session.query(cls).filter(
            (cls.code == code) | (cls.name == name)
        ).first()
        if existing:
            LOGGER.warning(f"Skipped author creation: Author with name '{name}' or code '{code}' already exists.")
            return existing
        
        new_author = cls(
            code=code,
            name=name
        )
        session.add(new_author)
        session.commit()
        LOGGER.info(f"Author added: '{code}' - '{name}' added successfully.")
        return new_author


    @staticmethod
    def delete_author(session: Session, code: str) -> None:
        """
        Delete an author permanently.
        """
        author = session.query(Author).filter_by(code=code).first()
        if not author:
            LOGGER.error(f"Author with code '{code}' not found.")
            raise ValueError(f"Author with code '{code}' not found.")
        
        session.delete(author)
        session.commit()
        LOGGER.info(f"Deleted {author.name} successfully.")
