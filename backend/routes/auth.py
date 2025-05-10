from functools import wraps
from flask import Blueprint, request, jsonify, make_response
from flask_mail import Mail, Message
from email.mime.text import MIMEText
import jwt
import datetime
import secrets
import re
from models.library_user import LibraryUser
from utils.psql_database import db_session
from constants.config import JWT_SECRET_KEY, CRJYOUTH_MAIL_SUPPORT, LOG_LEVEL
from constants.constants import APP_LOG_FILE
from utils.my_logger import CustomLogger
from utils.security import generate_password_hash, check_password_hash

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
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12)
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


@auth_bp.route('/api/v1/account/register', methods=['POST'])
@role_required(['Admin', 'Moderator'])
def register():
    data = request.json
    try:
        password = data.get('password')
        if not validate_strong_password(password, [data['first_name'], data['last_name'], data['email'], data.get('phone_number', '')]):
            return jsonify({"error": "Password does not meet policy requirements."}), 400

        new_user = LibraryUser.create_user(
            db_session,
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone_number=data.get('phone_number'),
            password=password,
            membership_type=data.get('membership')
        )
        return jsonify({"message": f"User registered successfully: {new_user.user_id}"}), 201
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
        LOGGER.info(f"User '{user.email}' logged in successfully.")
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
        LOGGER.info(f"User '{user.email}' successfully reset password.")
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
        secure_token = secrets.token_urlsafe(64)
        reset_token = jwt.encode({
            "email": email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }, JWT_SECRET_KEY, algorithm="HS256")

        # Send email
        msg = Message(
            subject="CRJ Youth Library Password Reset",
            recipients=[email],
            body=f"To reset your password, visit: https://crjyouth.in/reset-password?token={reset_token}",
            sender=CRJYOUTH_MAIL_SUPPORT
        )
        mail.send(msg)

        LOGGER.info(f"Password reset token generated and emailed to: {email}")
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
        LOGGER.info(f"User '{email}' password successfully updated via reset.")
        return jsonify({"message": "Password reset successful."}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Reset token expired."}), 400
    except Exception as ex:
        db_session.rollback()
        LOGGER.error(f"Password reset failed: {ex}")
        return jsonify({"error": "Password reset failed."}), 400
    finally:
        db_session.close()


@auth_bp.route('/test', methods=['POST'])
def email_test():
    data = request.json
    try:
        email = data['email']
        msg = Message(
            subject="TEST EMAIL",
            recipients=[email],
            body="test email. ignore",
            sender=CRJYOUTH_MAIL_SUPPORT
        )
        mail.send(msg)
        LOGGER.info("Test email sent.")
        return jsonify({'message': 'Test email sent'}), 200
        
    except Exception as ex:
        LOGGER.error(f'Test email failed: {ex}')
        return jsonify({'error': 'Test email failed'}), 400
