from functools import wraps
from flask import request, jsonify, g
import jwt
import datetime
import secrets
import time
from typing import Optional, Dict, Any, Tuple
from constants.config import JWT_SECRET_KEY
from constants.constants import (
    DEFAULT_RATE_LIMIT_REQUESTS, DEFAULT_RATE_LIMIT_WINDOW_MINUTES
)
from models.session import Session
from utils.sqlite_database import get_db_session


# Global storage for rate limiting and nonce
nonce_store: Dict[str, bool] = {}
request_counts: Dict[str, list] = {}  # Simple rate limiting storage
nonce_cleanup_time = time.time()  # Track last cleanup time


# -------------------- Utility Functions -------------------- #
def generate_nonce() -> str:
    """Generate a secure nonce for authentication."""
    return secrets.token_urlsafe(64)


def validate_nonce(nonce: str) -> bool:
    """Validate and consume a nonce."""
    if nonce in nonce_store:
        del nonce_store[nonce]
        return True
    return False


def validate_request_data(data: Optional[Dict], required_fields: list) -> Tuple[bool, str]:
    """Validate request JSON data and required fields."""
    if not data:
        return False, "Request body must be valid JSON"
    
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            return False, f"'{field}' is required and cannot be empty"
    
    return True, ""


def decode_jwt_token(token: Optional[str]) -> Tuple[Optional[Dict], Optional[str]]:
    """Decode JWT token and return payload or error message."""
    if not token:
        return None, "Token is missing"
    
    try:
        decoded_data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return decoded_data, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"


def extract_token_from_header(auth_header: Optional[str]) -> Optional[str]:
    """Extract token from Authorization header."""
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ")[1] if len(auth_header.split(" ")) == 2 else None


def check_rate_limit(endpoint: str, max_requests: int = DEFAULT_RATE_LIMIT_REQUESTS, window_minutes: int = DEFAULT_RATE_LIMIT_WINDOW_MINUTES) -> bool:
    """Simple rate limiting check with cleanup."""
    global nonce_cleanup_time
    
    now = datetime.datetime.now()
    current_time = time.time()
    key = f"{request.remote_addr}:{endpoint}"
    
    # Cleanup old data periodically (every 5 minutes)
    if current_time - nonce_cleanup_time > 300:  # 5 minutes
        cleanup_old_data(window_minutes)
        nonce_cleanup_time = current_time
    
    if key not in request_counts:
        request_counts[key] = []
    
    # Clean old requests for this specific key
    request_counts[key] = [req_time for req_time in request_counts[key] 
                          if now - req_time < datetime.timedelta(minutes=window_minutes)]
    
    if len(request_counts[key]) >= max_requests:
        return False
    
    request_counts[key].append(now)
    return True


def cleanup_old_data(window_minutes: int):
    """Clean up old rate limiting and nonce data to prevent memory leaks."""
    now = datetime.datetime.now()
    cutoff_time = now - datetime.timedelta(minutes=window_minutes)
    
    # Clean up old rate limiting data
    keys_to_remove = []
    for key, requests in request_counts.items():
        # Remove empty request lists
        if not requests:
            keys_to_remove.append(key)
            continue
        
        # Remove old requests
        request_counts[key] = [req_time for req_time in requests 
                              if req_time > cutoff_time]
        
        # Remove keys with no remaining requests
        if not request_counts[key]:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del request_counts[key]
    
    # Clean up old nonces (older than 10 minutes)
    nonce_cutoff = now - datetime.timedelta(minutes=10)
    nonces_to_remove = []
    for nonce, timestamp in nonce_store.items():
        if isinstance(timestamp, datetime.datetime) and timestamp < nonce_cutoff:
            nonces_to_remove.append(nonce)
    
    for nonce in nonces_to_remove:
        del nonce_store[nonce]


def validate_status_transition(current_status: str, target_status: str) -> bool:
    """Validate if status transition is allowed."""
    valid_transitions = {
        'PENDING': ['APPROVED', 'REJECTED'],
        'APPROVED': ['OPEN', 'REJECTED'],
        'OPEN': ['CLOSED', 'OVERDUE'],
        'OVERDUE': ['CLOSED', 'ESCALATED'],
        'CLOSED': ['ESCALATED'],
        'ESCALATED': ['CLOSED'],
        'REJECTED': []  # Terminal state
    }
    
    return target_status in valid_transitions.get(current_status, [])


