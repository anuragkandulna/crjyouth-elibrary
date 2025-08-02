import json
from datetime import datetime
import os

from models.base import Base
from utils.psql_database import get_database_session, get_database_connection
from utils.db_operations import (
    seed_roles_sql,
    seed_memberships_sql,
    seed_library_offices_sql,
    seed_publishers_sql,
    seed_authors_sql,
    seed_status_codes_sql,
    seed_book_categories_sql,
    seed_book_languages_sql,
    seed_subject_difficulty_tiers_sql,
    seed_spiritual_maturity_levels_sql,
    seed_library_users_sql,
    seed_books_sql,
    seed_book_copies_sql,
    seed_referral_codes_sql
)
from utils.my_logger import CustomLogger
from constants.constants import INFRA_LOG_FILE
from constants.config import LOG_LEVEL


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=INFRA_LOG_FILE).get_logger()

# Get the directory where this script is located (works from any execution directory)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_DIR = os.path.join(SCRIPT_DIR, "seed_data")


def detect_environment():
    """Detect if running in container or local environment."""
    if os.path.exists('/.dockerenv'):
        return "container"
    else:
        return "local"


def load_seed_json(filename):
    with open(os.path.join(SEED_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    session = get_database_session()
    db_connection = get_database_connection()

    env_type = detect_environment()
    engine = db_connection.engine
    if engine is None:
        raise RuntimeError("Database engine not properly initialized")
    
    if env_type == "container":
        LOGGER.info("🐳 Container environment detected - dropping all existing tables to ensure fresh state...")
        # Drop all tables first for completely fresh state (container only)
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
        # Seed all tables using dedicated seeder functions
        LOGGER.info("🌱 Starting database seeding process...")
        
        # Core system tables - using SQL-based functions
        seed_roles_sql(session, load_seed_json("role_seed.json"))
        seed_memberships_sql(session, load_seed_json("membership_seed.json"))
        seed_library_offices_sql(session, load_seed_json("library_office_seed.json"))
        
        # Reference data tables - using SQL-based functions
        seed_publishers_sql(session, load_seed_json("publishers_seed.json"))
        seed_authors_sql(session, load_seed_json("authors_seed.json"))
        seed_status_codes_sql(session, load_seed_json("status_code_seed.json"))
        seed_book_categories_sql(session, load_seed_json("book_categories_seed.json"))
        seed_book_languages_sql(session, load_seed_json("languages_seed.json"))
        seed_subject_difficulty_tiers_sql(session, load_seed_json("subject_difficulty_seed.json"))
        seed_spiritual_maturity_levels_sql(session, load_seed_json("spiritual_maturity_seed.json"))
        
        # User and content tables - using SQL-based functions
        seed_library_users_sql(session, load_seed_json("users_seed.json"))
        seed_books_sql(session, load_seed_json("books_seed.json"))
        seed_book_copies_sql(session, load_seed_json("book_copies_seed.json"))
        
        # Referral codes - using SQL-based functions (depends on users and offices)
        seed_referral_codes_sql(session, load_seed_json("referral_codes_seed.json"))
        
        LOGGER.info("🎉 Database seeding completed successfully!")

    except Exception as ex:
        session.rollback()
        LOGGER.error(f"❌ Error during seeding: {ex}")
        raise

    finally:
        session.close()
