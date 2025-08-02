from sqlalchemy import String, Integer, Boolean, select
from sqlalchemy.orm import Mapped, mapped_column, Session
from models.base import Base
from utils.my_logger import CustomLogger
from constants.config import LOG_LEVEL
from constants.constants import OPS_LOG_FILE
from models.exceptions import DuplicateSpiritualMaturityLevelError, SpiritualMaturityLevelNotFound


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


class SpiritualMaturityLevel(Base):
    __tablename__ = "spiritual_maturity_levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    min_years: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    max_years: Mapped[int] = mapped_column(Integer, default=120, nullable=True)
    weight: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    is_special_class: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)


    @classmethod
    def create(
        cls,
        session: Session,
        code: str,
        title: str,
        weight: int,
        min_years: int = 0,
        max_years: int = 120,
        is_special_class: bool = False,
        description: str = ""
    ) -> "SpiritualMaturityLevel":
        """
        Create a new spiritual maturity level in the database.
        """
        stmt = select(cls).where(
            (cls.code == code) | (cls.title == title) | (cls.weight == weight)
        )
        existing = session.scalar(stmt)

        if existing:
            LOGGER.error(f"Spiritual maturity level with this details already exists {existing.title}")
            raise DuplicateSpiritualMaturityLevelError(f"Spiritual maturity level with this details already exists {existing.title}")

        level = cls(
            code=code,
            title=title,
            min_years=min_years,
            max_years=max_years,
            weight=weight,
            is_special_class=is_special_class,
            description=description
        )
        session.add(level)
        session.commit()
        LOGGER.info(f"New spiritual maturity level {level} created successfully")
        return level


    @staticmethod
    def get_all_active(session: Session) -> list:
        """
        Fetch all active maturity levels sorted by weight.
        """
        stmt = select(SpiritualMaturityLevel).where(SpiritualMaturityLevel.is_active.is_(True)).order_by(SpiritualMaturityLevel.weight)
        return list(session.scalars(stmt).all())


    @staticmethod
    def delete_soft(session: Session, code: str) -> None:
        """
        Soft delete a maturity level by marking it inactive.
        """
        stmt = select(SpiritualMaturityLevel).where(SpiritualMaturityLevel.code == code, SpiritualMaturityLevel.is_active.is_(True))
        level = session.scalar(stmt)

        if not level:
            LOGGER.error(f"No spiritual maturity level exists with the code {code}")
            raise SpiritualMaturityLevelNotFound(f"No spiritual maturity level exists with the code {code}")

        level.is_active = False
        session.commit()
        LOGGER.info(f"Spiritual maturity level with code {code} deactivated successfully.")


    def __repr__(self):
        return f"<SpiritualMaturityLevel(code='{self.code}', title='{self.title}', active={self.is_active})>"
