from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from constants.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_USER
from constants.constants import OPS_LOG_FILE
from utils.my_logger import CustomLogger


# Invoke logger
LOGGER = CustomLogger(__name__, level=20, log_file=OPS_LOG_FILE).get_logger()
DATABASE_URI = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"


class DatabaseConnection:
    def __init__(self):
        """
        Setup a database connection engine.
        """
        try:
            self.engine = create_engine(
                DATABASE_URI,
                pool_size=10,
                max_overflow=20
            )
            self.SessionLocal = sessionmaker(bind=self.engine)
            LOGGER.info("Database connection created successfully.")

        except Exception as ex:
            LOGGER.critical(f"Failed to connect to database: {ex}")
            raise

    def get_session(self):
        """
        Create a database session.
        """
        return self.SessionLocal()


# Globally initiate database
db = DatabaseConnection()
db_session = db.get_session()
