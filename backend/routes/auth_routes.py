from flask import Blueprint, request, jsonify, make_response, g
from flask_mail import Message
import jwt
import datetime
from typing import Dict, Tuple
from models.user import User
from models.exceptions import DuplicateUserError, WeakPasswordError
from constants.config import JWT_SECRET_KEY, CRJYOUTH_MAIL_NO_REPLY, LOG_LEVEL
from constants.constants import (
    AUTH_LOG_FILE, TOKEN_EXPIRY_HOURS, PASSWORD_RESET_EXPIRY_MINUTES,
    LOGIN_RATE_LIMIT_REQUESTS, LOGIN_RATE_LIMIT_WINDOW_MINUTES,
    REGISTER_RATE_LIMIT_REQUESTS, REGISTER_RATE_LIMIT_WINDOW_MINUTES,
    PASSWORD_RESET_RATE_LIMIT_REQUESTS, PASSWORD_RESET_RATE_LIMIT_WINDOW_MINUTES,
)
from utils.sqlite_database import get_db_session
from utils.my_logger import CustomLogger
from utils.security import verify_strong_password
from utils.mail_setup import mail
from utils.route_utils import (
    generate_nonce, validate_nonce, validate_request_data,
    rate_limit, nonce_store, get_device_info, session_required
)
from models.session import Session
from models.exceptions import DuplicateUserError, WeakPasswordError

# Defined variables
user_token_cache = {}
auth_bp = Blueprint('auth_bp', __name__)
LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=AUTH_LOG_FILE).get_logger()


