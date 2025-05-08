from datetime import datetime
from models.base import Base
from utils.psql_database import db
from utils.db_operations import (
    seed_roles,
    seed_memberships,
    seed_library_offices
)
from models.author import Author
from models.publisher import Publisher
from models.library_user import LibraryUser
from models.book import Book
from models.book_copy import BookCopy
from models.status_codes import StatusCode
from utils.my_logger import CustomLogger
from constants.constants import APP_LOG_FILE


LOGGER = CustomLogger(__name__, level=20, log_file=APP_LOG_FILE).get_logger()


if __name__ == "__main__":
    session = db.get_session()

    LOGGER.info("⏳ Creating all database tables...")
    Base.metadata.create_all(bind=db.engine)
    LOGGER.info("✅ Tables created.")

    try:
        predefined_roles = {
            1: ("Admin", ["add_book", "edit_book", "delete_book", "approve_lending", "manage_users"]),
            2: ("Moderator", ["approve_lending", "manage_threads", "resolve_issues"]),
            3: ("Member", ["borrow_book", "return_book", "suggest_book", "participate_threads"]),
        }

        predefined_memberships = {
            1: ("Founder", 100000.0, 20, 60),
            2: ("Elite", 1000.0, 5, 30),
            3: ("Premium", 500.0, 4, 30),
            4: ("Regular", 250.0, 2, 15),
            5: ("Basic", 100.0, 1, 15),
        }

        predefined_offices = {
            "DHN01": ("JJNPC", "Dhanbad", "Jharkhand", "India", 828307),
            "MIH01": ("JJNPC", "Mihijam", "Jharkhand", "India", 815354)
        }

        seed_library_offices(session, predefined_offices)
        seed_roles(session, predefined_roles)
        seed_memberships(session, predefined_memberships)

        # ---------------- Seed Publishers --------------- #
        predefined_publishers = {
            "BSIN": "Bible Society of India",
            "ODBM": "Our Daily Bread Ministries",
        }
        for pub_code, pub_name in predefined_publishers.items():
            try:
                publisher1 = Publisher.create_publisher(session, code=pub_code, name=pub_name)
                LOGGER.info(f"✅ Seeded {publisher1.name} new publisher.")
            except Exception as ex:
                LOGGER.error(f"ℹ️ Skipped {pub_name} publisher seeding: {ex}")

        # ------------------ Seed Authors ---------------- #
        predefined_authors = {
            "BH": "Benny Hinn",
            "BG": "Billy Graham",
            "DP": "Derek Prince",
            "FM": "Dr. Francis Myles",
            "JG": "James W. Gall",
            "JK": "John Kurian",
            "JB": "John Bunyan",
            "RB": "Reinhard Bonnke",
            "SW": "Sam Wellman",
            "WN": "Watchman Nee",
            "WL": "Witness Lee",
            "WC": "William Carey",
            "ZP": "Zac Poonen",
        }
        for author_code, author_name in predefined_authors.items():
            try:
                author1 = Author.create_author(session, code=author_code, name=author_name)
                LOGGER.info(f"✅ Seeded {author1.name} new author.")
            except Exception as ex:
                LOGGER.error(f"ℹ️ Skipped {author_name} author seeding: {ex}")

        # --------------- Seed Status Codes -------------- #
        predefined_status_codes = [
            ("ACTIVE", "USER", "Active library user"),
            ("INACTIVE", "USER", "Deactivated library user"),
            ("BLACKLIST", "USER", "Permanently blacklisted library user"),
            ("BLOCKED", "USER", "Temporarily suspended library user"),
            ("BORROWED", "TRANSACTION", "Book currently borrowed"),
            ("RETURNED", "TRANSACTION", "Book returned successfully"),
            ("PENDING", "TRANSACTION", "Waiting for transaction approval"),
            ("OVERDUE", "TRANSACTION", "Return deadline missed"),
            ("LOST", "TRANSACTION", "Book reported lost"),
        ]
        for status_data in predefined_status_codes:
            try:
                code1 = StatusCode.create_new_code(session, code=status_data[0],
                                                   category=status_data[1], description=status_data[2])
                LOGGER.info(f"✅ Seeded {code1.code} - {code1.category} new status code.")
            except Exception as ex:
                LOGGER.error(f"ℹ️ Skipped {status_data[0]} status code seeding: {ex}")

        # ------------------ Seed Users ------------------ #
        predefined_users = [
            ("Fake", "Admin", "admin@crj.org", "1111111111", "admin123", 1, 1),
            ("Fake", "Mod", "mod@crj.org", "2222222222", "mod123", 2, 2),
            ("Fake", "Member", "member@crj.org", "3333333333", "member123", 3, 5)
        ]
        for user_data in predefined_users:
            try:
                user1 = LibraryUser.create_user(session, first_name=user_data[0], last_name=user_data[1],
                                                email=user_data[2], phone_number=user_data[3], password=user_data[4],
                                                role=user_data[5], membership_type=user_data[6])
                LOGGER.info(f"✅ Seeded new user successfully: {user1}")
            except Exception as ex:
                LOGGER.error(f"ℹ️ Skipped {user_data[0]} user seeding: {ex}")

        # ------------------ Seed Books ------------------ #
        predefined_books = [
            (101, "Test Book 1", None, "BSIN", "Bible", "English", 2001),
            (102, "Test Book 2", "BG", "ODBM", "Story", "Hindi", 2005)
        ]
        for book_data in predefined_books:
            try:
                book1 = Book.create_book(session, isbn=book_data[0], title=book_data[1], author_code=book_data[2],
                                         publisher_code=book_data[3], type=book_data[4], language=book_data[5],
                                         first_publication_year=book_data[6])
                LOGGER.info(f"✅ Seeded new book successfully: {book1}")
            except Exception as ex:
                LOGGER.error(f"ℹ️ Skipped {book_data[0]} book seeding: {ex}")

        # ------------------ Seed Book Copies ------------------ #
        predefined_copies = [
            ("BSIN-001", "DHN01", 120.0, 2020),
            ("BSIN-001", "MIH01", 120.0, 2021),
            ("BG-001", "DHN01", 150.0, 2019)
        ]
        for copy_data in predefined_copies:
            try:
                copy1 = BookCopy.create_copy(session, book_id=copy_data[0], branch_code=copy_data[1], price=copy_data[2], current_publication_year=copy_data[3])
                LOGGER.info(f"✅ Seeded new book copy successfully: {copy1}")
            except Exception as ex:
                LOGGER.error(f"ℹ️ Skipped {copy_data[0]} - {copy_data[1]} book copy seeding: {ex}")

    except Exception as ex:
        session.rollback()
        LOGGER.info(f"❌ Error during seeding: {ex}")
    finally:
        session.close()
