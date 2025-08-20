"""
Unit tests for the Base model.
"""

import pytest
from models.base import Base


@pytest.mark.unit
class TestBase:
    """Test cases for the Base model."""
    
    def test_base_is_declarative_base(self):
        """Test that Base is a SQLAlchemy DeclarativeBase."""
        from sqlalchemy.orm import DeclarativeBase
        assert issubclass(Base, DeclarativeBase)
    
    def test_base_docstring(self):
        """Test that Base has proper docstring."""
        assert Base.__doc__ is not None
        assert "Base class for all ORM models" in Base.__doc__
    
    def test_base_can_be_inherited(self):
        """Test that Base can be inherited by other models."""
        from sqlalchemy.orm import Mapped, mapped_column
        from sqlalchemy import String
        
        class TestModel(Base):
            __tablename__ = 'test_model'
            id: Mapped[str] = mapped_column(String, primary_key=True)
        
        assert hasattr(TestModel, '__tablename__')
        assert TestModel.__tablename__ == 'test_model'
        assert issubclass(TestModel, Base)
