from sqlalchemy.orm import Mapped, mapped_column, Session
from sqlalchemy import Integer, String, select, Boolean
from models.base import Base
from utils.my_logger import CustomLogger
from constants.constants import APP_LOG_FILE
from constants.config import LOG_LEVEL
from models.exceptions import DuplicateOfficeError, OfficeNotFoundError

LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=APP_LOG_FILE).get_logger()


class Office(Base):
    __tablename__ = "offices"

    code: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    pincode: Mapped[str] = mapped_column(String(6), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


    def __repr__(self) -> str:
        return f"<Office(code='{self.code}', name='{self.name}', city='{self.city}')>"


    @classmethod
    def create_office(cls, session: Session, code: int, name: str, address: str, city: str, pincode: str) -> "Office":
        stmt = select(cls).where(cls.code == code)
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            LOGGER.error(f"Office code {code} already exists.")
            raise DuplicateOfficeError(f"Office code {code} already exists.")

        office = cls(code=code, name=name, address=address, city=city, pincode=pincode)
        session.add(office)
        session.commit()
        LOGGER.info(f"Office {code} created successfully.")
        return office


    @classmethod
    def view_office(cls, session: Session, code: int) -> dict:
        stmt = select(cls).where(cls.code == code)
        office = session.execute(stmt).scalar_one_or_none()
        if not office:
            LOGGER.error(f"Office {code} not found.")
            raise OfficeNotFoundError("Office not found.")

        return {
            "code": office.code,
            "name": office.name,
            "address": office.address,
            "city": office.city,
            "pincode": office.pincode,
            "active": office.is_active
        }


    @classmethod
    def edit_office(cls, session: Session, code: int, **kwargs) -> None:
        stmt = select(cls).where(cls.code == code)
        office = session.execute(stmt).scalar_one_or_none()
        if not office:
            LOGGER.error(f"Office {code} not found for editing.")
            raise OfficeNotFoundError("Office not found")

        for key, value in kwargs.items():
            if hasattr(office, key):
                setattr(office, key, value)

        session.commit()
        LOGGER.info(f"Office '{office.code}' updated with {kwargs.keys()}.")


    @classmethod
    def delete_office(cls, session: Session, code: int) -> None:
        stmt = select(cls).where(cls.code == code)
        office = session.execute(stmt).scalar_one_or_none()
        if not office:
            LOGGER.error(f"Office {code} not found for deletion.")
            raise OfficeNotFoundError("Office not found")

        office.is_active = False
        session.commit()
        LOGGER.info(f"Office {code} deactivated successfully.")


    @classmethod
    def get_all_offices(cls, session: Session) -> list[dict]:
        stmt = select(cls).where(cls.is_active.is_(True)).order_by(cls.code)
        offices = session.execute(stmt).scalars().all()
        return [cls.view_office(session, office.code) for office in offices]
