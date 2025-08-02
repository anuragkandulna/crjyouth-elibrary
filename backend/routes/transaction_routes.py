from flask import Blueprint, request, jsonify, g
from typing import Dict, Tuple
from models.user import User
from models.transaction import Transaction
from models.book_copy import BookCopy
from models.exceptions import (
    DuplicateTransactionError, TransactionNotFoundError, TransactionValidationError
)
from constants.config import LOG_LEVEL
from constants.constants import APP_LOG_FILE, MAX_BORROW_LIMIT, LATE_FINE_AMOUNT, LOST_DAMAGE_FINE, VALID_TRANSACTION_STATUSES
from utils.sqlite_database import get_db_session
from utils.my_logger import CustomLogger
from utils.timezone_utils import (
    utc_date_only, add_weeks_to_date, 
    is_date_past_due, calculate_weeks_overdue, utc_now
)
from utils.route_utils import role_required, rate_limit, validate_request_data, session_required, validate_status_transition


# Blueprint setup
transaction_bp = Blueprint('transaction_bp', __name__, url_prefix='/api/v1/transactions')
LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=APP_LOG_FILE).get_logger()


# -------------------- Utility Functions -------------------- #
def handle_transaction_error(error: Exception, context: str, status_code: int = 500) -> Tuple[Dict[str, str], int]:
    """Centralized transaction error handling."""
    LOGGER.error(f"{context}: {error}")
    
    if isinstance(error, DuplicateTransactionError):
        return {"error": "Transaction with this ID already exists"}, 409
    elif isinstance(error, TransactionNotFoundError):
        return {"error": "Transaction not found"}, 404
    elif isinstance(error, TransactionValidationError):
        return {"error": str(error)}, 400
    else:
        return {"error": "Internal server error"}, status_code


def get_current_user_from_db(session) -> User:
    """Get current user from database using token data."""
    user_id = g.current_user['user_id']
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise TransactionValidationError("User not found")
    return user


def validate_borrowing_eligibility(session, customer: User) -> None:
    """Validate if customer is eligible to borrow books."""
    # Check if customer has active membership
    if not hasattr(customer, 'library_membership') or not customer.library_membership:
        raise TransactionValidationError("No active library membership found")
    
    # Check account status
    if customer.account_status != 'ACTIVE':
        raise TransactionValidationError("Account is not active")
    
    # Check for unpaid fines
    unpaid_fine_transactions = session.query(Transaction).filter(
        Transaction.customer_id == customer.user_id,
        Transaction.fine_incurred > 0,
        Transaction.fine_forgiven == False,
        Transaction.status == 'CLOSED'
    ).all()
    
    total_unpaid_fines = sum(t.fine_incurred for t in unpaid_fine_transactions)
    if total_unpaid_fines > 0:
        raise TransactionValidationError(f"Outstanding fine of ₹{total_unpaid_fines:.2f} must be paid before borrowing")


def validate_book_availability(session, copy_id: str) -> BookCopy:
    """Validate book copy exists and is available."""
    book_copy = session.query(BookCopy).filter_by(copy_id=copy_id).first()
    if not book_copy:
        raise TransactionValidationError("Book copy not found")
    
    if book_copy.status != 'AVAILABLE':
        raise TransactionValidationError(f"Book copy is not available (status: {book_copy.status})")
    
    return book_copy


def check_borrowing_limit(session, customer: User) -> None:
    """Check if customer has reached borrowing limit."""
    active_borrows = session.query(Transaction).filter(
        Transaction.customer_id == customer.user_id,
        Transaction.status.in_(['PENDING', 'APPROVED', 'OPEN', 'OVERDUE'])
    ).count()
    
    if active_borrows >= MAX_BORROW_LIMIT:
        raise TransactionValidationError(f"Borrowing limit of {MAX_BORROW_LIMIT} books reached")


