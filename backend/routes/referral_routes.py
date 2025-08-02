# routes/referral_routes.py
from flask import Blueprint, request, jsonify, g
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy import select
from utils.psql_database import get_db_session
from models.referral_code import ReferralCode
from models.library_user import LibraryUser
from models.exceptions import (
    ReferralCodeNotFoundError, ReferralCodeValidationError, 
    DuplicateReferralError, UserNotFoundError
)
from utils.my_logger import CustomLogger
from utils.route_utils import token_required, role_required, rate_limit, session_required
from constants.constants import OPS_LOG_FILE
from constants.config import LOG_LEVEL, TIMED_SECRET_KEY


referral_bp = Blueprint("referral_bp", __name__, url_prefix="/api/v1/referrals")
serializer = URLSafeTimedSerializer(TIMED_SECRET_KEY)
LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


def handle_referral_error(error: Exception, context: str, status_code: int = 500) -> tuple:
    """
    Centralized referral error handling.
    
    Args:
        error: Exception object
        context: Context of the error
        status_code: Status code to return
    """
    LOGGER.error(f"{context}: {error}")
    
    if isinstance(error, ReferralCodeNotFoundError):
        return {"error": "Referral code not found"}, 404
    elif isinstance(error, ReferralCodeValidationError):
        return {"error": str(error)}, 400
    elif isinstance(error, DuplicateReferralError):
        return {"error": str(error)}, 409
    elif isinstance(error, UserNotFoundError):
        return {"error": "User not found"}, 404
    else:
        return {"error": "Internal server error"}, status_code


def validate_referral_token(token: str, phone_number: str) -> tuple:
    """
    Validate referral token and return referral data if valid.
    
    Args:
        token: The referral token to validate
        phone_number: The phone number to match against the token
        
    Returns:
        tuple: (referral_data_dict, error_response, status_code)
               - If valid: (referral_data, None, None)
               - If invalid: (None, error_response, status_code)
    """

    with get_db_session() as session:
        # Decode token
        decoded = serializer.loads(token, max_age=6048800)  # valid for 7 days
        referral_id = decoded.get("referral_id")
        invited_phone = decoded.get("invited_phone")

        if not all([referral_id, invited_phone]):
            LOGGER.error(f"Invalid referral code data for validation: {decoded}")
            return handle_referral_error(
                error=ReferralCodeValidationError("Invalid referral code!!!"), 
                context="Invalid referral code!!!",
                status_code=400
            )

        # Verify phone number matches referral code
        if phone_number != invited_phone:
            LOGGER.warning(f"Phone number mismatch: invited_phone={invited_phone[-2:]}, provided={phone_number[-2:]}")
            return handle_referral_error(
                error=ReferralCodeValidationError("Invalid referral code!!!"), 
                context="Invalid referral code!!!",
                status_code=400
            )

        # Use referral code
        referral = ReferralCode.use_code(
            session=session,
            referral_id=referral_id,
            invited_phone=phone_number
        )
        LOGGER.info(f"Referral code {referral_id} used by phone ending with {phone_number[-2:]} at {referral.assigned_office}")
        
        # Return referral data
        referral_data = {
            "referral_id": referral_id,
            "code_owner": referral.code_owner,
            "invited_phone": invited_phone,
            "assigned_office": referral.assigned_office
        }
        return referral_data, None, None


def get_current_user_from_db(session) -> LibraryUser:
    """
    Get current user from database using token data.
    
    Args:
        session: Database session
        
    Returns:
        LibraryUser: Current user object
    """
    user_id = g.current_user['user_id']
    stmt = select(LibraryUser).where(LibraryUser.user_id == user_id)
    user = session.execute(stmt).scalar_one_or_none()
    if not user:
        raise UserNotFoundError("User not found")
    return user


