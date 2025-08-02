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


class DuplicateOfficeError(ValueError):
    """Raised when a duplicate office is attempted to be added."""
    pass


class OfficeNotFoundError(ValueError):
    """Raised when the specified office could not be found."""
    pass


class WeakPasswordError(ValueError):
    """Raised when the provided password is too weak."""
    pass


class AuthorNotFoundError(ValueError):
    """Raised when author could not be found."""
    pass


class PublisherNotFoundError(ValueError):
    """Raised when publisher could not be found."""
    pass


class GenreNotFoundError(ValueError):
    """Raised when genre could not be found."""
    pass


class LanguageNotFoundError(ValueError):
    """Raised when language could not be found."""
    pass


class TransactionNotFoundError(ValueError):
    """Raised when transaction could not be found."""
    pass


class TransactionValidationError(ValueError):
    """Raised when transaction validation fails."""
    pass


class DuplicateTransactionError(ValueError):
    """Raised when a duplicate transaction is attempted to be added."""
    pass