# -------------------- Customer Routes -------------------- #
@transaction_bp.route('/request-book', methods=['POST'])
@session_required
@rate_limit(max_requests=10, window_minutes=5)
def request_book():
    """Customer requests to borrow a book."""
    data = request.get_json()
    
    required_fields = ['copy_id', 'particulars']
    is_valid, error_msg = validate_request_data(data, required_fields)
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    try:
        with get_db_session() as session:
            customer = get_current_user_from_db(session)
            
            # Business logic validations
            validate_borrowing_eligibility(session, customer)
            check_borrowing_limit(session, customer)
            validate_book_availability(session, data['copy_id'])
            
            # Create transaction using model's CRUD operation
            transaction = Transaction.create_transaction(
                session=session,
                customer=customer,
                copy_id=data['copy_id'],
                particulars=data['particulars'],
                provided_ticket_id=data.get('ticket_id')
            )
            
            LOGGER.info(f"Book request created: {transaction.ticket_id} by customer {customer.user_id}")
            return jsonify({
                "message": "Book request submitted successfully",
                "ticket_id": transaction.ticket_id,
                "status": "PENDING"
            }), 201
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Book request failed")
        return jsonify(error_response), status_code


@transaction_bp.route('/extend-due-date/<ticket_id>', methods=['PUT'])
@session_required
@rate_limit(max_requests=5, window_minutes=10)
def extend_due_date(ticket_id: str):
    """Customer requests to extend book due date."""
    try:
        with get_db_session() as session:
            customer = get_current_user_from_db(session)
            
            # Business logic: Find and validate transaction
            transaction = session.query(Transaction).filter_by(
                ticket_id=ticket_id,
                customer_id=customer.user_id,
                status='OPEN'
            ).first()
            
            if not transaction:
                raise TransactionNotFoundError("Transaction not found or not in open state")
            
            # Validate that transaction is in a state that allows extension
            if transaction.status != 'OPEN':
                raise TransactionValidationError(f"Cannot extend due date for transaction in {transaction.status} state")
            
            # Business logic: Extension validation
            if transaction.is_extended:
                raise TransactionValidationError("Book has already been extended once")
            
            current_date = utc_date_only()
            if is_date_past_due(transaction.book_due_date, current_date):
                raise TransactionValidationError("Cannot extend book after due date has passed")
            
            # Business logic: Calculate new due date and update
            new_due_date = add_weeks_to_date(transaction.book_due_date, 1)
            new_particulars = transaction.particulars + " [EXTENDED]"
            
            # Use model's CRUD operation
            Transaction.edit_transaction(
                session=session,
                ticket_id=ticket_id,
                book_due_date=new_due_date,
                is_extended=True,
                particulars=new_particulars
            )
            
            LOGGER.info(f"Due date extended for transaction {ticket_id} by customer {customer.user_id} until {new_due_date.date()}")
            return jsonify({"message": "Due date extended successfully"}), 200
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Due date extension failed")
        return jsonify(error_response), status_code


@transaction_bp.route('/my-transactions', methods=['GET'])
@session_required
@rate_limit(max_requests=20, window_minutes=5)
def get_my_transactions():
    """Get all transactions for current user."""
    try:
        with get_db_session() as session:
            customer = get_current_user_from_db(session)
            
            # Business logic: Query user transactions
            transactions = session.query(Transaction).filter_by(
                customer_id=customer.user_id
            ).order_by(Transaction.ticket_created_date.desc()).all()
            
            # Convert to dict format
            transaction_list = []
            for t in transactions:
                transaction_list.append({
                    "ticket_id": t.ticket_id,
                    "status": t.status,
                    "particulars": t.particulars,
                    "copy_id": t.copy_id,
                    "book_borrow_date": t.book_borrow_date.date().isoformat() if t.book_borrow_date else None,
                    "book_due_date": t.book_due_date.date().isoformat() if t.book_due_date else None,
                    "book_return_date": t.book_return_date.date().isoformat() if t.book_return_date else None,
                    "fine_incurred": t.fine_incurred,
                    "fine_forgiven": t.fine_forgiven,
                    "is_extended": t.is_extended,
                    "created_date": t.ticket_created_date.isoformat()
                })
            
            return jsonify({
                "transactions": transaction_list,
                "count": len(transaction_list)
            }), 200
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Failed to fetch user transactions")
        return jsonify(error_response), status_code


