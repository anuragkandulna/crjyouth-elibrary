
from sqlalchemy.orm import Session
from sqlalchemy import text
from utils.my_logger import CustomLogger
from utils.timezone_utils import utc_now
from utils.security import generate_password_hash
from constants.constants import APP_LOG_FILE
from constants.config import LOG_LEVEL
import json


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=APP_LOG_FILE).get_logger()


# SQL-based seeding functions
def seed_authors_sql(session: Session, authors_data: dict) -> None:
    """
    SQL-based seeding for authors table.
    """
    inserted_count = 0
    
    for author_code, author_name in authors_data.items():
        # Check if author exists by code or name
        check_sql = text("SELECT 1 FROM authors WHERE code = :code OR name = :name")
        existing = session.execute(check_sql, {"code": author_code, "name": author_name}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Author '{author_name}' already exists, skipping.")
            continue
        
        # Insert new author
        insert_sql = text("""
            INSERT INTO authors (code, name)
            VALUES (:code, :name)
        """)
        session.execute(insert_sql, {
            "code": author_code,
            "name": author_name
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new author(s) via SQL.")
    else:
        LOGGER.info("✅ No new authors inserted via SQL. All authors already exist.")


def seed_books_sql(session: Session, books_data: list) -> None:
    """
    SQL-based seeding for books table.
    """
    inserted_count = 0
    
    for book_tuple in books_data:
        isbn, title, author_code, publisher_code, category, language, first_publication_year, price, description, contents = book_tuple
        isbn_str = str(isbn)
        
        # Check if book exists
        check_sql = text("SELECT 1 FROM books WHERE isbn = :isbn")
        existing = session.execute(check_sql, {"isbn": isbn_str}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Book with ISBN '{isbn}' already exists, skipping.")
            continue
        
        try:
            # Generate book_uuid, book_id, and book_number
            import uuid
            book_uuid = str(uuid.uuid4())
            
            # Get next book number for author
            num_sql = text("SELECT COALESCE(MAX(book_number), 0) + 1 FROM books WHERE author_code = :author_code")
            book_number = session.execute(num_sql, {"author_code": author_code}).scalar()
            
            # Generate book_id using the format from the model
            book_id = f"{author_code:02}{book_number:03}"
            
            # Insert new book
            insert_sql = text("""
                INSERT INTO books (
                    book_uuid, book_id, book_number, isbn, title, author_code, genre, language
                )
                VALUES (
                    :book_uuid, :book_id, :book_number, :isbn, :title, :author_code, :genre, :language
                )
            """)
            session.execute(insert_sql, {
                "book_uuid": book_uuid,
                "book_id": book_id,
                "book_number": book_number,
                "isbn": isbn_str,
                "title": title,
                "author_code": author_code,
                "genre": category,  # Use category as genre
                "language": language
            })
            inserted_count += 1
        except Exception as e:
            LOGGER.warning(f"ℹ️ Book with ISBN '{isbn}' creation failed: {e}")
            continue
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new book(s) via SQL.")
    else:
        LOGGER.info("✅ No new books inserted via SQL. All books already exist.")


def seed_book_copies_sql(session: Session, copies_data: list) -> None:
    """
    SQL-based seeding for book_copies table.
    """
    inserted_count = 0
    
    for copy_tuple in copies_data:
        book_id, branch_code, current_publication_year = copy_tuple
        
        try:
            # Get next copy number
            copy_num_sql = text("SELECT COALESCE(MAX(copy_number), 0) + 1 FROM book_copies WHERE book_id = :book_id")
            copy_number = session.execute(copy_num_sql, {"book_id": book_id}).scalar()
            
            # Generate copy_id and copy_uuid
            import uuid
            copy_uuid = str(uuid.uuid4())
            copy_id = f"{branch_code:02}{book_id}{copy_number:03}"
            
            # Check if book exists
            book_check_sql = text("SELECT 1 FROM books WHERE book_id = :book_id")
            book_exists = session.execute(book_check_sql, {"book_id": book_id}).scalar()
            if not book_exists:
                LOGGER.warning(f"ℹ️ Book '{book_id}' not found, skipping copy creation.")
                continue
            
            # Insert new copy
            insert_sql = text("""
                INSERT INTO book_copies (
                    copy_uuid, copy_id, book_id, branch_code, copy_number, is_available
                )
                VALUES (
                    :copy_uuid, :copy_id, :book_id, :branch_code, :copy_number, :is_available
                )
            """)
            session.execute(insert_sql, {
                "copy_uuid": copy_uuid,
                "copy_id": copy_id,
                "book_id": book_id,
                "branch_code": branch_code,
                "copy_number": copy_number,
                "is_available": True
            })
            inserted_count += 1
        except Exception as e:
            LOGGER.warning(f"ℹ️ Book copy '{book_id}-{branch_code}' creation failed: {e}")
            continue
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new book copy(ies) via SQL.")
    else:
        LOGGER.info("✅ No new book copies inserted via SQL. All copies already exist.")


# New seeding functions for existing models that were missing
def seed_genres_sql(session: Session, genres_data: list) -> None:
    """
    SQL-based seeding for genres table.
    """
    inserted_count = 0
    
    for item in genres_data:
        # Check if genre exists
        check_sql = text("SELECT 1 FROM genres WHERE name = :name")
        existing = session.execute(check_sql, {"name": item["name"]}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Genre '{item['name']}' already exists, skipping.")
            continue
        
        # Insert new genre
        insert_sql = text("""
            INSERT INTO genres (name, description, is_active)
            VALUES (:name, :description, :is_active)
        """)
        session.execute(insert_sql, {
            "name": item["name"],
            "description": item.get("description", ""),
            "is_active": True
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new genre(s) via SQL.")
    else:
        LOGGER.info("✅ No new genres inserted via SQL. All genres already exist.")


def seed_languages_sql(session: Session, languages_data: list) -> None:
    """
    SQL-based seeding for languages table.
    """
    inserted_count = 0
    
    for item in languages_data:
        language_name = item if isinstance(item, str) else item.get("language", item.get("name", ""))
        
        # Check if language exists
        check_sql = text("SELECT 1 FROM languages WHERE language = :language")
        existing = session.execute(check_sql, {"language": language_name}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Language '{language_name}' already exists, skipping.")
            continue
        
        # Insert new language
        insert_sql = text("""
            INSERT INTO languages (language, is_active)
            VALUES (:language, :is_active)
        """)
        session.execute(insert_sql, {
            "language": language_name,
            "is_active": True
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new language(s) via SQL.")
    else:
        LOGGER.info("✅ No new languages inserted via SQL. All languages already exist.")


def seed_offices_sql(session: Session, offices_data: dict) -> None:
    """
    SQL-based seeding for offices table.
    """
    inserted_count = 0
    
    for office_code, office_data in offices_data.items():
        office_code = int(office_code)
        
        # Check if office exists
        check_sql = text("SELECT 1 FROM offices WHERE code = :code")
        existing = session.execute(check_sql, {"code": office_code}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Office '{office_code}' already exists in '{office_data['city']}', skipping.")
            continue
        
        # Insert new office
        insert_sql = text("""
            INSERT INTO offices (code, name, address, city, pincode, is_active)
            VALUES (:code, :name, :address, :city, :pincode, :is_active)
        """)
        session.execute(insert_sql, {
            "code": office_code,
            "name": office_data['name'],
            "address": office_data['address'],
            "city": office_data['city'],
            "pincode": office_data['pincode'],
            "is_active": True
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new office(s) via SQL.")
    else:
        LOGGER.info("✅ No new offices inserted via SQL. All offices already exist.")


def seed_sessions_sql(session: Session, sessions_data: list) -> None:
    """
    SQL-based seeding for sessions table.
    Note: Sessions are typically runtime data, seeding may not be commonly needed.
    """
    inserted_count = 0
    
    for item in sessions_data:
        # Check if session exists
        session_id = item.get("session_id")
        if session_id:
            check_sql = text("SELECT 1 FROM sessions WHERE session_id = :session_id")
            existing = session.execute(check_sql, {"session_id": session_id}).scalar()
            if existing:
                LOGGER.info(f"ℹ️ Session '{session_id}' already exists, skipping.")
                continue
        
        # Insert new session (basic structure - adjust fields as needed)
        insert_sql = text("""
            INSERT INTO sessions (session_id, user_uuid, device_id, user_agent, ip_address, created_at, expires_at, is_active)
            VALUES (:session_id, :user_uuid, :device_id, :user_agent, :ip_address, :created_at, :expires_at, :is_active)
        """)
        session.execute(insert_sql, {
            "session_id": item.get("session_id"),
            "user_uuid": item.get("user_uuid"),
            "device_id": item.get("device_id"),
            "user_agent": item.get("user_agent"),
            "ip_address": item.get("ip_address"),
            "created_at": item.get("created_at", utc_now()),
            "expires_at": item.get("expires_at"),
            "is_active": item.get("is_active", True)
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new session(s) via SQL.")
    else:
        LOGGER.info("✅ No new sessions inserted via SQL. All sessions already exist.")


def seed_transactions_sql(session: Session, transactions_data: list) -> None:
    """
    SQL-based seeding for transactions table.
    """
    inserted_count = 0
    
    for item in transactions_data:
        # Check if transaction exists
        ticket_id = item.get("ticket_id")
        if ticket_id:
            check_sql = text("SELECT 1 FROM transactions WHERE ticket_id = :ticket_id")
            existing = session.execute(check_sql, {"ticket_id": ticket_id}).scalar()
            if existing:
                LOGGER.info(f"ℹ️ Transaction '{ticket_id}' already exists, skipping.")
                continue
        
        # Insert new transaction (basic structure - adjust fields as needed)
        insert_sql = text("""
            INSERT INTO transactions (transaction_uuid, ticket_id, office_code, customer_id, librarian_id, customer_name, copy_id, status, particulars, ticket_updated_date, book_borrow_date, book_due_date, fine_incurred)
            VALUES (:transaction_uuid, :ticket_id, :office_code, :customer_id, :librarian_id, :customer_name, :copy_id, :status, :particulars, :ticket_updated_date, :book_borrow_date, :book_due_date, :fine_incurred)
        """)
        
        import uuid
        session.execute(insert_sql, {
            "transaction_uuid": str(uuid.uuid4()),
            "ticket_id": item.get("ticket_id"),
            "office_code": item.get("office_code"),
            "customer_id": item.get("customer_id"),
            "librarian_id": item.get("librarian_id"),
            "customer_name": item.get("customer_name"),
            "copy_id": item.get("copy_id"),
            "status": item.get("status", "borrowed"),
            "particulars": item.get("particulars", "Test transaction"),
            "ticket_updated_date": item.get("ticket_updated_date", utc_now()),
            "book_borrow_date": item.get("book_borrow_date"),
            "book_due_date": item.get("book_due_date"),
            "fine_incurred": item.get("fine_incurred", 0.0)
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new transaction(s) via SQL.")
    else:
        LOGGER.info("✅ No new transactions inserted via SQL. All transactions already exist.")


def seed_users_sql(session: Session, users_data: dict) -> None:
    """
    SQL-based seeding for users table.
    """
    inserted_count = 0
    
    for user_id, user_data in users_data.items():
        user_id = int(user_id)
        
        # Check if user exists by email or user_id
        check_sql = text("SELECT 1 FROM users WHERE email = :email OR user_id = :user_id")
        existing = session.execute(check_sql, {
            "email": user_data["email"], 
            "user_id": user_id
        }).scalar()
        if existing:
            LOGGER.info(f"ℹ️ User '{user_data['email']}' already exists, skipping.")
            continue
        
        try:
            # Generate user_uuid
            import uuid
            user_uuid = str(uuid.uuid4())
            
            # Hash the password
            password_hash = generate_password_hash(user_data["password"])
            
            # Insert new user
            insert_sql = text("""
                INSERT INTO users (
                    user_uuid, user_id, first_name, last_name, email, 
                    password_hash, is_active, is_admin, registration_date
                )
                VALUES (
                    :user_uuid, :user_id, :first_name, :last_name, :email,
                    :password_hash, :is_active, :is_admin, :registration_date
                )
            """)
            session.execute(insert_sql, {
                "user_uuid": user_uuid,
                "user_id": user_id,
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "email": user_data["email"],
                "password_hash": password_hash,
                "is_active": user_data["is_active"],
                "is_admin": user_data["is_admin"],
                "registration_date": utc_now()
            })
            inserted_count += 1
        except Exception as e:
            LOGGER.warning(f"ℹ️ User '{user_data['email']}' creation failed: {e}")
            continue
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new user(s) via SQL.")
    else:
        LOGGER.info("✅ No new users inserted via SQL. All users already exist.")
