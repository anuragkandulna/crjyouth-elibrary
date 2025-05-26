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