@transaction_bp.route('/my-active-transactions', methods=['GET'])
@session_required
@rate_limit(max_requests=20, window_minutes=5)
def get_my_active_transactions():
    """Get active transactions for current user."""
    try:
        with get_db_session() as session:
            customer = get_current_user_from_db(session)
            
            # Business logic: Query active transactions
            transactions = session.query(Transaction).filter(
                Transaction.customer_id == customer.user_id,
                Transaction.status.in_(['PENDING', 'APPROVED', 'OPEN', 'OVERDUE'])
            ).order_by(Transaction.ticket_created_date.desc()).all()
            
            # Convert to dict format
            transaction_list = []
            for t in transactions:
                transaction_list.append({
                    "ticket_id": t.ticket_id,
                    "status": t.status,
                    "particulars": t.particulars,
                    "copy_id": t.copy_id,
                    "book_borrow_date": t.book_borrow_date.date().isoformat() if t.book_borrow_date else None,
                    "book_due_date": t.book_due_date.date().isoformat() if t.book_due_date else None,
                    "fine_incurred": t.fine_incurred,
                    "is_extended": t.is_extended,
                    "created_date": t.ticket_created_date.isoformat()
                })
            
            return jsonify({
                "active_transactions": transaction_list,
                "count": len(transaction_list)
            }), 200
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Failed to fetch active transactions")
        return jsonify(error_response), status_code


# -------------------- Staff Routes -------------------- #
@transaction_bp.route('/create-ticket', methods=['POST'])
@role_required(['LIBRARIAN', 'ADMIN'])
@rate_limit(max_requests=20, window_minutes=5)
def create_ticket():
    """Staff creates a transaction ticket."""
    data = request.get_json()
    
    required_fields = ['office_code', 'customer_name', 'particulars']
    is_valid, error_msg = validate_request_data(data, required_fields)
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    try:
        with get_db_session() as session:
            librarian = get_current_user_from_db(session)
            customer_id = data.get('customer_id')
            
            # Business logic: Validate customer if provided
            if customer_id:
                customer = session.query(User).filter_by(user_id=customer_id).first()
                if customer:
                    validate_borrowing_eligibility(session, customer)
                    check_borrowing_limit(session, customer)
            
            # Validate book copy if provided
            if data.get('copy_id'):
                validate_book_availability(session, data['copy_id'])
            
            # Create transaction using model's CRUD operation
            transaction = Transaction.create_staff_transaction(
                session=session,
                librarian=librarian,
                office_code=data['office_code'],
                customer_id=customer_id,
                customer_name=data['customer_name'],
                copy_id=data.get('copy_id'),
                particulars=data['particulars'],
                provided_ticket_id=data.get('ticket_id')
            )
            
            LOGGER.info(f"Transaction ticket created: {transaction.ticket_id} by staff {librarian.user_id}")
            return jsonify({
                "message": "Transaction ticket created successfully",
                "ticket_id": transaction.ticket_id,
                "status": transaction.status
            }), 201
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Transaction creation failed")
        return jsonify(error_response), status_code


