import json
import os
from models.base import Base
from utils.sqlite_database import get_database_session, get_database_connection
from utils.db_operations import (
    seed_authors_sql,
    seed_languages_sql,
    seed_books_sql,
    seed_book_copies_sql,
    seed_genres_sql,
    seed_offices_sql,
    seed_sessions_sql,
    seed_transactions_sql,
    seed_users_sql,
)
from utils.my_logger import CustomLogger
from constants.constants import APP_LOG_FILE
from constants.config import LOG_LEVEL


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=APP_LOG_FILE).get_logger()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_DIR = os.path.join(SCRIPT_DIR, "seed_data")


def detect_environment():
    """Detect if running in container or local environment."""
    if os.path.exists('/.dockerenv'):
        return "container"
    else:
        return "local"


def load_seed_json(filename):
    """Load seed data from JSON file with error handling."""
    file_path = os.path.join(SEED_DIR, filename)
    if not os.path.exists(file_path):
        LOGGER.warning(f"⚠️ Seed file '{filename}' not found, skipping...")
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        LOGGER.error(f"❌ Error loading seed file '{filename}': {e}")
        return None


if __name__ == "__main__":
    session = get_database_session()
    db_connection = get_database_connection()

    env_type = detect_environment()
    engine = db_connection.engine
    if engine is None:
        raise RuntimeError("Database engine not properly initialized")
    
    if env_type == "container":
        LOGGER.info("🐳 Container environment detected - dropping all existing tables to ensure fresh state...")
        Base.metadata.drop_all(bind=engine)
        LOGGER.info("🗑️ All tables dropped successfully.")
        
        LOGGER.info("⏳ Creating all database tables...")
        Base.metadata.create_all(bind=engine)
        LOGGER.info("✅ Tables created fresh.")
    else:
        LOGGER.info("🏠 Local environment detected - preserving existing data for safety...")
        LOGGER.info("⏳ Creating database tables (if they don't exist)...")
        Base.metadata.create_all(bind=engine)
        LOGGER.info("✅ Tables verified/created.")

    try:
        LOGGER.info("🌱 Starting database seeding process...")
        
        # Load and seed data with error handling
        seed_data = {
            "authors": load_seed_json("authors_seed.json"),
            "languages": load_seed_json("languages_seed.json"),
            "genres": load_seed_json("genres_seed.json"),
            "offices": load_seed_json("offices_seed.json"),
            "sessions": load_seed_json("sessions_seed.json"),
            "transactions": load_seed_json("transactions_seed.json"),
            "books": load_seed_json("books_seed.json"),
            "book_copies": load_seed_json("book_copies_seed.json"),
            "users": load_seed_json("users_seed.json")
        }
        
        # Seed data in dependency order
        if seed_data["authors"]:
            seed_authors_sql(session, seed_data["authors"])
        
        if seed_data["languages"]:
            seed_languages_sql(session, seed_data["languages"])
        
        if seed_data["genres"]:
            seed_genres_sql(session, seed_data["genres"])
        
        if seed_data["offices"]:
            seed_offices_sql(session, seed_data["offices"])
        
        if seed_data["books"]:
            seed_books_sql(session, seed_data["books"])
        
        if seed_data["book_copies"]:
            seed_book_copies_sql(session, seed_data["book_copies"])
        
        # Optional seeding (sessions and transactions are typically runtime data)
        if seed_data["sessions"]:
            seed_sessions_sql(session, seed_data["sessions"])
        
        if seed_data["transactions"]:
            seed_transactions_sql(session, seed_data["transactions"])
        
        if seed_data["users"]:
            seed_users_sql(session, seed_data["users"])
        
        LOGGER.info("🎉 Database seeding completed successfully!")

    except Exception as ex:
        session.rollback()
        LOGGER.error(f"❌ Error during seeding: {ex}")
        raise

    finally:
        session.close()
