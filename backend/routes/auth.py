from functools import wraps
from flask import Blueprint, request, jsonify
import jwt
import datetime
import random
import string
from models.library_user import LibraryUser
from utils.psql_database import db_session
from constants.config import JWT_SECRET_KEY
from utils.my_logger import CustomLogger


# Defined variables
nonce_store = {}
auth_bp = Blueprint('auth_bp', __name__)
LOGGER = CustomLogger(__name__, level=20, log_file='crjyouth_application.log').get_logger()


# Generate a unique nonce
def generate_nonce():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


# Validate nonce (Prevent replay attacks)
def validate_nonce(nonce):
    if nonce in nonce_store:
        del nonce_store[nonce]  # Invalidate nonce after use
        return True
    return False


# Generate JWT token
def generate_token(user):
    """Generate JWT token for a user."""
    payload = {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.user_role.role,
        "exp": datetime.datetime.now() + datetime.timedelta(hours=12),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")


# Middleware for token validation
def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else None

        if not token:
            return jsonify({"error": "Token is missing!"}), 401

        try:
            decoded_data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            request.user = decoded_data
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token!"}), 401

        return f(*args, **kwargs)
    return wrapper


# Role-based access control (RBAC) decorator
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Token is missing!"}), 401

            token = auth_header.split(" ")[1]

            try:
                decoded_data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
                role = decoded_data.get("role")

                if not role:
                    return jsonify({"error": "Role not found in token!"}), 401

                if role not in allowed_roles:
                    return jsonify({"error": "Access forbidden!"}), 403

                request.user = decoded_data  # Attach user info to the request object
                LOGGER.info(f"Access granted for role '{role}' to endpoint '{f.__name__}'")
                return f(*args, **kwargs)

            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token has expired!"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token!"}), 401

        return wrapper
    return decorator


# Route to fetch a nonce
@auth_bp.route('/api/v1/nonce', methods=['GET'])
def get_nonce():
    nonce = generate_nonce()
    nonce_store[nonce] = True  # Store nonce temporarily
    return jsonify({"nonce": nonce}), 200


# Register API
@auth_bp.route('/api/v1/register', methods=['POST'])
@role_required(['Admin', 'Moderator'])
def register():
    data = request.json
    try:
        new_user = LibraryUser.create_user(
            db_session,
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone_number=data.get('phone_number'),
            password=data.get('password'),
            membership_type=data.get('membership')
        )
        return jsonify({"message": f"User registered successfully: {new_user.user_id}"}), 201
    except Exception as ex:
        db_session.rollback()
        LOGGER.error(f"User registration failed: {ex}")
        return jsonify({"error": "Bad request!"}), 400
    finally:
        db_session.close()


# Login API
@auth_bp.route('/api/v1/login', methods=['POST'])
def login():
    data = request.json

    try:
        # Validate nonce if used
        if not validate_nonce(nonce=data.get('nonce', '')):
            return jsonify({"error": "Invalid or expired nonce."}), 401

        # Fetch user by email
        user = db_session.query(LibraryUser).filter_by(email=data['email'], account_status='ACTIVE').first()
        if not user:
            return jsonify({"error": "User not found."}), 404

        # Check password using ORM method
        if not user.check_password(data['password']):
            return jsonify({"error": "Invalid email or password."}), 401

        # Generate auth token
        token = generate_token(user)
        LOGGER.info(f"User '{user.email}' logged in successfully.")
        return jsonify({"message": "Login successful.", "token": token}), 200

    except Exception as ex:
        db_session.rollback()
        LOGGER.error(f"Login failed: {ex}")
        return jsonify({"error": "Login failed due to an internal error."}), 500

    finally:
        db_session.close()


# Protected API (example)
@auth_bp.route('/api/v1/protected', methods=['GET'])
@token_required
def protected_route():
    user_data = request.user
    return jsonify({"message": "Welcome!", "user": user_data}), 200


# Role-protected API (example)
@auth_bp.route('/api/v1/admin', methods=['GET'])
@token_required
@role_required([1])
def admin_route():
    return jsonify({"message": "Welcome, Admin!"}), 200