@transaction_bp.route('/approve/<ticket_id>', methods=['PUT'])
@role_required(['LIBRARIAN', 'ADMIN'])
@rate_limit(max_requests=20, window_minutes=5)
def approve_transaction(ticket_id: str):
    """Staff approves a pending transaction."""
    data = request.get_json() or {}
    
    try:
        with get_db_session() as session:
            librarian = get_current_user_from_db(session)
            
            # Business logic: Find and validate transaction
            transaction = session.query(Transaction).filter_by(
                ticket_id=ticket_id,
                status='PENDING'
            ).first()
            
            if not transaction:
                raise TransactionNotFoundError("Transaction not found or not in pending state")
            
            # Validate status transition
            if not validate_status_transition(transaction.status, 'APPROVED'):
                raise TransactionValidationError(f"Cannot approve transaction in {transaction.status} state")
            
            # Business logic: Validate book copy if being assigned
            book_copy = None
            if data.get('copy_id'):
                book_copy = validate_book_availability(session, data['copy_id'])
                
                # Update transaction with book copy
                transaction.copy_id = data['copy_id']
            elif not transaction.copy_id:
                raise TransactionValidationError("Book copy must be assigned for approval")
            else:
                # Validate existing book copy
                book_copy = validate_book_availability(session, transaction.copy_id)
            
            # Business logic: Assign librarian and update status
            transaction.librarian_id = librarian.user_id
            transaction.status = 'APPROVED'
            
            # Add remarks if provided
            if data.get('remarks'):
                existing_remarks = transaction.remarks or ""
                transaction.remarks = f"{existing_remarks} [APPROVED: {data['remarks']}]".strip()
            
            # Mark book copy as issued (will be changed to BORROWED when actually issued)
            if book_copy:
                book_copy.status = 'ISSUED'
            
            session.commit()
            
            LOGGER.info(f"Transaction approved: {ticket_id} by staff {librarian.user_id}")
            return jsonify({"message": "Transaction approved successfully"}), 200
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Transaction approval failed")
        return jsonify(error_response), status_code


@transaction_bp.route('/issue/<ticket_id>', methods=['PUT'])
@role_required(['LIBRARIAN', 'ADMIN'])
@rate_limit(max_requests=20, window_minutes=5)
def issue_book(ticket_id: str):
    """Staff issues book to customer."""
    data = request.get_json() or {}
    
    try:
        with get_db_session() as session:
            # Business logic: Find and validate transaction
            transaction = session.query(Transaction).filter_by(
                ticket_id=ticket_id,
                status='APPROVED'
            ).first()
            
            if not transaction:
                raise TransactionNotFoundError("Transaction not found or not in approved state")
            
            # Validate status transition
            if not validate_status_transition(transaction.status, 'OPEN'):
                raise TransactionValidationError(f"Cannot issue book for transaction in {transaction.status} state")
            
            if not transaction.copy_id:
                raise TransactionValidationError("No book copy assigned to this transaction")
            
            # Business logic: Validate book copy status
            book_copy = session.query(BookCopy).filter_by(copy_id=transaction.copy_id).first()
            if not book_copy or book_copy.status not in ['ISSUED', 'AVAILABLE']:
                raise TransactionValidationError("Book copy is not available for issue")
            
            # Business logic: Calculate borrowing and due dates
            current_date = utc_date_only()
            
            # Default borrowing period (2 weeks = 14 days)
            borrowing_period_weeks = 2
            due_date = add_weeks_to_date(current_date, borrowing_period_weeks)
            
            # Business logic: Update transaction dates and status
            transaction.book_borrow_date = current_date
            transaction.book_due_date = due_date  
            transaction.status = 'OPEN'
            
            # Add remarks if provided
            if data.get('remarks'):
                existing_remarks = transaction.remarks or ""
                transaction.remarks = f"{existing_remarks} [ISSUED: {data['remarks']}]".strip()
            
            # Business logic: Update book copy status
            book_copy.status = 'BORROWED'
            
            session.commit()
            
            LOGGER.info(f"Book issued for transaction: {ticket_id}, due date: {due_date.date()}")
            return jsonify({
                "message": "Book issued successfully", 
                "due_date": due_date.date().isoformat()
            }), 200
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Book issue failed")
        return jsonify(error_response), status_code


