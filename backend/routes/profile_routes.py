from flask import Blueprint, request, jsonify, g
from models.user import User
from constants.config import LOG_LEVEL
from constants.constants import AUTH_LOG_FILE
from utils.sqlite_database import get_db_session
from utils.my_logger import CustomLogger
from utils.route_utils import rate_limit, validate_request_data, session_required
from routes.auth_routes import handle_auth_error
from models.session import Session


profile_bp = Blueprint('profile_bp', __name__, url_prefix='/api/v1/profile')
LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=AUTH_LOG_FILE).get_logger()


# -------------------- Routes -------------------- #
@profile_bp.route('', methods=['GET'])
@session_required
@rate_limit()
def get_profile():
    """Get current user's profile information."""
    try:
        user_id = g.current_user['user_id']
        
        with get_db_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            
            if not user:
                return jsonify({
                    "error": "User not found", 
                    }), 404

            profile_data = {
                "user_id": user.user_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "address_line_1": user.address_line_1,
                "address_line_2": user.address_line_2,
                "city": user.city,
                "state": user.state,
                "country": user.country,
                "postal_code": user.postal_code,
                "account_status": user.account_status,
                "role": user.user_role.role,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }

            LOGGER.info(f"User '{user.user_id}' retrieved profile successfully.")
            return jsonify({"profile": profile_data}), 200

    except Exception as ex:
        error_response, status_code = handle_auth_error(ex, "Profile retrieval failed")
        return jsonify(error_response), status_code


@profile_bp.route('', methods=['PUT'])
@session_required
@rate_limit()
def update_profile():
    """Update current user's profile information."""
    data = request.get_json()
    
    if not data:
        return jsonify({
            "error": "Request body must be valid JSON"
        }), 400
    
    try:
        user_id = g.current_user['user_id']
        
        with get_db_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            
            if not user:
                return jsonify({
                    "error": "User not found", 
                    }), 404

            # Update allowed fields
            updatable_fields = [
                'first_name', 'last_name', 'email', 'phone_number',
                'address_line_1', 'address_line_2', 'city', 'state', 
                'country', 'postal_code'
            ]
            
            updated_fields = []
            for field in updatable_fields:
                if field in data and data[field] is not None:
                    setattr(user, field, data[field])
                    updated_fields.append(field)

            if updated_fields:
                session.commit()
                LOGGER.info(f"User '{user.user_id}' updated profile fields: {updated_fields}")
                return jsonify({
                    "message": "Profile updated successfully",
                    "updated_fields": updated_fields
                }), 200
            else:
                return jsonify({
                    "message": "No valid fields provided for update"
                }), 400

    except Exception as ex:
        error_response, status_code = handle_auth_error(ex, "Profile update failed")
        return jsonify(error_response), status_code


@profile_bp.route('/deactivate', methods=['PUT'])
@session_required
@rate_limit(max_requests=5, window_minutes=60)
def deactivate_account():
    """Deactivate current user's account."""
    data = request.get_json()
    
    is_valid, error_msg = validate_request_data(data, ['password', 'confirmation'])
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    if data['confirmation'] != 'DEACTIVATE':
        return jsonify({
            "error": "Confirmation must be 'DEACTIVATE'"
        }), 400
    
    try:
        user_id = g.current_user['user_id']
        
        with get_db_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            
            if not user:
                return jsonify({
                    "error": "User not found", 
                    }), 404

            if not user.check_password(data['password']):
                return jsonify({
                    "error": "Invalid password"
                }), 401

            user.is_active = False
            
            # Deactivate all user sessions
            Session.deactivate_all_sessions(session, user.user_uuid)
            
            session.commit()
            
            LOGGER.info(f"User '{user.user_id}' deactivated account successfully. All sessions invalidated.")
            return jsonify({"message": "Account deactivated successfully. Please login again if reactivating."}), 200

    except Exception as ex:
        error_response, status_code = handle_auth_error(ex, "Account deactivation failed")
        return jsonify(error_response), status_code


@profile_bp.route('/membership', methods=['GET'])
@session_required
@rate_limit()
def get_membership_info():
    """Get current user's membership information."""
    try:
        user_id = g.current_user['user_id']
        
        with get_db_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            
            if not user:
                return jsonify({
                    "error": "User not found", 
                    }), 404

            membership_data = {
                "user_id": user.user_id,
                "membership_type": user.library_membership.membership_type if user.library_membership else None,
                "membership_status": user.library_membership.membership_status if user.library_membership else None,
                "registered_at_office": user.registered_at_office,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }

            LOGGER.info(f"User '{user.user_id}' retrieved membership info successfully.")
            return jsonify({"membership": membership_data}), 200

    except Exception as ex:
        error_response, status_code = handle_auth_error(ex, "Membership info retrieval failed")
        return jsonify(error_response), status_code
