"""
Pytest configuration and fixtures for CRJ Youth E-Library tests.
"""

import pytest
from flask import Flask
from flask_cors import CORS
from models.user import User
from models.session import Session  
from utils.security import argon2
from utils.mail_setup import mail
from routes.auth_routes import auth_bp
from constants.config import JWT_SECRET_KEY
from utils.security import generate_password_hash
from datetime import datetime, timedelta, timezone


@pytest.fixture(scope='function')
def db_session():
    """Create a database session using the actual database for testing."""
    from utils.sqlite_database import get_database_connection
    from models import Base  # Import models package to ensure all models are loaded
    
    # Get database connection and recreate all tables with current schema
    db_conn = get_database_connection()
    
    # Drop all tables and recreate them to ensure current schema
    Base.metadata.drop_all(bind=db_conn.engine)
    Base.metadata.create_all(bind=db_conn.engine)

    # Use the actual database session
    session = db_conn.get_session()
    try:
        yield session
    finally:
        session.close()


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
    existing_user = db_session.query(User).filter_by(email=test_email).first()
    if existing_user:
        # Update password hash, ensure ACTIVE status, and set admin role
        existing_user.password_hash = generate_password_hash(admin_user_data["password"])
        existing_user.is_active = True
        existing_user.is_admin = True
        db_session.commit()
        return existing_user

    # Use the create_user method to ensure proper ID generation and validation
    admin = User.create_user(
        session=db_session,
        first_name=admin_user_data["first_name"],
        last_name=admin_user_data["last_name"],
        email=test_email,
        password=admin_user_data["password"],
    )

    # Set admin role for the created user
    admin.is_admin = True
    db_session.commit()
    return admin


@pytest.fixture(scope='function')
def member_user(db_session, admin_user_data):
    """Create a member user in database."""
    # Use a unique test email to avoid conflicts
    test_email = "test-member@textgpt.live"

    # Check if test member user already exists
    existing_user = db_session.query(User).filter_by(email=test_email).first()
    if existing_user:
        # Update password hash and ensure ACTIVE status
        existing_user.password_hash = generate_password_hash(admin_user_data["password"])
        existing_user.is_active = True
        existing_user.is_admin = False
        db_session.commit()
        return existing_user

    # Create member user
    member = User.create_user(
        session=db_session,
        first_name="Member",
        last_name="User",
        email=test_email,
        password=admin_user_data["password"],
    )

    # Ensure member is not admin
    member.is_admin = False
    db_session.commit()
    return member


@pytest.fixture(scope='function')
def session(db_session, admin_user):
    """Create a session for the admin user."""
    test_session = Session(
        user_uuid=admin_user.user_uuid,
        device_id='test_device_001',
        user_agent='pytest-test-agent',
        ip_address='127.0.0.1',
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        is_active=True
    )
    db_session.add(test_session)
    db_session.commit()
    return test_session
 