@transaction_bp.route('/return/<ticket_id>', methods=['PUT'])
@role_required(['LIBRARIAN', 'ADMIN'])
@rate_limit(max_requests=20, window_minutes=5)
def return_book(ticket_id: str):
    """Staff processes book return."""
    data = request.get_json() or {}
    
    try:
        with get_db_session() as session:
            # Business logic: Find and validate transaction
            transaction = session.query(Transaction).filter_by(
                ticket_id=ticket_id,
                status='OPEN'
            ).first()
            
            if not transaction:
                raise TransactionNotFoundError("Transaction not found or not in open state")
            
            # Validate status transition
            if not validate_status_transition(transaction.status, 'CLOSED'):
                raise TransactionValidationError(f"Cannot return book for transaction in {transaction.status} state")
            
            if not transaction.copy_id:
                raise TransactionValidationError("No book copy assigned to this transaction")
            
            # Business logic: Validate book copy
            book_copy = session.query(BookCopy).filter_by(copy_id=transaction.copy_id).first()
            if not book_copy:
                raise TransactionValidationError("Book copy not found")
            
            # Business logic: Calculate return date and potential fine
            return_date = utc_date_only()
            fine_amount = 0.0
            
            # Check if book is overdue and calculate fine
            if transaction.book_due_date and is_date_past_due(transaction.book_due_date, return_date):
                weeks_overdue = calculate_weeks_overdue(transaction.book_due_date, return_date)
                
                # Business logic: Fine calculation (₹10 per week overdue)
                fine_per_week = 10.0
                fine_amount = weeks_overdue * fine_per_week
                
                # Business logic: Check founder/pastor exemptions
                customer = session.query(User).filter_by(user_id=transaction.customer_id).first()
                if customer and (customer.is_founder or (customer.maturity_level and customer.maturity_level.title == "PASTOR")):
                    fine_amount = 0.0  # Founder/Pastor exempt from fines
                
                transaction.fine_incurred = fine_amount
            
            # Business logic: Handle damage or loss
            damage = data.get('damage', False)
            lost = data.get('lost', False)
            
            if lost:
                # Business logic: Lost book fine (₹100 base + overdue fine)
                lost_book_fine = 100.0
                transaction.fine_incurred += lost_book_fine
                book_copy.status = 'LOST'
            elif damage:
                # Business logic: Damage assessment fine (₹50 base + overdue fine)
                damage_fine = 50.0
                transaction.fine_incurred += damage_fine
                book_copy.status = 'DAMAGED'
            else:
                # Normal return - book available again
                book_copy.status = 'AVAILABLE'
            
            # Business logic: Update transaction
            transaction.book_return_date = return_date
            transaction.status = 'CLOSED'
            transaction.ticket_closed_date = utc_now()
            
            # Add remarks
            return_remarks = []
            if damage:
                return_remarks.append("DAMAGED")
            if lost:
                return_remarks.append("LOST") 
            if data.get('remarks'):
                return_remarks.append(data['remarks'])
            
            if return_remarks:
                existing_remarks = transaction.remarks or ""
                transaction.remarks = f"{existing_remarks} [RETURNED: {', '.join(return_remarks)}]".strip()
            
            session.commit()
            
            response_data = {"message": "Book returned successfully"}
            if transaction.fine_incurred > 0:
                response_data["fine_incurred"] = transaction.fine_incurred
                response_data["fine_message"] = f"Fine of ₹{transaction.fine_incurred:.2f} has been assessed"
            
            LOGGER.info(f"Book returned for transaction: {ticket_id}, fine: ₹{transaction.fine_incurred:.2f}")
            return jsonify(response_data), 200
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Book return failed")
        return jsonify(error_response), status_code