# -------------------- Routes -------------------- #
@referral_bp.route("/generate", methods=["POST"])
@session_required
@role_required(['Admin'])
@rate_limit(max_requests=10, window_minutes=5)
def generate_referral():
    """
    Generate a referral token for a specific phone number.
    
    Returns:
        JSON response with referral token and referral details.
    """
    data = request.get_json() or {}
    invited_phone = data.get("invited_phone")
    assigned_office = data.get("assigned_office")

    if not assigned_office:
        LOGGER.warning("Referral generation attempted without assigned_office")
        return jsonify({"error": "assigned_office is required"}), 400

    if not invited_phone:
        LOGGER.warning("Referral generation attempted without invited_phone")
        return jsonify({"error": "invited_phone is required"}), 400

    try:
        with get_db_session() as session:
            # Get current user (referrer)
            current_user = get_current_user_from_db(session)
            
            # Validate phone number format (basic validation)
            if len(invited_phone) < 10 or len(invited_phone) > 15:
                LOGGER.warning(f"Invalid phone number format: {invited_phone}")
                return jsonify({"error": "Invalid phone number format!!!"}), 400

            # Check if user is trying to refer themselves
            if current_user.phone_number == invited_phone:
                LOGGER.warning(f"User {current_user.user_id} attempted to refer themselves")
                return jsonify({"error": "Invalid referral attempt!!!"}), 400

            # Check if user with invited phone already exists
            stmt = select(LibraryUser).where(LibraryUser.phone_number == invited_phone)
            existing = session.execute(stmt).scalar_one_or_none()
            if existing:
                LOGGER.warning(f"User {current_user.user_id} attempted to refer existing user with phone {invited_phone}")
                return jsonify({"error": "Invalid referral attempt!!!"}), 400

            # Create referral code
            referral = ReferralCode.create_code(
                session=session, 
                owner=current_user.user_id, 
                invited_phone=invited_phone,
                assigned_office=assigned_office
            )
            
            # Create token with referral ID and phone number
            token_data = {
                "referral_id": referral.id,
                "invited_phone": invited_phone,
                "assigned_office": assigned_office,
                "referrer_id": current_user.user_uuid
            }
            token = serializer.dumps(token_data)
            LOGGER.info(f"Referral {referral.id} by user {current_user.user_id} for phone ending with {invited_phone[-2:]} at {assigned_office}")
            
            return jsonify({
                "referral_token": token,
                "referral": {
                    "id": referral.id,
                    "owner_id": current_user.user_uuid,
                    "owner_name": f"{current_user.first_name} {current_user.last_name}",
                    "phone_last_two_digits": invited_phone[-2:],
                    "assigned_office_code": assigned_office,
                    "created_at": referral.created_at.isoformat()
                }
            }), 201

    except Exception as ex:
        error_response, status_code = handle_referral_error(ex, "Referral generation failed")
        return jsonify(error_response), status_code


@referral_bp.route("/validate", methods=["POST"])
@rate_limit(max_requests=20, window_minutes=5)
def validate_referral():
    """Validate a referral token and return referral details."""
    data = request.get_json() or {}
    token = data.get("token")

    if not token:
        LOGGER.warning("Referral validation attempted without token")
        return jsonify({"error": "token is required"}), 400

    try:
        with get_db_session() as session:
            # Decode token
            decoded = serializer.loads(token, max_age=6048800)  # valid for 7 days
            referral_id = decoded.get("referral_id")
            invited_phone = decoded.get("invited_phone")
            assigned_office = decoded.get("assigned_office")
            referrer_id = decoded.get("referrer_id")

            if not all([referral_id, invited_phone, assigned_office, referrer_id]):
                LOGGER.error(f"Invalid token data: {decoded}")
                return jsonify({"error": "Invalid token!!!"}), 400

            # Get referral code
            referral = session.query(ReferralCode).filter_by(id=referral_id).first()
            if not referral:
                LOGGER.error(f"Referral code {referral_id} not found during validation")
                return jsonify({"valid": False, "reason": "Referral code not found"}), 404

            if not referral.is_active:
                LOGGER.warning(f"Referral code {referral_id} is not active")
                return jsonify({"valid": False, "reason": "Referral code is not active"}), 400

            if referral.invited_user_id:
                LOGGER.warning(f"Referral code {referral_id} has already been used")
                return jsonify({"valid": False, "reason": "Referral code has already been used"}), 400

            # Get referrer details
            referrer = session.query(LibraryUser).filter_by(user_id=referrer_id).first()
            if not referrer:
                LOGGER.error(f"Referrer {referrer_id} not found")
                return jsonify({"valid": False, "reason": "Referrer not found"}), 404

            LOGGER.info(f"Referral token validated: {referral_id} for phone {invited_phone}")

            return jsonify({
                "valid": True,
                "referral_id": referral.id,
                "referrer": {
                    "user_id": referrer.user_id,
                    "name": f"{referrer.first_name} {referrer.last_name}",
                    "phone": referrer.phone_number
                },
                "invited_phone": invited_phone
            }), 200

    except SignatureExpired:
        LOGGER.warning("Referral token expired during validation")
        return jsonify({"valid": False, "reason": "Referral token expired"}), 400
    except BadSignature:
        LOGGER.warning("Invalid referral token signature during validation")
        return jsonify({"valid": False, "reason": "Invalid referral token"}), 400
    except Exception as ex:
        error_response, status_code = handle_referral_error(ex, "Referral validation failed")
        return jsonify(error_response), status_code





