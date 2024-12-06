# models/base.py

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Base class for all ORM models.
    Inherit this in every model to register it with SQLAlchemy metadata.
    """
    pass