@transaction_bp.route('/reject/<ticket_id>', methods=['PUT'])
@role_required(['LIBRARIAN', 'ADMIN'])
@rate_limit(max_requests=20, window_minutes=5)
def reject_transaction(ticket_id: str):
    """Staff rejects a pending transaction."""
    data = request.get_json()
    
    is_valid, error_msg = validate_request_data(data, ['remarks'])
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    try:
        with get_db_session() as session:
            librarian = get_current_user_from_db(session)
            
            # Business logic: Find and validate transaction
            transaction = session.query(Transaction).filter_by(
                ticket_id=ticket_id,
                status='PENDING'
            ).first()
            
            if not transaction:
                raise TransactionNotFoundError("Transaction not found or not in pending state")
            
            # Validate status transition
            if not validate_status_transition(transaction.status, 'REJECTED'):
                raise TransactionValidationError(f"Cannot reject transaction in {transaction.status} state")
            
            # Business logic: Reject transaction
            transaction.status = 'REJECTED'
            transaction.librarian_id = librarian.user_id
            transaction.ticket_closed_date = utc_now()
            
            # Add rejection remarks
            existing_remarks = transaction.remarks or ""
            transaction.remarks = f"{existing_remarks} [REJECTED: {data['remarks']}]".strip()
            
            # Business logic: Free up book copy if assigned
            if transaction.copy_id:
                book_copy = session.query(BookCopy).filter_by(copy_id=transaction.copy_id).first()
                if book_copy and book_copy.status == 'ISSUED':
                    book_copy.status = 'AVAILABLE'
            
            session.commit()
            
            LOGGER.info(f"Transaction rejected: {ticket_id} by staff {librarian.user_id}")
            return jsonify({"message": "Transaction rejected successfully"}), 200
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Transaction rejection failed")
        return jsonify(error_response), status_code


@transaction_bp.route('/escalate/<ticket_id>', methods=['PUT'])
@role_required(['LIBRARIAN', 'ADMIN'])
@rate_limit(max_requests=10, window_minutes=5)
def escalate_for_fine_forgiveness(ticket_id: str):
    """Staff escalates transaction for fine forgiveness."""
    data = request.get_json()
    
    is_valid, error_msg = validate_request_data(data, ['remarks'])
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    try:
        with get_db_session() as session:
            librarian = get_current_user_from_db(session)
            
            # Business logic: Find and validate transaction
            transaction = session.query(Transaction).filter_by(
                ticket_id=ticket_id,
                status='CLOSED'
            ).first()
            
            if not transaction:
                raise TransactionNotFoundError("Transaction not found or not in closed state")
            
            # Validate status transition
            if not validate_status_transition(transaction.status, 'ESCALATED'):
                raise TransactionValidationError(f"Cannot escalate transaction in {transaction.status} state")
            
            if transaction.fine_incurred <= 0:
                raise TransactionValidationError("No fine to forgive for this transaction")
            
            if transaction.fine_forgiven:
                raise TransactionValidationError("Fine has already been forgiven for this transaction")
            
            # Business logic: Escalate for fine forgiveness
            transaction.status = 'ESCALATED'
            
            # Add escalation remarks
            existing_remarks = transaction.remarks or ""
            transaction.remarks = f"{existing_remarks} [ESCALATED: {data['remarks']}]".strip()
            
            session.commit()
            
            LOGGER.info(f"Transaction escalated: {ticket_id} by staff {librarian.user_id}")
            return jsonify({"message": "Transaction escalated for fine forgiveness"}), 200
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Transaction escalation failed")
        return jsonify(error_response), status_code


