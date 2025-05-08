from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy import String, Integer
from models.base import Base
from utils.my_logger import CustomLogger
from constants.constants import OPS_LOG_FILE


LOGGER = CustomLogger(__name__, level=20, log_file=OPS_LOG_FILE).get_logger()


class Publisher(Base):
    __tablename__ = "publishers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(4), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    books = relationship("Book", back_populates="publisher")


    def __repr__(self) -> str:
        return f"<Publisher(id='{self.id}', code='{self.code}', name='{self.name}')>"


    @classmethod
    def create_publisher(cls, session: Session, code: str, name: str) -> "Publisher":
        """
        Create a new publisher in the database.
        """
        # Check if publisher already exists
        existing = session.query(cls).filter(
            (cls.code == code) | (cls.name == name)
        ).first()
        if existing:
            LOGGER.warning(f"Skipped publication creation: Publisher with name '{name}' or code '{code}' already exists.")
            return existing
        
        new_publisher = cls(
            code=code,
            name=name
        )
        session.add(new_publisher)
        session.commit()
        LOGGER.info(f"Publisher added: '{code}' - '{name}' added successfully.")
        return new_publisher


    @staticmethod
    def delete_publisher(session: Session, code: str) -> None:
        """
        Delete a publisher permanently.
        """
        publisher = session.query(Publisher).filter_by(code=code).first()
        if not publisher:
            LOGGER.error(f"Publisher with code '{code}' not found.")
            raise ValueError(f"Publisher with code '{code}' not found.")
        
        session.delete(publisher)
        session.commit()
        LOGGER.info(f"Deleted {publisher.name} successfully.")
