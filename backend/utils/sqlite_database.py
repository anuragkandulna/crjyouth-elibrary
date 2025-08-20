"""
Database connection utilities for the CRJ Youth Library application.

This module provides thread-safe database connection and session management
using the Singleton pattern for the database connection and factory functions
for creating new database sessions.

Usage:
    # Get database connection object (singleton)
    db_conn = get_database_connection()
    
    # Get a new database session (manual management)
    session = get_database_session()
    try:
        # Perform database operations
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    
    # Use context manager for automatic transaction management (recommended)
    from utils.psql_database import get_db_session
    
    with get_db_session() as session:
        user = session.query(LibraryUser).first()
        # Automatic commit/rollback/cleanup
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from constants.config import LOG_LEVEL
from constants.constants import APP_LOG_FILE
from constants.config import DB_NAME
from utils.my_logger import CustomLogger


# Invoke logger
LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=APP_LOG_FILE).get_logger()

# SQLite database configuration
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DB_FILE = os.path.join(DB_DIR, f'{DB_NAME}.db')
DATABASE_URI = f"sqlite:///{DB_FILE}"


class DatabaseConnection:
    _instance = None
    _engine = None
    _session_local = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Setup a database connection engine (singleton pattern).
        Expects database file to already exist (created by bootstrap_database.sh).
        """
        try:
            if not os.path.exists(DB_FILE):
                raise RuntimeError(f"Database file not found at {DB_FILE}. Please run bootstrap_database.sh first.")
            
            self._engine = create_engine(
                DATABASE_URI,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20
                },
                echo=False
            )
            self._session_local = sessionmaker(bind=self._engine)
            LOGGER.info(f"SQLite database connection created successfully at {DB_FILE}")

        except Exception as ex:
            LOGGER.critical(f"Failed to connect to SQLite database: {ex}")
            raise

    @property
    def engine(self):
        """Get the database engine."""
        return self._engine

    @property
    def session_local(self):
        """Get the session factory."""
        return self._session_local

    def get_session(self):
        """
        Create a new database session.
        """
        if self._session_local is None:
            raise RuntimeError("Database connection not properly initialized")
        return self._session_local()
    
    def create_all_tables(self, base):
        """
        Create all database tables from SQLAlchemy Base metadata.
        
        Args:
            base: SQLAlchemy declarative base containing table definitions
        """
        try:
            base.metadata.create_all(bind=self._engine)
            LOGGER.info("Database tables created successfully")
        except Exception as ex:
            LOGGER.error(f"Failed to create database tables: {ex}")
            raise


# Global database connection functions
def get_database_connection() -> DatabaseConnection:
    """
    Get the database connection object (singleton).
    
    Returns:
        DatabaseConnection: The database connection instance
    """
    return DatabaseConnection()


def get_database_session():
    """
    Get a new database session.
    
    Returns:
        Session: A new SQLAlchemy session instance
    """
    db_connection = get_database_connection()
    return db_connection.get_session()


@contextmanager
def get_db_session():
    """
    Context manager for database sessions with automatic transaction management.
    
    Provides automatic commit on success, rollback on exception, and cleanup.
    
    Usage:
        with get_db_session() as session:
            user = session.query(LibraryUser).first()
            # Automatic commit if no exception
            
    Yields:
        Session: A new database session with automatic transaction management
    """
    session = get_database_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def initialize_database(base):
    """
    Initialize the SQLite database with all tables.

    Args:
        base: SQLAlchemy declarative base containing table definitions
    """
    db_connection = get_database_connection()
    db_connection.create_all_tables(base)
