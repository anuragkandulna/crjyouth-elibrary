"""
Database connection utilities for the CRJ Youth Library application.

This module provides thread-safe database connection and session management
using SQLAlchemy with connection pooling for improved concurrent performance.

Usage:
    # Use context manager for automatic transaction management (recommended)
    from utils.sqlite_database import get_db_session
    
    with get_db_session() as session:
        user = session.query(LibraryUser).first()
        # Automatic commit/rollback/cleanup
"""

import os
import threading
import time
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
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
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseConnection, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Setup a database connection engine with connection pooling.
        Expects database file to already exist (created by bootstrap_database.sh).
        """
        try:
            if not os.path.exists(DB_FILE):
                raise RuntimeError(f"Database file not found at {DB_FILE}. Please run bootstrap_database.sh first.")
            
            # Create engine with connection pooling
            self._engine = create_engine(
                DATABASE_URI,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20
                },
                # Connection pooling configuration
                poolclass=QueuePool,
                pool_size=10,  # Maximum number of connections in pool
                max_overflow=20,  # Additional connections beyond pool_size
                pool_timeout=30,  # Timeout for getting connection from pool
                pool_recycle=3600,  # Recycle connections after 1 hour
                pool_pre_ping=True,  # Validate connections before use
                echo=False
            )
            
            # Configure session factory
            self._session_local = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False
            )
            
            # Set up connection event listeners for better monitoring
            self._setup_connection_events()
            
            LOGGER.info(f"SQLite database connection pool initialized at {DB_FILE}")
            LOGGER.info(f"Pool configuration: size={self._engine.pool.size()}, overflow={self._engine.pool._max_overflow}")

        except Exception as ex:
            LOGGER.critical(f"Failed to connect to SQLite database: {ex}")
            raise

    def _setup_connection_events(self):
        """Set up SQLAlchemy connection event listeners for monitoring"""
        
        @event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Configure SQLite connection for better performance"""
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
            LOGGER.debug("SQLite connection configured with WAL mode and optimizations")

        @event.listens_for(self._engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log when connections are checked out from pool"""
            LOGGER.debug(f"Connection checked out from pool. Pool size: {self._engine.pool.size()}")

        @event.listens_for(self._engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log when connections are returned to pool"""
            LOGGER.debug(f"Connection returned to pool. Pool size: {self._engine.pool.size()}")

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

    def get_pool_stats(self):
        """Get connection pool statistics"""
        pool = self._engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow()
        }

    def dispose(self):
        """Dispose of the engine and close all connections"""
        if self._engine:
            self._engine.dispose()
            LOGGER.info("Database engine disposed and all connections closed")


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
