"""
Pytest configuration and fixtures for CRJ Youth E-Library tests.
"""

import pytest
from flask import Flask
from flask_cors import CORS
from models.library_user import LibraryUser
from utils.security import argon2
from utils.mail_setup import mail
from routes.auth_routes import auth_bp
from constants.config import JWT_SECRET_KEY
from utils.security import generate_password_hash


@pytest.fixture(scope='function')
def db_session():
    """Create a database session using the actual database for testing."""
    from utils.psql_database import get_database_session
    
    # Use the actual database session
    with get_database_session() as session:
        yield session


@pytest.fixture(scope='function')
def app():
    """Create Flask app instance for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Mail configuration for testing
    app.config['MAIL_SUPPRESS_SEND'] = True
    app.config['MAIL_BACKEND'] = 'locmem'
    
    # Argon2 Configuration (lighter for testing)
    app.config['ARGON2_TIME_COST'] = 1
    app.config['ARGON2_MEMORY_COST'] = 1024  # 1 MB for testing
    app.config['ARGON2_PARALLELISM'] = 1
    app.config['ARGON2_HASH_LENGTH'] = 32
    app.config['ARGON2_SALT_LENGTH'] = 16
    
    # Initialize extensions
    argon2.init_app(app)
    mail.init_app(app)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    
    return app


@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def admin_user_data():
    """Admin user test data from seed file."""
    return {
        "first_name": "Admin",
        "last_name": "User", 
        "email": "admin@textgpt.live",
        "phone_number": "1111111111",
        "password": "J4j>$U13&]Cn",
        "role": 1,
        "membership_type": 1
    }


@pytest.fixture(scope='function')  
def admin_user(db_session, admin_user_data):
    """Create admin user in database."""
    # Use a unique test email to avoid conflicts
    test_email = "test-admin@textgpt.live"
    test_phone = "9999999999"
    
    # Check if test admin user already exists
    existing_user = db_session.query(LibraryUser).filter_by(email=test_email).first()
    if existing_user:
        # Update password hash and ensure ACTIVE status
        existing_user.password_hash = generate_password_hash(admin_user_data["password"])
        existing_user.account_status = 'ACTIVE'
        db_session.commit()
        return existing_user
    
    # Use the create_user method to ensure proper ID generation and validation
    admin = LibraryUser.create_user(
        session=db_session,
        first_name=admin_user_data["first_name"],
        last_name=admin_user_data["last_name"],
        email=test_email,
        phone_number=test_phone,
        password=admin_user_data["password"],
        address_line_1="Test Admin Address Line 1",
        city="Test City",
        state="Test State", 
        country="Test Country",
        postal_code="123456",
        registered_at_office="DHN01",  # Use test office code
        role=admin_user_data["role"],
        membership_type=admin_user_data["membership_type"],
        spiritual_maturity=3,  # Using existing weight 3 (Mature believers 5+)
        sequence_number=50000001  # Test sequence number that doesn't conflict with seed data
    )
    
    # Ensure ACTIVE status for tests
    admin.account_status = 'ACTIVE'
    db_session.commit()
    return admin


 