def get_device_info() -> Tuple[Optional[str], Optional[str]]:
    """Extract device information from request headers."""
    user_agent = request.headers.get('User-Agent')
    device_id = request.headers.get('X-Device-ID') or request.headers.get('Device-ID')
    
    # If no device ID provided, generate one from User-Agent and IP
    if not device_id and user_agent:
        import hashlib
        ip_address = request.remote_addr or 'unknown'
        device_id = hashlib.md5(f"{user_agent}:{ip_address}".encode()).hexdigest()[:16]
    
    return device_id, user_agent


def validate_session(session_id: str) -> Tuple[bool, Optional[str]]:
    """Validate if a session is active and not expired."""
    if not session_id:
        return False, "Session ID is missing"
    
    try:
        with get_db_session() as session:
            if Session.is_session_valid(session, session_id):
                return True, None
            else:
                return False, "Session has expired or is invalid"
    except Exception as ex:
        return False, f"Session validation error: {str(ex)}"


def get_session_from_request() -> Optional[str]:
    """Extract session ID from request (cookie or header)."""
    # Try cookie first
    session_id = request.cookies.get('session_token')
    if session_id:
        return session_id
    
    # Try header
    session_id = request.headers.get('X-Session-ID') or request.headers.get('Session-ID')
    return session_id


def refresh_user_session(session_id: str) -> bool:
    """Refresh a user session if it's valid."""
    if not session_id:
        return False
    
    try:
        with get_db_session() as session:
            return Session.refresh_session(session, session_id)
    except Exception:
        return False


# -------------------- Decorators -------------------- #
def token_required(f):
    """Decorator to require valid JWT token."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = extract_token_from_header(auth_header)
        
        decoded_data, error_msg = decode_jwt_token(token)
        if error_msg or not decoded_data:
            return jsonify({"error": error_msg or "Invalid token"}), 401
        
        g.current_user = decoded_data
        return f(*args, **kwargs)
    return wrapper


def session_required(f):
    """Decorator to require valid session along with JWT token."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        # First validate JWT token
        auth_header = request.headers.get('Authorization', '')
        token = extract_token_from_header(auth_header)
        
        decoded_data, error_msg = decode_jwt_token(token)
        if error_msg or not decoded_data:
            return jsonify({
                "error": error_msg or "Invalid token",
                "requires_login": True
            }), 401
        
        # Then validate session
        session_id = get_session_from_request()
        if not session_id:
            return jsonify({
                "error": "Session not found. Please login again.",
                "requires_login": True
            }), 401
        
        is_valid, session_error = validate_session(session_id)
        if not is_valid:
            return jsonify({
                "error": session_error or "Session expired. Please login again.",
                "requires_login": True
            }), 401
        
        # Refresh session on successful validation
        refresh_user_session(session_id)
        
        g.current_user = decoded_data
        g.session_id = session_id
        return f(*args, **kwargs)
    return wrapper