# -------------------- Utility Functions -------------------- #
def generate_login_token(user: User) -> str:
    """Generate JWT token for user login."""
    payload = {
        "user_id": user.user_id,
        "email": user.email,
        "role": "ADMIN" if user.is_admin else "USER",
        "exp": datetime.datetime.now() + datetime.timedelta(hours=TOKEN_EXPIRY_HOURS)
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    user_token_cache[user.email] = token
    return token


def handle_auth_error(error: Exception, context: str, status_code: int = 500) -> Tuple[Dict[str, str], int]:
    """Centralized error handling."""
    LOGGER.error(f"{context}: {error}")
    
    if isinstance(error, DuplicateUserError):
        return {"error": "Email already exists"}, 409
    elif isinstance(error, WeakPasswordError):
        return {"error": f"Password policy error: {error}"}, 406
    elif "does not exist" in str(error):
        return {"error": "User not found"}, 404
    else:
        return {"error": "Internal server error"}, status_code


# -------------------- Routes -------------------- #
@auth_bp.route('/api/v1/nonce', methods=['GET'])
@rate_limit(max_requests=10, window_minutes=5)
def get_nonce():
    nonce = generate_nonce()
    nonce_store[nonce] = True
    return jsonify({"nonce": nonce}), 200


@auth_bp.route('/api/v1/check-password-strength', methods=['POST'])
@rate_limit(max_requests=10, window_minutes=5)
def check_password_strength():
    data = request.get_json()
    
    is_valid, error_msg = validate_request_data(data, ['password1', 'password2'])
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    try:
        password1 = data['password1']
        password2 = data['password2']
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        email = data.get('email', '')

        is_strong, reason = verify_strong_password(
            password1=password1, password2=password2,
            first_name=first_name, last_name=last_name,
            email=email
        )

        if not is_strong:
            raise WeakPasswordError(reason)

        return jsonify({"message": "Password meets security policy requirements."}), 200

    except Exception as ex:
        error_response, status_code = handle_auth_error(ex, "Password strength check failed", 400)
        return jsonify(error_response), status_code


@auth_bp.route('/api/v1/register', methods=['POST'])
@rate_limit(max_requests=REGISTER_RATE_LIMIT_REQUESTS, window_minutes=REGISTER_RATE_LIMIT_WINDOW_MINUTES)
def register():
    data = request.get_json()
    required_fields = ['first_name', 'last_name', 'email', 'password']
    is_valid, error_msg = validate_request_data(data, required_fields)
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    try:
        with get_db_session() as session:
            user = User.create_user(
                session=session,
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data.get('email'),
                password=data['password']
            )
            LOGGER.info(f"User registered: {user.user_id}")
            return jsonify({
                "message": "User registered successfully",
                "user_id": user.user_id,
                "role": "ADMIN" if user.is_admin else "USER"
            }), 201
    except Exception as ex:
        error_response, status_code = handle_auth_error(ex, "User registration failed")
        return jsonify(error_response), status_code


@auth_bp.route('/api/v1/login', methods=['POST'])
@rate_limit(max_requests=LOGIN_RATE_LIMIT_REQUESTS, window_minutes=LOGIN_RATE_LIMIT_WINDOW_MINUTES)
def login():
    data = request.get_json()
    
    is_valid, error_msg = validate_request_data(data, ['password'])
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    if not data.get('email'):
        return jsonify({
            "error": "Email is required"
        }), 400
    
    try:
        if not validate_nonce(data.get('nonce', '')):
            return jsonify({"error": "Invalid or expired nonce"}), 401

        with get_db_session() as session:
            user = None
            if data.get('email'):
                user = session.query(User).filter_by(
                    email=data['email'], 
                    is_active=True
                ).first()

            if not user or not user.check_password(data['password']):
                return jsonify({
                    "error": "Invalid credentials"
                }), 401

            # Generate JWT token
            token = user_token_cache.get(user.email) or generate_login_token(user)
            
            # Get device information
            device_id, user_agent = get_device_info()
            ip_address = request.remote_addr
            
            # Create user session
            user_session = Session.create_session(
                session=session,
                user_uuid=user.user_uuid, 
                device_id=device_id or 'unknown',
                user_agent=user_agent,
                ip_address=ip_address,
                ttl_minutes=TOKEN_EXPIRY_HOURS * 60
            )
            
            response = make_response(jsonify({
                "message": "Login successful",
                "user_id": user.user_id,
                "role": "ADMIN" if user.is_admin else "USER",
                "session_expires_at": user_session.expires_at.isoformat()
            }))
            
            # Set session cookie instead of JWT token
            response.set_cookie(
                'session_token', 
                user_session.session_id, 
                httponly=True, 
                samesite='Strict', 
                secure=True,
                expires=user_session.expires_at
            )
            
            LOGGER.info(f"User '{user.user_id}' logged in successfully with session '{user_session.session_id}'.")
            return response

    except Exception as ex:
        error_response, status_code = handle_auth_error(ex, "Login failed", 500)
        return jsonify(error_response), status_code


@auth_bp.route('/api/v1/account/reset-password', methods=['PUT'])
@session_required
@rate_limit(max_requests=PASSWORD_RESET_RATE_LIMIT_REQUESTS, window_minutes=PASSWORD_RESET_RATE_LIMIT_WINDOW_MINUTES)
def reset_password_authenticated():
    data = request.get_json()
    
    required_fields = ['old_password', 'new_password1', 'new_password2']
    is_valid, error_msg = validate_request_data(data, required_fields)
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    try:
        old_password = data['old_password']
        new_password1 = data['new_password1']
        new_password2 = data['new_password2']

        user_email = g.current_user['email']
        
        with get_db_session() as session:
            user = session.query(User).filter_by(email=user_email).first()

            if not user or not user.check_password(old_password):
                return jsonify({
                    "error": "Invalid old password"
                }), 401

            is_strong, reason = verify_strong_password(
                password1=new_password1, password2=new_password2,
                first_name=user.first_name, last_name=user.last_name,
                email=user.email or ''
            )
            if not is_strong:
                LOGGER.error(f"Weak password for user '{user.user_id}': {reason}")
                raise WeakPasswordError(reason)

            User.update_user_password(
                session=session,
                email=user.email,
                password=new_password1
            )
            
            # Invalidate all other sessions except current one for security
            all_sessions = Session.get_active_sessions(session, user.user_uuid)
            current_session_id = g.session_id
            
            for user_session in all_sessions:
                if user_session.session_id != current_session_id:
                    Session.invalidate_session(session, user_session.session_id)    
            
            LOGGER.info(f"User '{user.user_id}' changed password successfully. Other sessions invalidated.")
            return jsonify({"message": "Password changed successfully. Other active sessions have been logged out."}), 200

    except Exception as ex:
        error_response, status_code = handle_auth_error(ex, "Password change failed")
        return jsonify(error_response), status_code


@auth_bp.route('/api/v1/password-reset-request', methods=['POST'])
@rate_limit(max_requests=PASSWORD_RESET_RATE_LIMIT_REQUESTS, window_minutes=PASSWORD_RESET_RATE_LIMIT_WINDOW_MINUTES)
def password_reset_request():
    data = request.get_json()
    
    is_valid, error_msg = validate_request_data(data, ['email'])
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    try:
        email = data['email']
        reset_token = jwt.encode({
            "email": email,
            "exp": datetime.datetime.now() + datetime.timedelta(minutes=PASSWORD_RESET_EXPIRY_MINUTES)
        }, JWT_SECRET_KEY, algorithm="HS256")

        msg = Message(
            subject="CRJ Youth Library Password Reset",
            recipients=[email],
            body=f"To reset your password, visit: https://crjyouth.in/reset-password?token={reset_token}",
            sender=CRJYOUTH_MAIL_NO_REPLY
        )
        mail.send(msg)

        LOGGER.info(f"Password reset email sent to {email}.")
        return jsonify({"message": "If your email is registered, a reset link has been sent."}), 200

    except Exception as ex:
        error_response, status_code = handle_auth_error(ex, "Password reset request failed", 400)
        return jsonify(error_response), status_code


@auth_bp.route('/api/v1/password-reset-confirm', methods=['PUT'])
@rate_limit(max_requests=PASSWORD_RESET_RATE_LIMIT_REQUESTS, window_minutes=PASSWORD_RESET_RATE_LIMIT_WINDOW_MINUTES)
def password_reset_confirm():
    data = request.get_json()
    
    required_fields = ['token', 'password1', 'password2']
    is_valid, error_msg = validate_request_data(data, required_fields)
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    try:
        token = data["token"]
        password1 = data["password1"]
        password2 = data["password2"]

        if password1 != password2:
            return jsonify({
                "error": "Passwords do not match"
            }), 400

        decoded_data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        email = decoded_data.get("email")
        
        with get_db_session() as session:
            user = session.query(User).filter_by(email=email).first()
            
            if not user:
                return jsonify({
                    "error": "User not found"
                }), 404

            is_strong, reason = verify_strong_password(
                password1=password1, password2=password2,
                first_name=user.first_name, last_name=user.last_name,
                email=user.email or ''
            )
            if not is_strong:
                LOGGER.error(f"Weak password for user '{user.user_id}': {reason}")
                raise WeakPasswordError(reason)

            User.update_user_password(
                session=session,
                email=user.email,
                password=password1
            )
            
            # Invalidate all existing sessions for security
            Session.deactivate_all_sessions(session, user.user_uuid)
            
            LOGGER.info(f"User '{user.user_id}' reset password successfully. All sessions invalidated.")
            return jsonify({"message": "Password reset successfully. Please login again."}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({
            "error": "Reset token expired"
        }), 400
    except Exception as ex:
        error_response, status_code = handle_auth_error(ex, "Password reset failed", 400)
        return jsonify(error_response), status_code


# -------------------- Session Management Routes -------------------- #
@auth_bp.route('/api/v1/session/info', methods=['GET'])
@session_required
@rate_limit(max_requests=20, window_minutes=5)
def get_session_info():
    """Get current session information."""
    try:
        session_id = g.session_id
        
        with get_db_session() as session:
            user_session = Session.get_session_by_id(session, session_id)
            
            if not user_session:
                return jsonify({
                    "error": "Session not found",
                    "requires_login": True
                }), 404
            
            return jsonify({
                "session_id": user_session.session_id,
                "device_id": user_session.device_id,
                "created_at": user_session.created_at.isoformat(),
                "expires_at": user_session.expires_at.isoformat(),
                "last_refreshed": user_session.last_refreshed.isoformat() if user_session.last_refreshed else None,
                "time_until_expiry": user_session.time_until_expiry().total_seconds() if user_session.time_until_expiry() else None,
                "user_id": g.current_user['user_id']
            }), 200
            
    except Exception as ex:
        error_response, status_code = handle_auth_error(ex, "Session info retrieval failed")
        return jsonify(error_response), status_code


@auth_bp.route('/api/v1/session/refresh', methods=['POST'])
@session_required
@rate_limit(max_requests=10, window_minutes=5)
def refresh_session():
    """Manually refresh current session."""
    try:
        session_id = g.session_id
        
        with get_db_session() as session:
            if Session.refresh_session(session, session_id):
                user_session = Session.get_session_by_id(session, session_id)
                LOGGER.info(f"Session '{session_id}' refreshed manually by user '{g.current_user['user_id']}'.")
                return jsonify({
                    "message": "Session refreshed successfully",
                    "new_expires_at": user_session.expires_at.isoformat()
                }), 200
            else:
                return jsonify({
                    "error": "Session refresh failed",
                    "requires_login": True
                }), 400
                
    except Exception as ex:
        error_response, status_code = handle_auth_error(ex, "Session refresh failed")
        return jsonify(error_response), status_code


@auth_bp.route('/api/v1/logout', methods=['POST'])
@session_required
@rate_limit(max_requests=10, window_minutes=5)
def logout():
    """Logout current session."""
    try:
        session_id = g.session_id
        
        with get_db_session() as session:
            Session.invalidate_session(session, session_id)
            
        # Clear session cookie
        response = make_response(jsonify({"message": "Logged out successfully"}))
        response.set_cookie('session_token', '', expires=0)
        
        LOGGER.info(f"User '{g.current_user['user_id']}' logged out. Session '{session_id}' invalidated.")
        return response
        
    except Exception as ex:
        error_response, status_code = handle_auth_error(ex, "Logout failed")
        return jsonify(error_response), status_code


@auth_bp.route('/api/v1/logout-all', methods=['POST'])
@session_required
@rate_limit(max_requests=5, window_minutes=10)
def logout_all():
    """Logout from all sessions."""
    try:
        user_id = g.current_user['user_id']
        
        with get_db_session() as session:
            # Get user to find user_uuid
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                return jsonify({"error": "User not found"}), 404
            count = Session.deactivate_all_sessions(session, user.user_uuid)
        response = make_response(jsonify({"message": "Logged out from all sessions"}))
        response.set_cookie('session_token', '', expires=0)
        
        LOGGER.info(f"User '{user_id}' logged out from all sessions.")
        return response
        
    except Exception as ex:
        error_response, status_code = handle_auth_error(ex, "Logout all failed")
        return jsonify(error_response), status_code