# -------------------- Admin Routes -------------------- #
@transaction_bp.route('/forgive-fine/<ticket_id>', methods=['PUT'])
@role_required(['ADMIN'])
@rate_limit(max_requests=10, window_minutes=5)
def forgive_fine(ticket_id: str):
    """Admin forgives fine for escalated transaction."""
    data = request.get_json()
    
    is_valid, error_msg = validate_request_data(data, ['remarks'])
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    try:
        with get_db_session() as session:
            admin = get_current_user_from_db(session)
            
            # Business logic: Find and validate transaction
            transaction = session.query(Transaction).filter_by(
                ticket_id=ticket_id,
                status='ESCALATED'
            ).first()
            
            if not transaction:
                raise TransactionNotFoundError("Transaction not found or not in escalated state")
            
            # Validate status transition
            if not validate_status_transition(transaction.status, 'CLOSED'):
                raise TransactionValidationError(f"Cannot forgive fine for transaction in {transaction.status} state")
            
            if transaction.fine_incurred <= 0:
                raise TransactionValidationError("No fine to forgive for this transaction")
            
            if transaction.fine_forgiven:
                raise TransactionValidationError("Fine has already been forgiven for this transaction")
            
            # Business logic: Forgive fine
            transaction.fine_forgiven = True
            transaction.fine_forgiven_by = admin.user_id
            transaction.fine_forgiven_date = utc_now()
            transaction.status = 'CLOSED'
            
            # Add forgiveness remarks
            existing_remarks = transaction.remarks or ""
            transaction.remarks = f"{existing_remarks} [FINE_FORGIVEN: {data['remarks']}]".strip()
            
            session.commit()
            
            LOGGER.info(f"Fine forgiven for transaction: {ticket_id} by admin {admin.user_id}")
            return jsonify({"message": "Fine forgiven successfully"}), 200
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Fine forgiveness failed")
        return jsonify(error_response), status_code


# -------------------- Query Routes -------------------- #
@transaction_bp.route('/view/<ticket_id>', methods=['GET'])
@session_required
@rate_limit(max_requests=30, window_minutes=5)
def view_transaction(ticket_id: str):
    """View transaction details."""
    try:
        with get_db_session() as session:
            current_user = get_current_user_from_db(session)
            
            # Business logic: Check if user can view this transaction
            transaction = session.query(Transaction).filter_by(ticket_id=ticket_id).first()
            if not transaction:
                raise TransactionNotFoundError("Transaction not found")
            
            # Customers can only view their own transactions
            if current_user.user_role == 3 and transaction.customer_id != current_user.user_id:
                return jsonify({"error": "Access forbidden"}), 403
            
            # Use model's CRUD operation
            transaction_data = Transaction.view_transaction(session, ticket_id)
            
            return jsonify({"transaction": transaction_data}), 200
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Failed to view transaction")
        return jsonify(error_response), status_code


@transaction_bp.route('/pending', methods=['GET'])
@role_required(['LIBRARIAN', 'ADMIN'])
@rate_limit(max_requests=20, window_minutes=5)
def get_pending_transactions():
    """Get all pending transactions."""
    try:
        with get_db_session() as session:
            # Business logic: Query pending transactions
            transactions = session.query(Transaction).filter_by(
                status='PENDING'
            ).order_by(Transaction.ticket_created_date.asc()).all()
            
            # Convert to dict format
            transaction_list = []
            for t in transactions:
                transaction_list.append({
                    "ticket_id": t.ticket_id,
                    "customer_id": t.customer_id,
                    "customer_name": t.customer_name,
                    "copy_id": t.copy_id,
                    "particulars": t.particulars,
                    "office_code": t.office_code,
                    "created_by_customer": t.created_by_customer,
                    "created_date": t.ticket_created_date.isoformat()
                })
            
            return jsonify({
                "pending_transactions": transaction_list,
                "count": len(transaction_list)
            }), 200
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Failed to fetch pending transactions")
        return jsonify(error_response), status_code


@transaction_bp.route('/overdue', methods=['GET'])
@role_required(['LIBRARIAN', 'ADMIN'])
@rate_limit(max_requests=20, window_minutes=5)
def get_overdue_transactions():
    """Get all overdue transactions."""
    try:
        with get_db_session() as session:
            current_date = utc_date_only()
            
            # Business logic: Query overdue transactions
            transactions = session.query(Transaction).filter(
                Transaction.status == 'OPEN',
                Transaction.book_due_date < current_date
            ).order_by(Transaction.book_due_date.asc()).all()
            
            # Convert to dict format with overdue calculations
            transaction_list = []
            for t in transactions:
                weeks_overdue = calculate_weeks_overdue(t.book_due_date, current_date) if t.book_due_date else 0
                transaction_list.append({
                    "ticket_id": t.ticket_id,
                    "customer_id": t.customer_id,
                    "customer_name": t.customer_name,
                    "copy_id": t.copy_id,
                    "particulars": t.particulars,
                    "book_due_date": t.book_due_date.date().isoformat(),
                    "weeks_overdue": weeks_overdue,
                    "potential_fine": weeks_overdue * 10.0,  # ₹10 per week
                    "is_extended": t.is_extended,
                    "librarian_id": t.librarian_id
                })
            
            return jsonify({
                "overdue_transactions": transaction_list,
                "count": len(transaction_list)
            }), 200
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Failed to fetch overdue transactions")
        return jsonify(error_response), status_code


