from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy import String, Integer, Boolean
from models.base import Base
from constants.constants import STATUS_CODE_CATEGORY, OPS_LOG_FILE
from utils.my_logger import CustomLogger
from constants.config import LOG_LEVEL


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


class StatusCode(Base):
    __tablename__ = "status_codes"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


    def is_valid_category(category: str) -> bool:
        """
        Verify if status code category exists.
        """
        return category in STATUS_CODE_CATEGORY


    def __repr__(self) -> str:
        return f"<StatusCode(code='{self.code}', category='{self.category}', description='{self.description}'"


    # ------------------ CRUD Operations ------------------ #
    @classmethod
    def create_new_code(cls, session: Session,
                        code: str, category: str, description: str) -> "StatusCode":
        """
        Create a new status code in database.
        """
        # Check if status code already exists
        if session.query(cls).filter_by(code=code).first():
            LOGGER.exception(f"Status code {code} already exists.")
            raise ValueError(f"Status code {code} already exists.")
        
        # Check if status code category already exists
        if not cls.is_valid_category(category):
            LOGGER.error(f"Status code category {category} does not exist.")
            raise ValueError(f"Status code category {category} does not exist.")

        new_code = cls(
            code=code,
            category=category,
            description=description
        )
        session.add(new_code)
        session.commit()
        LOGGER.info(f"Status code {new_code.code} - {new_code.category} added successfully.")
        return new_code


    @staticmethod
    def delete_status_code(session: Session, code: str) -> None:
        """
        Soft delete a status code.
        """
        status_code = session.query(StatusCode).filter_by(code=code, is_active=True).first()
        if not status_code:
            LOGGER.error(f"Status code {code} not found or is already deleted.")
            raise ValueError(f"Status code {code} not found or is already deleted.")
        
        status_code.is_active = False
        session.commit()
        LOGGER.info(f"Status code {status_code.code} - {status_code.category} deactivated successfully.")
