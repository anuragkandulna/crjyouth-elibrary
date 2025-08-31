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
    rate_limit, nonce_store, get_device_info, session_required, session_only_required
)
from models.session import Session
from models.exceptions import DuplicateUserError, WeakPasswordError
from utils.timezone_utils import utc_now, utc_datetime

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


@auth_bp.route('/api/v1/debug/cookies', methods=['GET'])
def debug_cookies():
    """Debug endpoint to check cookies."""
    return jsonify({
        "cookies": dict(request.cookies),
        "headers": dict(request.headers),
        "session_token": request.cookies.get('session_token')
    }), 200


@auth_bp.route('/api/v1/debug/db-pool', methods=['GET'])
def debug_db_pool():
    """Debug endpoint to check database connection pool status."""
    try:
        from utils.sqlite_database import get_database_connection
        db_connection = get_database_connection()
        pool_stats = db_connection.get_pool_stats()
        
        return jsonify({
            "database_pool": pool_stats,
            "database_file": "data/crjyouth_library.db",
            "status": "healthy"
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


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
@rate_limit(5, 60)  # 5 requests per minute
def login():
    """Login endpoint with session management"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        nonce = data.get('nonce')
        device_id = data.get('device_id', 'unknown')
        user_agent = request.headers.get('User-Agent', 'unknown')

        # Validate required parameters
        if not all([email, password, nonce]):
            return jsonify({"error": "Missing required parameters: email, password, nonce"}), 400

        # Validate nonce
        if not validate_nonce(nonce):
            return jsonify({"error": "Invalid or expired nonce"}), 400

        with get_db_session() as session:
            # Find user by email
            user = session.query(User).filter_by(email=email).first()
            if not user:
                return jsonify({"error": "Invalid email or password"}), 401

            # Verify password
            if not user.check_password(password):
                return jsonify({"error": "Invalid email or password"}), 401

            # Check if user already has an active session for this device and user agent
            existing_session = Session.get_session_by_device_and_agent(session, user.user_uuid, device_id, user_agent)
            
            if existing_session:
                # Refresh existing session
                if Session.refresh_session(session, existing_session.session_id, ttl_minutes=240):
                    LOGGER.info(f"Refreshed existing session {existing_session.session_id} for user {user.email}")
                    
                    response = make_response(jsonify({
                        "message": "Login successful (session refreshed)",
                        "user": {
                            "user_id": user.user_id,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "is_admin": user.is_admin
                        },
                        "session_id": existing_session.session_id,
                        "expires_at": existing_session.expires_at.isoformat() if existing_session.expires_at else None
                    }))
                    
                    response.set_cookie(
                        'session_token',
                        existing_session.session_id,
                        httponly=True,
                        samesite='Lax',
                        secure=False,
                        path='/',
                        domain=None,
                        expires=existing_session.expires_at
                    )
                    
                    return response, 200
                else:
                    LOGGER.error(f"Failed to refresh session {existing_session.session_id}")
                    return jsonify({"error": "Failed to refresh session"}), 500
            else:
                # Create new session with limit management
                new_session = Session.create_session_with_limits(session, user.user_uuid, device_id, user_agent, ttl_minutes=240)
                
                if not new_session:
                    return jsonify({"error": "Failed to create session"}), 500

                LOGGER.info(f"Created new session {new_session.session_id} for user {user.email}")

                response = make_response(jsonify({
                    "message": "Login successful",
                    "user": {
                        "user_id": user.user_id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "is_admin": user.is_admin
                    },
                    "session_id": new_session.session_id,
                    "expires_at": new_session.expires_at.isoformat() if new_session.expires_at else None
                }))
                
                response.set_cookie(
                    'session_token',
                    new_session.session_id,
                    httponly=True,
                    samesite='Lax',
                    secure=False,
                    path='/',
                    domain=None,
                    expires=new_session.expires_at
                )
                
                return response, 200

    except Exception as ex:
        LOGGER.error(f"Login failed: {ex}")
        return jsonify({"error": "Login failed"}), 500


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
@session_only_required
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
            
            # Handle timezone-naive datetime objects
            try:
                created_at_str = user_session.created_at.isoformat()
            except Exception:
                created_at_str = str(user_session.created_at)
                
            try:
                expires_at_str = user_session.expires_at.isoformat()
            except Exception:
                expires_at_str = str(user_session.expires_at)
                
            try:
                last_refreshed_str = user_session.last_refreshed.isoformat() if user_session.last_refreshed else None
            except Exception:
                last_refreshed_str = str(user_session.last_refreshed) if user_session.last_refreshed else None
                
            return jsonify({
                "session_id": user_session.session_id,
                "device_id": user_session.device_id,
                "created_at": created_at_str,
                "expires_at": expires_at_str,
                "last_refreshed": last_refreshed_str,
                "time_until_expiry": user_session.time_until_expiry().total_seconds() if user_session.time_until_expiry() else None,
                "user": {
                    "user_id": g.current_user['user_id'],
                    "first_name": g.current_user['first_name'],
                    "last_name": g.current_user['last_name'],
                    "email": g.current_user['email'],
                    "is_admin": g.current_user['is_admin']
                }
            }), 200
            
    except Exception as ex:
        error_response, status_code = handle_auth_error(ex, "Session info retrieval failed")
        return jsonify(error_response), status_code


@auth_bp.route('/api/v1/auth/refresh', methods=['POST'])
@session_only_required
def refresh_session():
    """Refresh the current session"""
    try:
        with get_db_session() as session:
            session_id = g.session_id
            user_uuid = g.current_user['user_uuid']
            
            # Get current session
            session_obj = Session.get_session_by_id(session, session_id)
            if not session_obj:
                return jsonify({"error": "Session not found"}), 404
            
            # Check if session is close to expiry (within 2 minutes)
            now = utc_now()
            expires_at = session_obj.expires_at
            time_until_expiry = (expires_at - now).total_seconds()
            
            if time_until_expiry <= 120:  # 2 minutes threshold
                # Refresh the session
                if Session.refresh_session(session, session_id, ttl_minutes=240):  # 4 hours
                    session_obj = Session.get_session_by_id(session, session_id)
                    
                    # Log the refresh
                    from utils.session_manager import SessionManager
                    # Handle timezone-naive datetime objects
                    try:
                        new_expires_at_str = session_obj.expires_at.isoformat()
                    except Exception:
                        new_expires_at_str = str(session_obj.expires_at)
                        
                    SessionManager.log_session_event("refresh", {
                        "user_uuid": user_uuid,
                        "session_id": session_id,
                        "device_id": session_obj.device_id,
                        "user_agent": session_obj.user_agent
                    }, {
                        "time_until_expiry_before": time_until_expiry,
                        "new_expires_at": new_expires_at_str
                    })
                    
                    # Handle timezone-naive datetime objects
                    try:
                        expires_at_str = session_obj.expires_at.isoformat()
                    except Exception:
                        expires_at_str = str(session_obj.expires_at)
                        
                    response = make_response(jsonify({
                        "message": "Session refreshed successfully",
                        "expires_at": expires_at_str
                    }))
                    
                    # Update the cookie
                    response.set_cookie(
                        'session_token',
                        session_id,
                        httponly=True,
                        samesite='Lax',
                        secure=False,
                        path='/',
                        domain=None,
                        expires=session_obj.expires_at
                    )
                    
                    return response, 200
                else:
                    return jsonify({"error": "Failed to refresh session"}), 500
            else:
                # Handle timezone-naive datetime objects
                try:
                    expires_at_str = session_obj.expires_at.isoformat()
                except Exception:
                    expires_at_str = str(session_obj.expires_at)
                    
                return jsonify({
                    "message": "Session does not need refresh",
                    "expires_at": expires_at_str,
                    "time_until_expiry": time_until_expiry
                }), 200
                
    except Exception as ex:
        LOGGER.error(f"Session refresh failed: {ex}")
        return jsonify({"error": "Session refresh failed"}), 500

@auth_bp.route('/api/v1/logout', methods=['POST'])
@rate_limit(max_requests=10, window_minutes=5)
def logout():
    """Logout current session."""
    try:
        # Get session token from cookie
        session_token = request.cookies.get('session_token')
        
        if session_token:
            try:
                with get_db_session() as session:
                    # Try to invalidate the session if it exists
                    Session.invalidate_session(session, session_token)
                    LOGGER.info(f"Session '{session_token}' invalidated during logout.")
            except Exception as ex:
                # Session might not exist or be invalid, that's okay for logout
                LOGGER.warning(f"Session invalidation failed during logout: {ex}")
        
        # Always clear session cookie regardless of session state
        response = make_response(jsonify({"message": "Logged out successfully"}))
        response.set_cookie('session_token', '', expires=0, secure=False, path='/')
        
        LOGGER.info("Logout completed successfully.")
        return response
        
    except Exception as ex:
        LOGGER.error(f"Logout failed: {ex}")
        # Even if there's an error, clear the cookie
        response = make_response(jsonify({"message": "Logged out successfully"}))
        response.set_cookie('session_token', '', expires=0, secure=False, path='/')
        return response


@auth_bp.route('/api/v1/logout-all', methods=['POST'])
def logout_all_sessions():
    """Logout from all active sessions for the user"""
    try:
        # Get session token from cookie
        session_token = request.cookies.get('session_token')
        
        if session_token:
            try:
                with get_db_session() as session:
                    # Try to get session info to find user_uuid
                    session_obj = Session.get_session_by_id(session, session_token)
                    if session_obj:
                        user_uuid = session_obj.user_uuid
                        
                        # Invalidate all sessions for the user
                        count = Session.invalidate_all_user_sessions(session, user_uuid)
                        
                        # Log the logout all event
                        from utils.session_manager import SessionManager
                        SessionManager.log_session_event("logout_all", {
                            "user_uuid": user_uuid,
                            "session_id": session_token,
                            "device_id": "all",
                            "user_agent": "all"
                        }, {
                            "sessions_invalidated": count
                        })
                        
                        LOGGER.info(f"Logged out from {count} sessions for user {user_uuid}")
                    else:
                        LOGGER.warning("Session not found during logout-all")
            except Exception as ex:
                # Session might not exist or be invalid, that's okay for logout
                LOGGER.warning(f"Session invalidation failed during logout-all: {ex}")
        
        # Always clear session cookie regardless of session state
        response = make_response(jsonify({
            "message": "Logged out from all sessions successfully"
        }))
        response.set_cookie('session_token', '', expires=0, secure=False, path='/')
        
        return response, 200
        
    except Exception as ex:
        LOGGER.error(f"Logout all failed: {ex}")
        # Even if there's an error, clear the cookie
        response = make_response(jsonify({
            "message": "Logged out from all sessions successfully"
        }))
        response.set_cookie('session_token', '', expires=0, secure=False, path='/')
        return response, 200
