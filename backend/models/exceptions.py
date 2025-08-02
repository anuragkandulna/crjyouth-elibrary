"""
All exceptions defined here.
"""

class DuplicateUserError(ValueError):
    """Raised when a user with the same email or phone already exists."""
    pass

class DuplicateUserIdError(ValueError):
    """Raised when a generated user ID already exists in the database."""
    pass

class UserNotFoundError(ValueError):
    """Raised when the specified user could not be found."""
    pass

class DuplicateBookError(ValueError):
    """Raised when a book with the same ISBN or ID already exists."""
    pass

class BookNotFoundError(ValueError):
    """Raised when the specified book could not be found."""
    pass

class DuplicateBookCopyError(ValueError):
    """Raised when a duplicate book copy is attempted to be added."""
    pass

class BookCopyNotFound(ValueError):
    """Raised when the specified book copy could not be found."""
    pass

class LibraryOfficeNotFound(ValueError):
    """Raised when the specified library office/branch does not exist."""
    pass

class WeakPasswordError(ValueError):
    """Raised when the provided password is too weak."""
    pass

class DuplicateSpiritualMaturityLevelError(ValueError):
    """Raised when duplicate spiritual maturity level is attempted to be added."""
    pass

class SpiritualMaturityLevelNotFound(ValueError):
    """Raised when spiritual maturity level could not be found."""
    pass

class AuthorNotFoundError(ValueError):
    """Raised when author could not be found."""
    pass

class PublisherNotFoundError(ValueError):
    """Raised when publisher could not be found."""
    pass

class SubjectDifficultyTierNotFoundError(ValueError):
    """Raised when subject difficulty tier could not be found."""
    pass

class BookLanguageNotFoundError(ValueError):
    """Raised when book language could not be found."""
    pass

class BookCategoryNotFoundError(ValueError):
    """Raised when book genre could not be found."""
    pass


class DuplicateTransactionError(ValueError):
    """Raised when a transaction with the same ticket ID already exists."""
    pass


class TransactionNotFoundError(ValueError):
    """Raised when the specified transaction could not be found."""
    pass


class InvalidTransactionStateError(ValueError):
    """Raised when a transaction operation is attempted on an invalid state."""
    pass


class TransactionValidationError(ValueError):
    """Raised when transaction validation fails."""
    pass


class DuplicateOfficeError(ValueError):
    """Raised when an office with the same office code already exists."""
    pass


class OfficeNotFoundError(ValueError):
    """Raised when the specified office could not be found."""
    pass


class OfficeValidationError(ValueError):
    """Raised when office validation fails."""
    pass


class ReferralCodeNotFoundError(ValueError):
    """Raised when the specified referral code could not be found."""
    pass


class ReferralCodeValidationError(ValueError):
    """Raised when referral code validation fails."""
    pass


class DuplicateReferralError(ValueError):
    """Raised when a duplicate referral is attempted."""
    pass
