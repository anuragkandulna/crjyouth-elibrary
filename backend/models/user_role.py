from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base

class UserRole(Base):
    __tablename__ = 'user_roles'

    rank: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    permissions: Mapped[list] = mapped_column(JSON, nullable=False)

    users = relationship("LibraryUser", back_populates="user_role")
