### utils/db_operations.py

from sqlalchemy.orm import Session
from sqlalchemy import text
from utils.my_logger import CustomLogger
from utils.timezone_utils import utc_now
from constants.constants import INFRA_LOG_FILE
from constants.config import LOG_LEVEL
import json


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=INFRA_LOG_FILE).get_logger()


def seed_roles(session: Session, predefined_roles: dict) -> None:
    """
    Core logic to seed user_roles.
    """
    inserted_count = 0
    for rank, (role_name, permissions) in predefined_roles.items():
        rank = int(rank)
        
        # Check if role exists
        check_sql = text("SELECT 1 FROM user_roles WHERE rank = :rank")
        existing = session.execute(check_sql, {"rank": rank}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Role '{role_name}' already exists, skipping.")
            continue
        
        # Insert new role
        insert_sql = text("""
            INSERT INTO user_roles (rank, role, permissions) 
            VALUES (:rank, :role, :permissions)
        """)
        session.execute(insert_sql, {
            "rank": rank,
            "role": role_name,
            "permissions": json.dumps(permissions)
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new role(s).")
    else:
        LOGGER.info("✅ No new roles inserted. All roles already exist.")


def seed_memberships(session: Session, predefined_memberships: dict) -> None:
    """
    Core logic to seed library_memberships.
    """
    inserted_count = 0
    for rank, (membership, reg_fee, book_limit, days_count) in predefined_memberships.items():
        rank = int(rank)
        
        # Check if membership exists
        check_sql = text("SELECT 1 FROM library_memberships WHERE rank = :rank")
        existing = session.execute(check_sql, {"rank": rank}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Membership class '{membership}' already exists, skipping.")
            continue
        
        # Insert new membership
        insert_sql = text("""
            INSERT INTO library_memberships (rank, membership_title, borrowing_limit, borrow_duration_days, annual_fee)
            VALUES (:rank, :membership_title, :borrowing_limit, :borrow_duration_days, :annual_fee)
        """)
        session.execute(insert_sql, {
            "rank": rank,
            "membership_title": membership,
            "borrowing_limit": book_limit,
            "borrow_duration_days": days_count,
            "annual_fee": reg_fee
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new membership(s).")
    else:
        LOGGER.info("✅ No new memberships inserted. All memberships already exist.")


def seed_library_offices(session: Session, predefined_offices: dict) -> None:
    """
    Core logic to seed library_offices table.
    :param session: Active SQLAlchemy session.
    :param predefined_offices: Dictionary with office_code as key and office details as value.
    """
    inserted_count = 0

    for office_code, office_data in predefined_offices.items():
        # Check if office exists
        check_sql = text("SELECT 1 FROM library_offices WHERE office_code = :office_code")
        existing = session.execute(check_sql, {"office_code": office_code}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Library Office '{office_code}' already exists in '{office_data['city']}', skipping.")
            continue
        
        # Insert new office
        insert_sql = text("""
            INSERT INTO library_offices (office_code, office_tag, office_num, address, city, state, country, pincode, is_active)
            VALUES (:office_code, :office_tag, :office_num, :address, :city, :state, :country, :pincode, :is_active)
        """)
        session.execute(insert_sql, {
            "office_code": office_code,
            "office_tag": office_data['office_tag'],
            "office_num": office_data['office_num'],
            "address": office_data['address'],
            "city": office_data['city'],
            "state": office_data['state'],
            "country": office_data['country'],
            "pincode": office_data['pincode'],
            "is_active": True
        })
        inserted_count += 1

    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new library office(s).")
    else:
        LOGGER.info("✅ No new library offices inserted. All offices already exist.")


def seed_publishers(session: Session, publishers_data: dict) -> None:
    """
    Core logic to seed publishers table.
    :param session: Active SQLAlchemy session.
    :param publishers_data: Dictionary with publisher_code as key and publisher_name as value.
    """
    inserted_count = 0
    
    for pub_code, pub_name in publishers_data.items():
        # Check if publisher exists
        check_sql = text("SELECT 1 FROM publishers WHERE code = :code")
        existing = session.execute(check_sql, {"code": pub_code}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Publisher '{pub_name}' already exists, skipping.")
            continue
        
        # Insert new publisher
        insert_sql = text("""
            INSERT INTO publishers (code, name)
            VALUES (:code, :name)
        """)
        session.execute(insert_sql, {
            "code": pub_code,
            "name": pub_name
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new publisher(s).")
    else:
        LOGGER.info("✅ No new publishers inserted. All publishers already exist.")


def seed_authors(session: Session, authors_data: dict) -> None:
    """
    Core logic to seed authors table.
    :param session: Active SQLAlchemy session.
    :param authors_data: Dictionary with author_code as key and author_name as value.
    """
    inserted_count = 0
    
    for author_code, author_name in authors_data.items():
        # Check if author exists
        check_sql = text("SELECT 1 FROM authors WHERE code = :code")
        existing = session.execute(check_sql, {"code": author_code}).scalar()
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
        LOGGER.info(f"✅ Seeded {inserted_count} new author(s).")
    else:
        LOGGER.info("✅ No new authors inserted. All authors already exist.")


def seed_status_codes(session: Session, status_codes_data: list) -> None:
    """
    Core logic to seed status_codes table.
    :param session: Active SQLAlchemy session.
    :param status_codes_data: List of tuples (code, category, description).
    """
    inserted_count = 0
    
    for code, category, desc in status_codes_data:
        # Check if status code exists
        check_sql = text("SELECT 1 FROM status_codes WHERE code = :code")
        existing = session.execute(check_sql, {"code": code}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Status code '{code}' already exists, skipping.")
            continue
        
        # Insert new status code
        insert_sql = text("""
            INSERT INTO status_codes (code, category, description, is_active)
            VALUES (:code, :category, :description, :is_active)
        """)
        session.execute(insert_sql, {
            "code": code,
            "category": category,
            "description": desc,
            "is_active": True
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new status code(s).")
    else:
        LOGGER.info("✅ No new status codes inserted. All status codes already exist.")


def seed_book_categories(session: Session, categories_data: list) -> None:
    """
    Core logic to seed book_categories table.
    :param session: Active SQLAlchemy session.
    :param categories_data: List of dictionaries with 'name' and 'description' keys.
    """
    inserted_count = 0
    
    for item in categories_data:
        # Check if category exists
        check_sql = text("SELECT 1 FROM book_categories WHERE name = :name")
        existing = session.execute(check_sql, {"name": item["name"]}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Book category '{item['name']}' already exists, skipping.")
            continue
        
        # Insert new category
        insert_sql = text("""
            INSERT INTO book_categories (name, description, is_active)
            VALUES (:name, :description, :is_active)
        """)
        session.execute(insert_sql, {
            "name": item["name"],
            "description": item["description"],
            "is_active": True
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new book category(ies).")
    else:
        LOGGER.info("✅ No new book categories inserted. All categories already exist.")


def seed_book_languages(session: Session, languages_data: list) -> None:
    """
    Core logic to seed book_languages table.
    :param session: Active SQLAlchemy session.
    :param languages_data: List of dictionaries with 'name' and 'description' keys.
    """
    inserted_count = 0
    
    for item in languages_data:
        # Check if language exists
        check_sql = text("SELECT 1 FROM book_languages WHERE language = :language")
        existing = session.execute(check_sql, {"language": item["name"]}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Book language '{item['name']}' already exists, skipping.")
            continue
        
        # Insert new language
        insert_sql = text("""
            INSERT INTO book_languages (language, description, is_active)
            VALUES (:language, :description, :is_active)
        """)
        session.execute(insert_sql, {
            "language": item["name"],
            "description": item["description"],
            "is_active": True
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new book language(s).")
    else:
        LOGGER.info("✅ No new book languages inserted. All languages already exist.")


def seed_subject_difficulty_tiers(session: Session, difficulty_data: list) -> None:
    """
    Core logic to seed subject_difficulty_tiers table.
    :param session: Active SQLAlchemy session.
    :param difficulty_data: List of dictionaries with tier details.
    """
    inserted_count = 0
    
    for item in difficulty_data:
        # Generate the name
        name = f"{item['difficulty_class'].upper()}"
        if item["difficulty_value"] is not None:
            name += f"-{item['difficulty_value']}"
        
        # Check if tier exists
        check_sql = text("SELECT 1 FROM subject_difficulty_tiers WHERE name = :name")
        existing = session.execute(check_sql, {"name": name}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Subject difficulty tier '{name}' already exists, skipping.")
            continue
        
        # Insert new tier
        insert_sql = text("""
            INSERT INTO subject_difficulty_tiers (tier, name, difficulty_class, difficulty_value, description, is_private, is_active)
            VALUES (:tier, :name, :difficulty_class, :difficulty_value, :description, :is_private, :is_active)
        """)
        session.execute(insert_sql, {
            "tier": item["tier"],
            "name": name,
            "difficulty_class": item["difficulty_class"],
            "difficulty_value": item["difficulty_value"],
            "description": item["description"],
            "is_private": item["is_private"],
            "is_active": True
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new subject difficulty tier(s).")
    else:
        LOGGER.info("✅ No new subject difficulty tiers inserted. All tiers already exist.")


def seed_spiritual_maturity_levels(session: Session, maturity_data: list) -> None:
    """
    Core logic to seed spiritual_maturity_levels table.
    :param session: Active SQLAlchemy session.
    :param maturity_data: List of dictionaries with maturity level details.
    """
    inserted_count = 0
    
    for item in maturity_data:
        # Check if maturity level exists
        check_sql = text("SELECT 1 FROM spiritual_maturity_levels WHERE code = :code")
        existing = session.execute(check_sql, {"code": item["code"]}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Spiritual maturity level '{item['code']}' already exists, skipping.")
            continue
        
        # Insert new maturity level
        insert_sql = text("""
            INSERT INTO spiritual_maturity_levels (code, title, weight, min_years, max_years, is_special_class, is_active, description)
            VALUES (:code, :title, :weight, :min_years, :max_years, :is_special_class, :is_active, :description)
        """)
        session.execute(insert_sql, {
            "code": item["code"],
            "title": item["title"],
            "weight": item["weight"],
            "min_years": item["min_years"],
            "max_years": item["max_years"],
            "is_special_class": item["is_special_class"],
            "is_active": True,
            "description": item["description"]
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new spiritual maturity level(s).")
    else:
        LOGGER.info("✅ No new spiritual maturity levels inserted. All levels already exist.")


def seed_library_users(session: Session, users_data: list) -> None:
    """
    Core logic to seed library_users table.
    :param session: Active SQLAlchemy session.
    :param users_data: List of dictionaries with user details.
    """
    inserted_count = 0
    
    for user in users_data:
        try:
            # Check if user exists by email or phone
            check_sql = text("""
                SELECT 1 FROM users 
                WHERE email = :email OR phone_number = :phone_number
            """)
            existing = session.execute(check_sql, {
                "email": user["email"],
                "phone_number": user["phone_number"]
            }).scalar()
            
            if existing:
                LOGGER.info(f"ℹ️ User '{user['first_name']} {user['last_name']}' already exists, skipping.")
                continue
            
            # Generate user_uuid and user_id (simplified version)
            import uuid
            user_uuid = str(uuid.uuid4())
            
            # Generate user_id based on office and date
            office_code = user["registered_at_office"]
            reg_date = utc_now()  # Use timezone utility
            office_tag = office_code[:3]  # Extract first 3 chars as tag
            month = f"{reg_date.month:02d}"
            year = f"{reg_date.year % 100:02d}"
            sequence = user.get("sequence_number", 1)
            user_id = f"{office_tag}{month}{year}{sequence:08d}"
            
            # Hash password (simplified - in real scenario should use proper hashing)
            from utils.security import generate_password_hash
            password_hash = generate_password_hash(user["password"])
            
            # Insert new user
            insert_sql = text("""
                INSERT INTO users (
                    user_uuid, user_id, first_name, last_name, email, phone_number, registration_date,
                    role, membership_type, address_line_1, address_line_2, city, state, 
                    country, postal_code, registered_at_office, password_hash, spiritual_maturity,
                    account_status, borrowed_books, fines_due, is_founder
                )
                VALUES (
                    :user_uuid, :user_id, :first_name, :last_name, :email, :phone_number, :registration_date,
                    :role, :membership_type, :address_line_1, :address_line_2, :city, :state,
                    :country, :postal_code, :registered_at_office, :password_hash, :spiritual_maturity,
                    :account_status, :borrowed_books, :fines_due, :is_founder
                )
            """)
            session.execute(insert_sql, {
                "user_uuid": user_uuid,
                "user_id": user_id,
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "email": user["email"],
                "phone_number": user["phone_number"],
                "registration_date": reg_date,
                "role": user["role"],
                "membership_type": user["membership_type"],
                "address_line_1": user["address_line_1"],
                "address_line_2": user.get("address_line_2"),
                "city": user["city"],
                "state": user["state"],
                "country": user["country"],
                "postal_code": user["postal_code"],
                "registered_at_office": user["registered_at_office"],
                "password_hash": password_hash,
                "spiritual_maturity": 5,  # Default
                "account_status": "UNVERIFIED",  # Default
                "borrowed_books": json.dumps([]),  # Empty list
                "fines_due": 0.0,
                "is_founder": False
            })
            session.flush()  # Flush this individual insert
            inserted_count += 1
        except Exception as e:
            LOGGER.warning(f"ℹ️ User '{user['first_name']} {user['last_name']}' creation failed: {e}")
            session.rollback()  # Rollback failed transaction
            continue
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new library user(s).")
    else:
        LOGGER.info("✅ No new library users inserted. All users already exist.")


def seed_books(session: Session, books_data: list) -> None:
    """
    Core logic to seed books table.
    :param session: Active SQLAlchemy session.
    :param books_data: List of tuples with book details.
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
            
            # Get next book number for author/publisher
            if author_code:
                num_sql = text("SELECT COALESCE(MAX(book_number), 0) + 1 FROM books WHERE author_code = :author_code")
                book_number = session.execute(num_sql, {"author_code": author_code}).scalar()
                id_prefix = author_code
            else:
                num_sql = text("SELECT COALESCE(MAX(book_number), 0) + 1 FROM books WHERE publisher_code = :publisher_code")
                book_number = session.execute(num_sql, {"publisher_code": publisher_code}).scalar()
                id_prefix = publisher_code
            
            book_id = f"{id_prefix}-{book_number:03d}"
            
            # Insert new book
            insert_sql = text("""
                INSERT INTO books (
                    book_uuid, book_id, book_number, isbn, title, author_code, publisher_code,
                    description, contents, price, category, language, base_difficulty,
                    first_publication_year, is_restricted_book
                )
                VALUES (
                    :book_uuid, :book_id, :book_number, :isbn, :title, :author_code, :publisher_code,
                    :description, :contents, :price, :category, :language, :base_difficulty,
                    :first_publication_year, :is_restricted_book
                )
            """)
            session.execute(insert_sql, {
                "book_uuid": book_uuid,
                "book_id": book_id,
                "book_number": book_number,
                "isbn": isbn_str,
                "title": title,
                "author_code": author_code,
                "publisher_code": publisher_code,
                "description": description,
                "contents": json.dumps(contents) if contents else None,
                "price": price,
                "category": category,
                "language": language,
                "base_difficulty": 1,  # Default
                "first_publication_year": first_publication_year,
                "is_restricted_book": False
            })
            inserted_count += 1
        except Exception as e:
            LOGGER.warning(f"ℹ️ Book with ISBN '{isbn}' creation failed: {e}")
            continue

    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new book(s).")
    else:
        LOGGER.info("✅ No new books inserted. All books already exist.")


def seed_book_copies(session: Session, copies_data: list) -> None:
    """
    Core logic to seed book_copies table.
    :param session: Active SQLAlchemy session.
    :param copies_data: List of tuples with copy details (book_id, branch_code, current_publication_year).
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
            copy_id = f"{branch_code.upper()}-{book_id}-{copy_number:04d}"
            
            # Get book's base difficulty
            diff_sql = text("SELECT base_difficulty FROM books WHERE book_id = :book_id")
            base_difficulty = session.execute(diff_sql, {"book_id": book_id}).scalar()
            if not base_difficulty:
                LOGGER.warning(f"ℹ️ Book '{book_id}' not found, skipping copy creation.")
                continue
            
            # Insert new copy
            added_on = utc_now()  # Use timezone utility
            
            insert_sql = text("""
                INSERT INTO book_copies (
                    copy_uuid, copy_id, book_id, branch_code, copy_number,
                    current_publication_year, contributer, added_on, copy_difficulty, is_available
                )
                VALUES (
                    :copy_uuid, :copy_id, :book_id, :branch_code, :copy_number,
                    :current_publication_year, :contributer, :added_on, :copy_difficulty, :is_available
                )
            """)
            session.execute(insert_sql, {
                "copy_uuid": copy_uuid,
                "copy_id": copy_id,
                "book_id": book_id,
                "branch_code": branch_code,
                "copy_number": copy_number,
                "current_publication_year": current_publication_year,
                "contributer": None,  # Default to NULL for optional field
                "added_on": added_on,
                "copy_difficulty": str(base_difficulty),  # Convert to string as per FK
                "is_available": True
            })
            inserted_count += 1
        except Exception as e:
            LOGGER.warning(f"ℹ️ Book copy '{book_id}-{branch_code}' creation failed: {e}")
            continue

    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new book copy(ies).")
    else:
        LOGGER.info("✅ No new book copies inserted. All copies already exist.")


def seed_referral_codes_sql(session: Session, referral_codes_data: list) -> None:
    """
    Core logic to seed referral_codes table.
    :param session: Active SQLAlchemy session.
    :param referral_codes_data: List of dictionaries with referral code details.
    """
    inserted_count = 0
    
    for referral in referral_codes_data:
        try:
            # Check if referral already exists for this phone number and owner
            check_sql = text("""
                SELECT 1 FROM referral_codes 
                WHERE code_owner = :code_owner AND invited_phone = :invited_phone
            """)
            existing = session.execute(check_sql, {
                "code_owner": referral["code_owner"],
                "invited_phone": referral["invited_phone"]
            }).scalar()
            
            if existing:
                LOGGER.info(f"ℹ️ Referral code for phone ending with {referral['invited_phone'][-2:]} by owner {referral['code_owner']} already exists, skipping.")
                continue
            
            # Insert new referral code
            insert_sql = text("""
                INSERT INTO referral_codes (code_owner, invited_phone, assigned_office, is_active, created_at)
                VALUES (:code_owner, :invited_phone, :assigned_office, :is_active, :created_at)
            """)
            session.execute(insert_sql, {
                "code_owner": referral["code_owner"],
                "invited_phone": referral["invited_phone"],
                "assigned_office": referral["assigned_office"],
                "is_active": referral["is_active"],
                "created_at": utc_now()
            })
            inserted_count += 1
        except Exception as e:
            LOGGER.warning(f"ℹ️ Referral code creation failed for phone ending with {referral['invited_phone'][-2:]}: {e}")
            continue
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new referral code(s).")
    else:
        LOGGER.info("✅ No new referral codes inserted. All referral codes already exist.")


# SQL-based seeding functions
def seed_roles_sql(session: Session, predefined_roles: dict) -> None:
    """
    SQL-based seeding for user_roles table.
    """
    inserted_count = 0
    for rank, (role_name, permissions) in predefined_roles.items():
        rank = int(rank)
        
        # Check if role exists
        check_sql = text("SELECT 1 FROM user_roles WHERE rank = :rank")
        existing = session.execute(check_sql, {"rank": rank}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Role '{role_name}' already exists, skipping.")
            continue
        
        # Insert new role
        insert_sql = text("""
            INSERT INTO user_roles (rank, role, permissions) 
            VALUES (:rank, :role, :permissions)
        """)
        session.execute(insert_sql, {
            "rank": rank,
            "role": role_name,
            "permissions": json.dumps(permissions)
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new role(s) via SQL.")
    else:
        LOGGER.info("✅ No new roles inserted via SQL. All roles already exist.")


def seed_memberships_sql(session: Session, predefined_memberships: dict) -> None:
    """
    SQL-based seeding for library_memberships table.
    """
    inserted_count = 0
    for rank, (membership, reg_fee, book_limit, days_count) in predefined_memberships.items():
        rank = int(rank)
        
        # Check if membership exists
        check_sql = text("SELECT 1 FROM library_memberships WHERE rank = :rank")
        existing = session.execute(check_sql, {"rank": rank}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Membership class '{membership}' already exists, skipping.")
            continue
        
        # Insert new membership
        insert_sql = text("""
            INSERT INTO library_memberships (rank, membership_title, borrowing_limit, borrow_duration_days, annual_fee)
            VALUES (:rank, :membership_title, :borrowing_limit, :borrow_duration_days, :annual_fee)
        """)
        session.execute(insert_sql, {
            "rank": rank,
            "membership_title": membership,
            "borrowing_limit": book_limit,
            "borrow_duration_days": days_count,
            "annual_fee": reg_fee
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new membership(s) via SQL.")
    else:
        LOGGER.info("✅ No new memberships inserted via SQL. All memberships already exist.")


def seed_library_offices_sql(session: Session, predefined_offices: dict) -> None:
    """
    SQL-based seeding for library_offices table.
    """
    inserted_count = 0
    
    for office_code, office_data in predefined_offices.items():
        # Check if office exists
        check_sql = text("SELECT 1 FROM library_offices WHERE office_code = :office_code")
        existing = session.execute(check_sql, {"office_code": office_code}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Library Office '{office_code}' already exists in '{office_data['city']}', skipping.")
            continue
        
        # Insert new office
        insert_sql = text("""
            INSERT INTO library_offices (office_code, office_tag, office_num, address, city, state, country, pincode, is_active)
            VALUES (:office_code, :office_tag, :office_num, :address, :city, :state, :country, :pincode, :is_active)
        """)
        session.execute(insert_sql, {
            "office_code": office_code,
            "office_tag": office_data['office_tag'],
            "office_num": office_data['office_num'],
            "address": office_data['address'],
            "city": office_data['city'],
            "state": office_data['state'],
            "country": office_data['country'],
            "pincode": office_data['pincode'],
            "is_active": True
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new library office(s) via SQL.")
    else:
        LOGGER.info("✅ No new library offices inserted via SQL. All offices already exist.")


def seed_publishers_sql(session: Session, publishers_data: dict) -> None:
    """
    SQL-based seeding for publishers table.
    """
    inserted_count = 0
    
    for pub_code, pub_name in publishers_data.items():
        # Check if publisher exists
        check_sql = text("SELECT 1 FROM publishers WHERE code = :code")
        existing = session.execute(check_sql, {"code": pub_code}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Publisher '{pub_name}' already exists, skipping.")
            continue
        
        # Insert new publisher
        insert_sql = text("""
            INSERT INTO publishers (code, name)
            VALUES (:code, :name)
        """)
        session.execute(insert_sql, {
            "code": pub_code,
            "name": pub_name
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new publisher(s) via SQL.")
    else:
        LOGGER.info("✅ No new publishers inserted via SQL. All publishers already exist.")


def seed_authors_sql(session: Session, authors_data: dict) -> None:
    """
    SQL-based seeding for authors table.
    """
    inserted_count = 0
    
    for author_code, author_name in authors_data.items():
        # Check if author exists
        check_sql = text("SELECT 1 FROM authors WHERE code = :code")
        existing = session.execute(check_sql, {"code": author_code}).scalar()
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


def seed_status_codes_sql(session: Session, status_codes_data: list) -> None:
    """
    SQL-based seeding for status_codes table.
    """
    inserted_count = 0
    
    for code, category, desc in status_codes_data:
        # Check if status code exists
        check_sql = text("SELECT 1 FROM status_codes WHERE code = :code")
        existing = session.execute(check_sql, {"code": code}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Status code '{code}' already exists, skipping.")
            continue
        
        # Insert new status code
        insert_sql = text("""
            INSERT INTO status_codes (code, category, description, is_active)
            VALUES (:code, :category, :description, :is_active)
        """)
        session.execute(insert_sql, {
            "code": code,
            "category": category,
            "description": desc,
            "is_active": True
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new status code(s) via SQL.")
    else:
        LOGGER.info("✅ No new status codes inserted via SQL. All status codes already exist.")


def seed_book_categories_sql(session: Session, categories_data: list) -> None:
    """
    SQL-based seeding for book_categories table.
    """
    inserted_count = 0
    
    for item in categories_data:
        # Check if category exists
        check_sql = text("SELECT 1 FROM book_categories WHERE name = :name")
        existing = session.execute(check_sql, {"name": item["name"]}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Book category '{item['name']}' already exists, skipping.")
            continue
        
        # Insert new category
        insert_sql = text("""
            INSERT INTO book_categories (name, description, is_active)
            VALUES (:name, :description, :is_active)
        """)
        session.execute(insert_sql, {
            "name": item["name"],
            "description": item["description"],
            "is_active": True
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new book category(ies) via SQL.")
    else:
        LOGGER.info("✅ No new book categories inserted via SQL. All categories already exist.")


def seed_book_languages_sql(session: Session, languages_data: list) -> None:
    """
    SQL-based seeding for book_languages table.
    """
    inserted_count = 0
    
    for item in languages_data:
        # Check if language exists
        check_sql = text("SELECT 1 FROM book_languages WHERE language = :language")
        existing = session.execute(check_sql, {"language": item["name"]}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Book language '{item['name']}' already exists, skipping.")
            continue
        
        # Insert new language
        insert_sql = text("""
            INSERT INTO book_languages (language, description, is_active)
            VALUES (:language, :description, :is_active)
        """)
        session.execute(insert_sql, {
            "language": item["name"],
            "description": item["description"],
            "is_active": True
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new book language(s) via SQL.")
    else:
        LOGGER.info("✅ No new book languages inserted via SQL. All languages already exist.")


def seed_subject_difficulty_tiers_sql(session: Session, difficulty_data: list) -> None:
    """
    SQL-based seeding for subject_difficulty_tiers table.
    """
    inserted_count = 0
    
    for item in difficulty_data:
        # Generate the name
        name = f"{item['difficulty_class'].upper()}"
        if item["difficulty_value"] is not None:
            name += f"-{item['difficulty_value']}"
        
        # Check if tier exists
        check_sql = text("SELECT 1 FROM subject_difficulty_tiers WHERE name = :name")
        existing = session.execute(check_sql, {"name": name}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Subject difficulty tier '{name}' already exists, skipping.")
            continue
        
        # Insert new tier
        insert_sql = text("""
            INSERT INTO subject_difficulty_tiers (tier, name, difficulty_class, difficulty_value, description, is_private, is_active)
            VALUES (:tier, :name, :difficulty_class, :difficulty_value, :description, :is_private, :is_active)
        """)
        session.execute(insert_sql, {
            "tier": item["tier"],
            "name": name,
            "difficulty_class": item["difficulty_class"],
            "difficulty_value": item["difficulty_value"],
            "description": item["description"],
            "is_private": item["is_private"],
            "is_active": True
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new subject difficulty tier(s) via SQL.")
    else:
        LOGGER.info("✅ No new subject difficulty tiers inserted via SQL. All tiers already exist.")


def seed_spiritual_maturity_levels_sql(session: Session, maturity_data: list) -> None:
    """
    SQL-based seeding for spiritual_maturity_levels table.
    """
    inserted_count = 0
    
    for item in maturity_data:
        # Check if maturity level exists
        check_sql = text("SELECT 1 FROM spiritual_maturity_levels WHERE code = :code")
        existing = session.execute(check_sql, {"code": item["code"]}).scalar()
        if existing:
            LOGGER.info(f"ℹ️ Spiritual maturity level '{item['code']}' already exists, skipping.")
            continue
        
        # Insert new maturity level
        insert_sql = text("""
            INSERT INTO spiritual_maturity_levels (code, title, weight, min_years, max_years, is_special_class, is_active, description)
            VALUES (:code, :title, :weight, :min_years, :max_years, :is_special_class, :is_active, :description)
        """)
        session.execute(insert_sql, {
            "code": item["code"],
            "title": item["title"],
            "weight": item["weight"],
            "min_years": item["min_years"],
            "max_years": item["max_years"],
            "is_special_class": item["is_special_class"],
            "is_active": True,
            "description": item["description"]
        })
        inserted_count += 1
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new spiritual maturity level(s) via SQL.")
    else:
        LOGGER.info("✅ No new spiritual maturity levels inserted via SQL. All levels already exist.")


def seed_library_users_sql(session: Session, users_data: list) -> None:
    """
    SQL-based seeding for users table.
    """
    inserted_count = 0
    
    for user in users_data:
        try:
            # Check if user exists by email or phone
            check_sql = text("""
                SELECT 1 FROM users 
                WHERE email = :email OR phone_number = :phone_number
            """)
            existing = session.execute(check_sql, {
                "email": user["email"],
                "phone_number": user["phone_number"]
            }).scalar()
            
            if existing:
                LOGGER.info(f"ℹ️ User '{user['first_name']} {user['last_name']}' already exists, skipping.")
                continue
            
            # Generate user_uuid and user_id (simplified version)
            import uuid
            user_uuid = str(uuid.uuid4())
            
            # Generate user_id based on office and date
            office_code = user["registered_at_office"]
            reg_date = utc_now()  # Use timezone utility
            office_tag = office_code[:3]  # Extract first 3 chars as tag
            month = f"{reg_date.month:02d}"
            year = f"{reg_date.year % 100:02d}"
            sequence = user.get("sequence_number", 1)
            user_id = f"{office_tag}{month}{year}{sequence:08d}"
            
            # Hash password (simplified - in real scenario should use proper hashing)
            from utils.security import generate_password_hash
            password_hash = generate_password_hash(user["password"])
            
            # Insert new user
            insert_sql = text("""
                INSERT INTO users (
                    user_uuid, user_id, first_name, last_name, email, phone_number, registration_date,
                    role, membership_type, address_line_1, address_line_2, city, state, 
                    country, postal_code, registered_at_office, password_hash, spiritual_maturity,
                    account_status, borrowed_books, fines_due, is_founder
                )
                VALUES (
                    :user_uuid, :user_id, :first_name, :last_name, :email, :phone_number, :registration_date,
                    :role, :membership_type, :address_line_1, :address_line_2, :city, :state,
                    :country, :postal_code, :registered_at_office, :password_hash, :spiritual_maturity,
                    :account_status, :borrowed_books, :fines_due, :is_founder
                )
            """)
            session.execute(insert_sql, {
                "user_uuid": user_uuid,
                "user_id": user_id,
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "email": user["email"],
                "phone_number": user["phone_number"],
                "registration_date": reg_date,
                "role": user["role"],
                "membership_type": user["membership_type"],
                "address_line_1": user["address_line_1"],
                "address_line_2": user.get("address_line_2"),
                "city": user["city"],
                "state": user["state"],
                "country": user["country"],
                "postal_code": user["postal_code"],
                "registered_at_office": user["registered_at_office"],
                "password_hash": password_hash,
                "spiritual_maturity": 5,  # Default
                "account_status": "UNVERIFIED",  # Default
                "borrowed_books": json.dumps([]),  # Empty list
                "fines_due": 0.0,
                "is_founder": False
            })
            session.flush()  # Flush this individual insert
            inserted_count += 1
        except Exception as e:
            LOGGER.warning(f"ℹ️ User '{user['first_name']} {user['last_name']}' creation failed: {e}")
            session.rollback()  # Rollback failed transaction
            continue
    
    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new library user(s) via SQL.")
    else:
        LOGGER.info("✅ No new library users inserted via SQL. All users already exist.")


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
            
            # Get next book number for author/publisher
            if author_code:
                num_sql = text("SELECT COALESCE(MAX(book_number), 0) + 1 FROM books WHERE author_code = :author_code")
                book_number = session.execute(num_sql, {"author_code": author_code}).scalar()
                id_prefix = author_code
            else:
                num_sql = text("SELECT COALESCE(MAX(book_number), 0) + 1 FROM books WHERE publisher_code = :publisher_code")
                book_number = session.execute(num_sql, {"publisher_code": publisher_code}).scalar()
                id_prefix = publisher_code
            
            book_id = f"{id_prefix}-{book_number:03d}"
            
            # Insert new book
            insert_sql = text("""
                INSERT INTO books (
                    book_uuid, book_id, book_number, isbn, title, author_code, publisher_code,
                    description, contents, price, category, language, base_difficulty,
                    first_publication_year, is_restricted_book
                )
                VALUES (
                    :book_uuid, :book_id, :book_number, :isbn, :title, :author_code, :publisher_code,
                    :description, :contents, :price, :category, :language, :base_difficulty,
                    :first_publication_year, :is_restricted_book
                )
            """)
            session.execute(insert_sql, {
                "book_uuid": book_uuid,
                "book_id": book_id,
                "book_number": book_number,
                "isbn": isbn_str,
                "title": title,
                "author_code": author_code,
                "publisher_code": publisher_code,
                "description": description,
                "contents": json.dumps(contents) if contents else None,
                "price": price,
                "category": category,
                "language": language,
                "base_difficulty": 1,  # Default
                "first_publication_year": first_publication_year,
                "is_restricted_book": False
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
            copy_id = f"{branch_code.upper()}-{book_id}-{copy_number:04d}"
            
            # Get book's base difficulty
            diff_sql = text("SELECT base_difficulty FROM books WHERE book_id = :book_id")
            base_difficulty = session.execute(diff_sql, {"book_id": book_id}).scalar()
            if not base_difficulty:
                LOGGER.warning(f"ℹ️ Book '{book_id}' not found, skipping copy creation.")
                continue
            
            # Insert new copy
            added_on = utc_now()  # Use timezone utility
            
            insert_sql = text("""
                INSERT INTO book_copies (
                    copy_uuid, copy_id, book_id, branch_code, copy_number,
                    current_publication_year, contributer, added_on, copy_difficulty, is_available
                )
                VALUES (
                    :copy_uuid, :copy_id, :book_id, :branch_code, :copy_number,
                    :current_publication_year, :contributer, :added_on, :copy_difficulty, :is_available
                )
            """)
            session.execute(insert_sql, {
                "copy_uuid": copy_uuid,
                "copy_id": copy_id,
                "book_id": book_id,
                "branch_code": branch_code,
                "copy_number": copy_number,
                "current_publication_year": current_publication_year,
                "contributer": None,  # Default to NULL for optional field
                "added_on": added_on,
                "copy_difficulty": str(base_difficulty),  # Convert to string as per FK
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
