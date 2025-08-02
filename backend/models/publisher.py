from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy import String, Integer, select
from models.base import Base
from utils.my_logger import CustomLogger
from constants.constants import OPS_LOG_FILE
from constants.config import LOG_LEVEL
from models.exceptions import PublisherNotFoundError


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


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
        stmt = select(cls).where((cls.code == code) | (cls.name == name))
        existing = session.execute(stmt).scalar_one_or_none()

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
        stmt = select(Publisher).where(Publisher.code == code)
        publisher = session.execute(stmt).scalar_one_or_none()

        if not publisher:
            LOGGER.error(f"Publisher with code '{code}' not found.")
            raise PublisherNotFoundError(f"Publisher with code '{code}' not found.")

        session.delete(publisher)
        session.commit()
        LOGGER.info(f"Deleted {publisher.name} successfully.")
