from functools import wraps
from flask import Blueprint, request, jsonify, make_response
from flask_mail import Message
import jwt
import datetime
import secrets
import re
from models.library_user import LibraryUser
from models.exceptions import DuplicateUserError, WeakPasswordError
from constants.config import JWT_SECRET_KEY, CRJYOUTH_MAIL_NO_REPLY, LOG_LEVEL
from constants.constants import APP_LOG_FILE
from utils.psql_database import db_session
from utils.my_logger import CustomLogger
from utils.security import generate_password_hash, is_strong_password
from utils.mail_setup import mail


# Defined variables
nonce_store = {}
user_token_cache = {}
auth_bp = Blueprint('auth_bp', __name__)
LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=APP_LOG_FILE).get_logger()


# -------------------- Utility Functions -------------------- #
def generate_nonce():
    return secrets.token_urlsafe(64)


def validate_nonce(nonce):
    if nonce in nonce_store:
        del nonce_store[nonce]
        return True
    return False


def validate_strong_password(password, name_fields):
    if len(password) < 12:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    for field in name_fields:
        if field and field.lower() in password.lower():
            return False
    return True


def generate_login_token(user):
    payload = {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.user_role.role,
        "exp": datetime.datetime.now() + datetime.timedelta(hours=12)
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    user_token_cache[user.email] = token
    return token


# -------------------- Decorators -------------------- #
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


def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            token = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else None

            if not token:
                return jsonify({"error": "Token is missing!"}), 401

            try:
                decoded_data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
                role = decoded_data.get("role")

                if not role or role not in allowed_roles:
                    return jsonify({"error": "Access forbidden!"}), 403

                request.user = decoded_data
                return f(*args, **kwargs)

            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token has expired!"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token!"}), 401

        return wrapper
    return decorator


# -------------------- Routes -------------------- #
@auth_bp.route('/api/v1/nonce', methods=['GET'])
def get_nonce():
    nonce = generate_nonce()
    nonce_store[nonce] = True
    return jsonify({"nonce": nonce}), 200


@auth_bp.route('/api/v1/account/check-password-strength', methods=['POST'])
def check_password_strength():
    data = request.json
    try:
        # Verify if password1 and password2 matches
        password1 = data['password1']
        password2 = data['password2']
        if password1 != password2:
            raise WeakPasswordError("Password and confirm password do not match.")

        if not (12 <= len(password1) <= 20 and 12 <= len(password2) <= 20):
            raise WeakPasswordError("Password length must be between 12 and 20 characters.")

        # Verify if password policy meets
        first_name = data['first_name']
        last_name = data['last_name']
        phone_number = data['phone_number']
        email = data.get('email', None)

        if not is_strong_password(password1, first_name, last_name, phone_number, email):
            raise WeakPasswordError("Password must not contain name, email or phone number.")

        return jsonify({"message": "Password meets security policy requirements."}), 200

    except WeakPasswordError as ex:
        return jsonify({"error": f"Password policy error. Reason: {ex}"}), 406
    except Exception as ex:
        LOGGER.error(f"Password strength check failed: {ex}")
        return jsonify({"error": "Bad request!"}), 400


@auth_bp.route('/api/v1/account/register', methods=['POST'])
def register():
    data = request.json
    try:
        new_user = LibraryUser.create_user(
            db_session,
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data.get('email', None),
            phone_number=data['phone_number'],
            password=data['password'],
            membership_type=data.get('membership')
        )
        LOGGER.info(f"User '{new_user.user_id}' registration successfully.")
        return jsonify({"message": f"User registered successfully. Your user id is {new_user.user_id}"}), 201

    except DuplicateUserError as ex:
        db_session.rollback()
        LOGGER.error(f"User already exists error: {ex}")
        return jsonify({"error": "Email or phone number exists."}), 409
    except WeakPasswordError as ex:
        db_session.rollback()
        LOGGER.error(f"Weak password error: {ex}")
        return jsonify({"error": f"Password policy error. Reason: {ex}"}), 406
    except Exception as ex:
        db_session.rollback()
        LOGGER.error(f"User registration failed: {ex}")
        return jsonify({"error": "Bad request!"}), 400
    finally:
        db_session.close()