@transaction_bp.route('/escalated', methods=['GET'])
@role_required(['ADMIN'])
@rate_limit(max_requests=20, window_minutes=5)
def get_escalated_transactions():
    """Get all escalated transactions."""
    try:
        with get_db_session() as session:
            # Business logic: Query escalated transactions
            transactions = session.query(Transaction).filter_by(
                status='ESCALATED'
            ).order_by(Transaction.ticket_updated_date.asc()).all()
            
            # Convert to dict format
            transaction_list = []
            for t in transactions:
                transaction_list.append({
                    "ticket_id": t.ticket_id,
                    "customer_id": t.customer_id,
                    "customer_name": t.customer_name,
                    "copy_id": t.copy_id,
                    "particulars": t.particulars,
                    "fine_incurred": t.fine_incurred,
                    "book_return_date": t.book_return_date.date().isoformat() if t.book_return_date else None,
                    "escalated_date": t.ticket_updated_date.isoformat(),
                    "remarks": t.remarks
                })
            
            return jsonify({
                "escalated_transactions": transaction_list,
                "count": len(transaction_list)
            }), 200
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Failed to fetch escalated transactions")
        return jsonify(error_response), status_code


# -------------------- Maintenance Routes -------------------- #
@transaction_bp.route('/mark-overdue', methods=['POST'])
@role_required(['ADMIN'])
@rate_limit(max_requests=5, window_minutes=60)
def mark_overdue_transactions():
    """Mark open transactions as overdue (scheduled task)."""
    try:
        with get_db_session() as session:
            current_date = utc_date_only()
            
            # Business logic: Find open transactions past due date
            overdue_transactions = session.query(Transaction).filter(
                Transaction.status == 'OPEN',
                Transaction.book_due_date < current_date
            ).all()
            
            count = 0
            for transaction in overdue_transactions:
                # Business logic: Calculate fine for overdue books
                if transaction.book_due_date:
                    weeks_overdue = calculate_weeks_overdue(transaction.book_due_date, current_date)
                    fine_per_week = 10.0
                    calculated_fine = weeks_overdue * fine_per_week
                    
                    # Business logic: Check founder/pastor exemptions
                    customer = session.query(User).filter_by(user_id=transaction.customer_id).first()
                    if customer and (customer.is_founder or (customer.maturity_level and customer.maturity_level.title == "PASTOR")):
                        calculated_fine = 0.0  # Founder/Pastor exempt from fines
                    
                    # Validate status transition
                    if validate_status_transition(transaction.status, 'OVERDUE'):
                        # Update transaction status and fine
                        transaction.status = 'OVERDUE'
                        transaction.fine_incurred = calculated_fine
                        
                        # Add overdue remark
                        existing_remarks = transaction.remarks or ""
                        transaction.remarks = f"{existing_remarks} [MARKED_OVERDUE: System automated process]".strip()
                        
                        count += 1
            
            session.commit()
            
            LOGGER.info(f"Marked {count} transactions as overdue")
            return jsonify({
                "message": f"Successfully marked {count} transactions as overdue",
                "count": count
            }), 200
            
    except Exception as ex:
        error_response, status_code = handle_transaction_error(ex, "Failed to mark overdue transactions")
        return jsonify(error_response), status_code
