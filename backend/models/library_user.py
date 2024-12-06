from sqlalchemy import String, Integer, Boolean, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
import hashlib
from models.base import Base

class UserRole(Base):
    __tablename__ = 'user_roles'

    rank: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    permissions: Mapped[list] = mapped_column(JSON, nullable=False)

class LibraryUser(Base):
    __tablename__ = 'users'

    user_id: Mapped[str] = mapped_column(String(10), primary_key=True, unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(30), nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(15), nullable=True)
    registration_date: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    role: Mapped[int] = mapped_column(ForeignKey('user_roles.rank'), default=3, nullable=False)
    max_books_allowed: Mapped[int] = mapped_column(default=5, nullable=False)
    borrowed_books: Mapped[list] = mapped_column(JSON, default=list)
    fines_due: Mapped[float] = mapped_column(default=0.0)
    is_active: Mapped[bool] = mapped_column(default=True)
    password: Mapped[str] = mapped_column(String(128), nullable=False)

    user_role = relationship("UserRole", backref="users", primaryjoin="LibraryUser.role == UserRole.rank")

    def __init__(self, first_name: str, last_name: str, email: str, phone_number: str, password: str,
                 max_books_allowed: int = 5):
        self.user_id = self.generate_user_id(email)
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone_number = phone_number
        self.password = self.hash_password(password)
        self.role = 3  # Default to Member
        self.max_books_allowed = max_books_allowed

    @staticmethod
    def generate_user_id(email: str) -> str:
        now = datetime.utcnow().isoformat()
        data = f"{email}{now}"
        return hashlib.sha256(data.encode()).hexdigest()[:10]

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        return self.password == self.hash_password(password)

    def check_permission(self, action: str) -> bool:
        if self.user_role and action in self.user_role.permissions:
            return True
        return False
