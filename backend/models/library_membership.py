# models/library_membership.py

from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


class LibraryMembership(Base):
    __tablename__ = 'library_memberships'

    rank: Mapped[int] = mapped_column(Integer, primary_key=True)
    membership_title: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    borrowing_limit: Mapped[str] = mapped_column(Integer, nullable=False, default=1)
    borrow_duration_days: Mapped[str] = mapped_column(Integer, nullable=False, default=15)
    annual_fee: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)

    users = relationship("LibraryUser", back_populates="user_membership")
