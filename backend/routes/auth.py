from flask import Blueprint, request, jsonify
import jwt
import datetime
import random
import string
from models.library_user import LibraryUser
from utils.psql_database import get_session

# Secret key for JWT
SECRET_KEY = "your_secret_key"
# Store nonces for validation
nonce_store = {}

# Flask Blueprint for user-related APIs
auth_bp = Blueprint('auth_bp', __name__)


# Generate a unique nonce
def generate_nonce():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


# Validate nonce (Prevent replay attacks)
def validate_nonce(nonce):
    if nonce in nonce_store:
        del nonce_store[nonce]  # Invalidate nonce after use
        return True
    return False


# Middleware for token validation
def token_required(f):
    def wrapper(*args, **kwargs):
        token = None

        # Extract token from the Authorization header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing!"}), 401

        try:
            # Decode and verify the token
            decoded_data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user = decoded_data  # Attach user data to the request
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token!"}), 401

        return f(*args, **kwargs)

    wrapper.__name__ = f.__name__
    return wrapper


# Role-based access control (RBAC) decorator
def role_required(allowed_roles):
    def decorator(f):
        def wrapper(*args, **kwargs):
            token = None
            if 'Authorization' in request.headers:
                token = request.headers['Authorization'].split(" ")[1]

            if not token:
                return jsonify({"error": "Token is missing!"}), 401

            try:
                decoded_data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                if decoded_data["role"] not in allowed_roles:
                    return jsonify({"error": "Access forbidden!"}), 403
                request.user = decoded_data
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token has expired!"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token!"}), 401

            return f(*args, **kwargs)

        wrapper.__name__ = f.__name__
        return wrapper
    return decorator


# Generate JWT token
def generate_token(user):
    """Generate JWT token for a user."""
    payload = {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.user_role.role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


# Route to fetch a nonce
@auth_bp.route('/api/v1/nonce', methods=['GET'])
def get_nonce():
    nonce = generate_nonce()
    nonce_store[nonce] = True  # Store nonce temporarily
    return jsonify({"nonce": nonce}), 200


# Register API
@auth_bp.route('/api/v1/register', methods=['POST'])
def register():
    session = get_session()
    data = request.json
    try:
        user = LibraryUser(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone_number=data.get('phone_number'),
            role=data.get('role', 3)  # Default to Member role
        )
        user.set_password(data['password'])  # Hash the password
        session.add(user)
        session.commit()
        return jsonify({"message": "User registered successfully."}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


# Login API
@auth_bp.route('/api/v1/login', methods=['POST'])
def login():
    session = get_session()
    data = request.json

    try:
        # Validate nonce
        if not validate_nonce(nonce=data['nonce']):
            return jsonify({"error": "Invalid or expired nonce."}), 401
        
        # Query user if exists
        user = session.query(LibraryUser).filter_by(email=data['email']).first()
        if not user:
            return jsonify({"error": "User not found."}), 404

        # Verify user 
        if user and user.check_password(data['password']):
            token = generate_token(user)
            return jsonify({"message": "Login successful.", "token": token}), 200
        
        return jsonify({"error": "Invalid email or password."}), 401

    finally:
        session.close()


# Protected API (example)
@auth_bp.route('/protected', methods=['GET'])
@token_required
def protected_route():
    user_data = request.user
    return jsonify({"message": "Welcome!", "user": user_data}), 200


# Role-protected API (example)
@auth_bp.route('/admin', methods=['GET'])
@token_required
@role_required(["Admin"])
def admin_route():
    return jsonify({"message": "Welcome, Admin!"}), 200