def session_only_required(f):
    """Decorator to require valid session only (no JWT required)."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Get session from request
        session_id = get_session_from_request()
        
        if not session_id:
            return jsonify({
                "error": "Session not found. Please login again.",
                "requires_login": True
            }), 401
        
        # Validate session
        is_valid, session_error = validate_session(session_id)
        
        if not is_valid:
            return jsonify({
                "error": session_error or "Session expired. Please login again.",
                "requires_login": True
            }), 401
        
        # Get user information from session
        try:
            with get_db_session() as session:
                session_obj = Session.get_session_by_id(session, session_id)
                if not session_obj:
                    return jsonify({
                        "error": "Invalid session. Please login again.",
                        "requires_login": True
                    }), 401
                
                # Get user information from database
                from models.user import User
                user = session.query(User).filter_by(user_uuid=session_obj.user_uuid).first()
                if not user:
                    return jsonify({
                        "error": "User not found. Please login again.",
                        "requires_login": True
                    }), 401
                
                # Store user information in Flask g
                g.current_user = {
                    "user_id": user.user_id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_admin": user.is_admin,
                    "user_uuid": user.user_uuid
                }
                g.session_id = session_id
                
                # Refresh session on successful validation
                refresh_user_session(session_id)
                
        except Exception as ex:
            return jsonify({
                "error": "Session validation failed. Please login again.",
                "requires_login": True
            }), 401
        
        return f(*args, **kwargs)
    return wrapper


def role_required(allowed_roles):
    """Decorator to require specific user roles using session tokens."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Get session token from request
            session_id = get_session_from_request()
            if not session_id:
                return jsonify({
                    "error": "Session not found. Please login again.",
                    "requires_login": True
                }), 401
            
            # Validate session and get user information
            try:
                with get_db_session() as session:
                    # Check if session is valid
                    if not Session.is_session_valid(session, session_id):
                        return jsonify({
                            "error": "Session has expired. Please login again.",
                            "requires_login": True
                        }), 401
                    
                    # Get session object to access user_uuid
                    session_obj = Session.get_session_by_id(session, session_id)
                    if not session_obj:
                        return jsonify({
                            "error": "Invalid session. Please login again.",
                            "requires_login": True
                        }), 401
                    
                    # Get user information from database
                    from models.user import User
                    user = session.query(User).filter_by(user_uuid=session_obj.user_uuid).first()
                    if not user:
                        return jsonify({
                            "error": "User not found. Please login again.",
                            "requires_login": True
                        }), 401
                    
                    # Map user role to role name
                    user_role_name = "ADMIN" if user.is_admin else "USER"
                    if not user_role_name:
                        return jsonify({
                            "error": "Invalid user role. Please contact administrator.",
                            "requires_login": True
                        }), 403
                    
                    # Check if user role is in allowed roles
                    if user_role_name not in allowed_roles:
                        return jsonify({"error": "Access forbidden"}), 403
                    
                    # Store user information in Flask g
                    g.current_user = {
                        "user_id": user.user_id,
                        "email": user.email,
                        "role": user_role_name,
                        "user_uuid": user.user_uuid
                    }
                    g.session_id = session_id
                    
                    # Refresh session on successful validation
                    Session.refresh_session(session, session_id)
                    
            except Exception as ex:
                return jsonify({
                    "error": f"Session validation error: {str(ex)}",
                    "requires_login": True
                }), 500
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(max_requests: int = DEFAULT_RATE_LIMIT_REQUESTS, window_minutes: int = DEFAULT_RATE_LIMIT_WINDOW_MINUTES):
    """Decorator to apply rate limiting to routes."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not check_rate_limit(f.__name__, max_requests, window_minutes):
                return jsonify({
                    "error": "Rate limit exceeded. Please try again later."
                }), 429
            return f(*args, **kwargs)
        return wrapper
    return decorator


def session_role_required(allowed_roles):
    """Decorator that combines session validation with role checking."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Get session token from request
            session_id = get_session_from_request()
            if not session_id:
                return jsonify({
                    "error": "Session not found. Please login again.",
                    "requires_login": True
                }), 401
            
            # Validate session and get user information
            try:
                with get_db_session() as session:
                    # Check if session is valid
                    if not Session.is_session_valid(session, session_id):
                        return jsonify({
                            "error": "Session has expired. Please login again.",
                            "requires_login": True
                        }), 401
                    
                    # Get session object to access user_uuid
                    session_obj = Session.get_session_by_id(session, session_id)
                    if not session_obj:
                        return jsonify({
                            "error": "Invalid session. Please login again.",
                            "requires_login": True
                        }), 401
                    
                    # Get user information from database
                    from models.user import User
                    user = session.query(User).filter_by(user_uuid=session_obj.user_uuid).first()
                    if not user:
                        return jsonify({
                            "error": "User not found. Please login again.",
                            "requires_login": True
                        }), 401
                    
                    # Map user role to role name
                    user_role_name = "ADMIN" if user.is_admin else "USER"
                    if not user_role_name:
                        return jsonify({
                            "error": "Invalid user role. Please contact administrator.",
                            "requires_login": True
                        }), 403
                    
                    # Check if user role is in allowed roles
                    if user_role_name not in allowed_roles:
                        return jsonify({"error": "Access forbidden"}), 403
                    
                    # Store user information in Flask g
                    g.current_user = {
                        "user_id": user.user_id,
                        "email": user.email,
                        "role": user_role_name,
                        "user_uuid": user.user_uuid
                    }
                    g.session_id = session_id
                    
                    # Refresh session on successful validation
                    Session.refresh_session(session, session_id)
                    
            except Exception as ex:
                return jsonify({
                    "error": f"Session validation error: {str(ex)}",
                    "requires_login": True
                }), 500
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


# Export all utilities for easy import
__all__ = [
    'generate_nonce', 'validate_nonce', 'validate_request_data', 
    'decode_jwt_token', 'extract_token_from_header', 'check_rate_limit',
    'validate_status_transition', 'get_device_info', 'validate_session',
    'get_session_from_request', 'refresh_user_session',
    'token_required', 'session_required', 'role_required', 'session_role_required', 'rate_limit',
    'nonce_store', 'request_counts'
]
