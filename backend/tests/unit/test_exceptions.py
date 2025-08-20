"""
Unit tests for custom exceptions.
"""

import pytest
from models.exceptions import (
    DuplicateUserError, DuplicateUserIdError, UserNotFoundError,
    DuplicateBookError, BookNotFoundError, DuplicateBookCopyError,
    BookCopyNotFound, OfficeNotFoundError, WeakPasswordError,
    AuthorNotFoundError, PublisherNotFoundError, GenreNotFoundError,
    LanguageNotFoundError
)


@pytest.mark.unit
class TestExceptions:
    """Test cases for custom exceptions."""

    def test_duplicate_user_error(self):
        """Test DuplicateUserError exception."""
        with pytest.raises(DuplicateUserError, match="Test message"):
            raise DuplicateUserError("Test message")

        assert issubclass(DuplicateUserError, ValueError)


    def test_duplicate_user_id_error(self):
        """Test DuplicateUserIdError exception."""
        with pytest.raises(DuplicateUserIdError, match="Test message"):
            raise DuplicateUserIdError("Test message")

        assert issubclass(DuplicateUserIdError, ValueError)


    def test_user_not_found_error(self):
        """Test UserNotFoundError exception."""
        with pytest.raises(UserNotFoundError, match="Test message"):
            raise UserNotFoundError("Test message")

        assert issubclass(UserNotFoundError, ValueError)


    def test_duplicate_book_error(self):
        """Test DuplicateBookError exception."""
        with pytest.raises(DuplicateBookError, match="Test message"):
            raise DuplicateBookError("Test message")

        assert issubclass(DuplicateBookError, ValueError)


    def test_book_not_found_error(self):
        """Test BookNotFoundError exception."""
        with pytest.raises(BookNotFoundError, match="Test message"):
            raise BookNotFoundError("Test message")

        assert issubclass(BookNotFoundError, ValueError)


    def test_duplicate_book_copy_error(self):
        """Test DuplicateBookCopyError exception."""
        with pytest.raises(DuplicateBookCopyError, match="Test message"):
            raise DuplicateBookCopyError("Test message")

        assert issubclass(DuplicateBookCopyError, ValueError)


    def test_book_copy_not_found(self):
        """Test BookCopyNotFound exception."""
        with pytest.raises(BookCopyNotFound, match="Test message"):
            raise BookCopyNotFound("Test message")

        assert issubclass(BookCopyNotFound, ValueError)


    def test_office_not_found(self):
        """Test OfficeNotFoundError exception."""
        with pytest.raises(OfficeNotFoundError, match="Test message"):
            raise OfficeNotFoundError("Test message")

        assert issubclass(OfficeNotFoundError, ValueError)


    def test_weak_password_error(self):
        """Test WeakPasswordError exception."""
        with pytest.raises(WeakPasswordError, match="Test message"):
            raise WeakPasswordError("Test message")

        assert issubclass(WeakPasswordError, ValueError)

    
    def test_author_not_found_error(self):
        """Test AuthorNotFoundError exception."""
        with pytest.raises(AuthorNotFoundError, match="Test message"):
            raise AuthorNotFoundError("Test message")

        assert issubclass(AuthorNotFoundError, ValueError)


    def test_publisher_not_found_error(self):
        """Test PublisherNotFoundError exception."""
        with pytest.raises(PublisherNotFoundError, match="Test message"):
            raise PublisherNotFoundError("Test message")

        assert issubclass(PublisherNotFoundError, ValueError)


    def test_genre_not_found_error(self):
        """Test GenreNotFoundError exception."""
        with pytest.raises(GenreNotFoundError, match="Test message"):
            raise GenreNotFoundError("Test message")

        assert issubclass(GenreNotFoundError, ValueError)


    def test_language_not_found_error(self):
        """Test LanguageNotFoundError exception."""
        with pytest.raises(LanguageNotFoundError, match="Test message"):
            raise LanguageNotFoundError("Test message")

        assert issubclass(LanguageNotFoundError, ValueError)
