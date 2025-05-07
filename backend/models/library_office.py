from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from models.base import Base


class LibraryOffice(Base):
    __tablename__ = "library_offices"

    office_code: Mapped[str] = mapped_column(String(5), primary_key=True)
    address: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[str] = mapped_column(String(50), nullable=False)
    pincode: Mapped[str] = mapped_column(Integer, nullable=False)