@referral_bp.route("/my-referrals", methods=["GET"])
@session_required
@role_required(['Admin'])
@rate_limit(max_requests=20, window_minutes=5)
def get_my_referrals():
    """Get all referrals created by current user."""
    try:
        with get_db_session() as session:
            current_user = get_current_user_from_db(session)
            
            # Get referrals created by current user
            referrals = session.query(ReferralCode).filter_by(
                code_owner=current_user.user_uuid
            ).order_by(ReferralCode.created_at.desc()).all()
            
            referral_list = []
            for referral in referrals:
                # Check if user exists for this phone number
                invited_user = None
                if referral.invited_phone:
                    invited_user = session.query(LibraryUser).filter_by(
                        phone_number=referral.invited_phone
                    ).first()
                
                referral_data = {
                    "id": referral.id,
                    "invited_phone": referral.invited_phone,
                    "is_active": referral.is_active,
                    "created_at": referral.created_at.isoformat(),
                    "invited_user": None
                }
                
                if invited_user:
                    referral_data["invited_user"] = {
                        "user_id": invited_user.user_id,
                        "name": f"{invited_user.first_name} {invited_user.last_name}",
                        "phone": invited_user.phone_number
                    }
                
                referral_list.append(referral_data)
            
            LOGGER.info(f"Retrieved {len(referral_list)} referrals for user {current_user.user_id}")
            
            return jsonify({
                "referrals": referral_list,
                "count": len(referral_list)
            }), 200

    except Exception as ex:
        error_response, status_code = handle_referral_error(ex, "Failed to get user referrals")
        return jsonify(error_response), status_code


@referral_bp.route("/deactivate/<int:referral_id>", methods=["PUT"])
@session_required
@role_required(['Admin'])
@rate_limit(max_requests=5, window_minutes=10)
def deactivate_referral(referral_id: int):
    """Deactivate a referral code (only by owner)."""
    try:
        with get_db_session() as session:
            current_user = get_current_user_from_db(session)
            
            # Get referral code
            referral = session.query(ReferralCode).filter_by(id=referral_id).first()
            if not referral:
                LOGGER.error(f"Referral code {referral_id} not found for deactivation")
                return jsonify({"error": "Referral code not found"}), 404

            # Check if current user is the owner
            if referral.code_owner != current_user.user_uuid:
                LOGGER.warning(f"User {current_user.user_id} attempted to deactivate referral {referral_id} owned by {referral.code_owner}")
                return jsonify({"error": "Not authorized to deactivate this referral"}), 403

            # Deactivate referral
            ReferralCode.deactivate_code(session, referral_id)
            
            LOGGER.info(f"Referral code {referral_id} deactivated by owner {current_user.user_id}")
            
            return jsonify({"message": "Referral code deactivated successfully"}), 200

    except Exception as ex:
        error_response, status_code = handle_referral_error(ex, "Referral deactivation failed")
        return jsonify(error_response), status_code
