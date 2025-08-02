from sqlalchemy import Integer, String, Boolean, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from models.base import Base
from typing import Optional
from utils.my_logger import CustomLogger
from constants.config import LOG_LEVEL
from constants.constants import OPS_LOG_FILE
from models.exceptions import SubjectDifficultyTierNotFoundError


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


class SubjectDifficultyTier(Base):
    __tablename__ = "subject_difficulty_tiers"

    tier: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    difficulty_class: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    books = relationship("Book", back_populates="subject_difficulty")


    @classmethod
    def generate_tier_name(cls, difficulty_class: str, difficulty_value: Optional[int]) -> str:
        """
        Create book tier name string using difficulty_class and difficulty_value.
        """
        if difficulty_value is not None:
            return f"{difficulty_class.upper()}-{difficulty_value}"
        return f"{difficulty_class.upper()}"


    @classmethod
    def create_tier(
        cls, session: Session, tier: int,
        difficulty_class: str, difficulty_value: Optional[int],
        description: str, is_private: bool
    ) -> "SubjectDifficultyTier":
        """
        Create a new book tier in the database.
        """
        name = cls.generate_tier_name(difficulty_class, difficulty_value=difficulty_value)

        stmt = select(cls).where((cls.name == name))
        existing = session.scalar(stmt)

        if existing:
            LOGGER.warning(f"Skipped tier creation '{name}' already exists.")
            return existing

        tier_obj = cls(tier=tier, name=name, difficulty_class=difficulty_class, 
                       difficulty_value=difficulty_value, description=description, is_private=is_private)
        session.add(tier_obj)
        session.commit()
        LOGGER.info(f"Created book tier '{name}' added successfully.")
        return tier_obj


    @staticmethod
    def delete_tier(session: Session, name: str) -> None:
        """
        Soft delete a book tier by name.
        """
        stmt = select(SubjectDifficultyTier).where(SubjectDifficultyTier.name == name, SubjectDifficultyTier.is_active.is_(True))
        tier = session.scalar(stmt)

        if not tier:
            LOGGER.error(f"Book tier '{tier}' not found.")
            raise SubjectDifficultyTierNotFoundError(f"Book tier '{tier}' not found.")

        tier.is_active = False
        session.commit()
        LOGGER.info(f"Book tier {tier.name} deactivated successfully.")


    def __repr__(self):
        return f"<SubjectDifficultyTier(tier={self.tier}, name='{self.name}', active={self.is_active})>"
