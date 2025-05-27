"""
All exceptions defined here.
"""

class DuplicateUserError(ValueError):
    pass

class UserNotFoundError(ValueError):
    pass

class DuplicateBookError(ValueError):
    pass

class BookNotFoundError(ValueError):
    pass

class DuplicateBookCopyError(ValueError):
    pass

class BookCopyNotFound(ValueError):
    pass

class LibraryOfficeNotFound(ValueError):
    pass

class WeakPasswordError(ValueError):
    pass
