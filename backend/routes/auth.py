from functools import wraps
from flask import Blueprint, request, jsonify, make_response
from flask_mail import Message
import jwt
import datetime
import secrets
from models.library_user import LibraryUser
from models.exceptions import DuplicateUserError, WeakPasswordError
from constants.config import JWT_SECRET_KEY, CRJYOUTH_MAIL_NO_REPLY, LOG_LEVEL
from constants.constants import APP_LOG_FILE
from utils.psql_database import db_session
from utils.my_logger import CustomLogger
from utils.security import generate_password_hash, verify_strong_password
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


@auth_bp.route('/api/v1/check-password-strength', methods=['POST'])
def check_password_strength():
    data = request.json
    try:
        password1 = data['password1']
        password2 = data['password2']
        first_name = data.get('first_name', None)
        last_name = data.get('last_name', None)
        phone_number = data.get('phone_number', None)
        email = data.get('email', None)

        is_strong, reason = verify_strong_password(
            password1=password1, password2=password2,
            first_name=first_name, last_name=last_name,
            email=email, phone_number=phone_number
        )

        if not is_strong:
            raise WeakPasswordError(reason)

        return jsonify({"message": "Password meets security policy requirements."}), 200

    except WeakPasswordError as ex:
        return jsonify({"error": f"Password policy error. Reason: {ex}"}), 406
    except Exception as ex:
        LOGGER.error(f"Password strength check failed: {ex}")
        return jsonify({"error": "Bad request!"}), 400


@auth_bp.route('/api/v1/register', methods=['POST'])
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


@auth_bp.route('/api/v1/login', methods=['POST'])
def login():
    data = request.json
    try:
        if not validate_nonce(data.get('nonce', '')):
            return jsonify({"error": "Unauthorized."}), 401

        if data.get('phone_number', None):
            user = db_session.query(LibraryUser).filter_by(phone_number=data['phone_number'], account_status='ACTIVE').first()
        else:
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
        old_password = data['old_password']
        new_password1 = data['new_password1']
        new_password2 = data['new_password2']

        if 'email' in data:
            user = db_session.query(LibraryUser).filter_by(email=data['email']).first()
        else:
            user = db_session.query(LibraryUser).filter_by(phone_number=data['phone_number']).first()

        if not user or not user.check_password(old_password):
            return jsonify({"error": "Invalid old password."}), 401

        # Verify if password meets security policy requirements
        is_strong, reason = verify_strong_password(
            password1=new_password1, password2=new_password2, first_name=user.first_name,
            last_name=user.last_name, email=user.email, phone_number=user.phone_number
        )
        if not is_strong:
            LOGGER.error(f"Weak password for user '{user.user_id}': {reason}")
            raise WeakPasswordError(reason)

        user.update_user_password(phone_number=user.phone_number, password=new_password1)
        LOGGER.info(f"User {user.user_id} password changed successfully.")
        return jsonify({"message": "Password changed successfully."}), 200

    except Exception as ex:
        db_session.rollback()
        LOGGER.error(f"Password reset failed: {ex}")
        return jsonify({"error": "Password reset failed."}), 500
    finally:
        db_session.close()


@auth_bp.route('/api/v1/password-reset-request', methods=['POST'])
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
        LOGGER.error(f"Password reset request bad request: {ex}")
        return jsonify({"error": "Bad request."}), 400


@auth_bp.route('/api/v1/password-reset-confirm', methods=['PUT'])
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

        # Verify if password meets security policy requirements
        is_strong, reason = verify_strong_password(
            password1=password1, password2=password2, first_name=user.first_name,
            last_name=user.last_name, email=user.email, phone_number=user.phone_number
        )
        if not is_strong:
            LOGGER.error(f"Weak password for user '{user.user_id}': {reason}")
            raise WeakPasswordError(reason)

        user.update_user_password(phone_number=user.phone_number, password=password1)
        LOGGER.info(f"User {user.user_id} password reset successfully.")
        return jsonify({"message": "Password reset successfully."}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Reset token expired."}), 400
    except Exception as ex:
        db_session.rollback()
        LOGGER.error(f"Password reset failed due to: {ex}")
        return jsonify({"error": "Bad request."}), 400
    finally:
        db_session.close()