@auth_bp.route('/api/v1/account/login', methods=['POST'])
def login():
    data = request.json
    try:
        if not validate_nonce(data.get('nonce', '')):
            return jsonify({"error": "Invalid or expired nonce."}), 401

        user = db_session.query(LibraryUser).filter_by(email=data['email'], account_status='ACTIVE').first()
        if not user or not user.check_password(data['password']):
            return jsonify({"error": "Invalid email or password."}), 401

        token = user_token_cache.get(user.email) or generate_login_token(user)
        response = make_response(jsonify({"message": "Login successful."}))
        response.set_cookie('session_token', token, httponly=True, samesite='Strict', secure=True)
        LOGGER.info(f"User '{user.user_id}' logged in successfully.")
        return response

    except Exception as ex:
        db_session.rollback()
        LOGGER.error(f"Login failed: {ex}")
        return jsonify({"error": "Login failed due to internal error."}), 500
    finally:
        db_session.close()


@auth_bp.route('/api/v1/account/reset-password', methods=['PUT'])
@token_required
def reset_password_authenticated():
    data = request.json
    try:
        user_email = request.user['email']
        user = db_session.query(LibraryUser).filter_by(email=user_email).first()

        password1 = data.get("password1")
        password2 = data.get("password2")

        if password1 != password2:
            return jsonify({"error": "Passwords do not match."}), 400

        if not validate_strong_password(password1, [user.first_name, user.last_name, user.email, user.phone_number]):
            return jsonify({"error": "Password does not meet policy requirements."}), 400

        user.password_hash = generate_password_hash(password1)
        db_session.commit()
        LOGGER.info(f"User '{user.user_id}' successfully reset password.")
        return jsonify({"message": "Password updated successfully."}), 200

    except Exception as ex:
        db_session.rollback()
        LOGGER.error(f"Password reset failed: {ex}")
        return jsonify({"error": "Password reset failed."}), 500
    finally:
        db_session.close()


@auth_bp.route('/api/v1/account/password-reset-request', methods=['POST'])
def password_reset_request():
    data = request.json
    try:
        email = data.get('email')
        reset_token = jwt.encode({
            "email": email,
            "exp": datetime.datetime.now() + datetime.timedelta(minutes=30)
        }, JWT_SECRET_KEY, algorithm="HS256")

        # Send email to user
        msg = Message(
            subject="CRJ Youth Library Password Reset",
            recipients=[email],
            body=f"To reset your password, visit: https://crjyouth.in/reset-password?token={reset_token}",
            sender=CRJYOUTH_MAIL_NO_REPLY
        )
        mail.send(msg)

        LOGGER.info(f"Password reset token email sent.")
        return jsonify({"message": "If your email is registered, a reset link has been sent."}), 200

    except Exception as ex:
        LOGGER.error(f"Password reset request failed: {ex}")
        return jsonify({"error": "Password reset failed."}), 400


@auth_bp.route('/api/v1/account/password-reset-confirm', methods=['PUT'])
def password_reset_confirm():
    data = request.json
    try:
        token = data.get("token")
        password1 = data.get("password1")
        password2 = data.get("password2")

        if password1 != password2:
            return jsonify({"error": "Passwords do not match."}), 400

        decoded_data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        email = decoded_data.get("email")
        user = db_session.query(LibraryUser).filter_by(email=email).first()

        if not validate_strong_password(password1, [user.first_name, user.last_name, user.email, user.phone_number]):
            return jsonify({"error": "Password does not meet policy requirements."}), 400

        user.password_hash = generate_password_hash(password1)
        db_session.commit()
        LOGGER.info(f"User '{user.user_id}' password successfully updated via reset.")
        return jsonify({"message": "Password reset successful."}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Reset token expired."}), 400
    except Exception as ex:
        db_session.rollback()
        LOGGER.error(f"Password reset failed: {ex}")
        return jsonify({"error": "Password reset failed."}), 400
    finally:
        db_session.close()
