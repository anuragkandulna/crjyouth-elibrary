"""
Unit tests for custom exceptions.
"""

import pytest
from models.exceptions import (
    DuplicateUserError, DuplicateUserIdError, UserNotFoundError,
    DuplicateBookError, BookNotFoundError, DuplicateBookCopyError,
    BookCopyNotFound, LibraryOfficeNotFound, WeakPasswordError,
    DuplicateSpiritualMaturityLevelError, SpiritualMaturityLevelNotFound,
    AuthorNotFoundError, PublisherNotFoundError, SubjectDifficultyTierNotFoundError,
    BookLanguageNotFoundError, BookCategoryNotFoundError,
    DuplicateTransactionError, TransactionNotFoundError,
    InvalidTransactionStateError, TransactionValidationError,
    DuplicateOfficeError, OfficeNotFoundError, OfficeValidationError,
    ReferralCodeNotFoundError, ReferralCodeValidationError, DuplicateReferralError
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
    
    def test_library_office_not_found(self):
        """Test LibraryOfficeNotFound exception."""
        with pytest.raises(LibraryOfficeNotFound, match="Test message"):
            raise LibraryOfficeNotFound("Test message")
        
        assert issubclass(LibraryOfficeNotFound, ValueError)
    
    def test_weak_password_error(self):
        """Test WeakPasswordError exception."""
        with pytest.raises(WeakPasswordError, match="Test message"):
            raise WeakPasswordError("Test message")
        
        assert issubclass(WeakPasswordError, ValueError)
    
    def test_duplicate_spiritual_maturity_level_error(self):
        """Test DuplicateSpiritualMaturityLevelError exception."""
        with pytest.raises(DuplicateSpiritualMaturityLevelError, match="Test message"):
            raise DuplicateSpiritualMaturityLevelError("Test message")
        
        assert issubclass(DuplicateSpiritualMaturityLevelError, ValueError)
    
    def test_spiritual_maturity_level_not_found(self):
        """Test SpiritualMaturityLevelNotFound exception."""
        with pytest.raises(SpiritualMaturityLevelNotFound, match="Test message"):
            raise SpiritualMaturityLevelNotFound("Test message")
        
        assert issubclass(SpiritualMaturityLevelNotFound, ValueError)
    
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
    
    def test_subject_difficulty_tier_not_found_error(self):
        """Test SubjectDifficultyTierNotFoundError exception."""
        with pytest.raises(SubjectDifficultyTierNotFoundError, match="Test message"):
            raise SubjectDifficultyTierNotFoundError("Test message")
        
        assert issubclass(SubjectDifficultyTierNotFoundError, ValueError)
    
    def test_book_language_not_found_error(self):
        """Test BookLanguageNotFoundError exception."""
        with pytest.raises(BookLanguageNotFoundError, match="Test message"):
            raise BookLanguageNotFoundError("Test message")
        
        assert issubclass(BookLanguageNotFoundError, ValueError)
    
    def test_book_category_not_found_error(self):
        """Test BookCategoryNotFoundError exception."""
        with pytest.raises(BookCategoryNotFoundError, match="Test message"):
            raise BookCategoryNotFoundError("Test message")
        
        assert issubclass(BookCategoryNotFoundError, ValueError)
    
    def test_duplicate_transaction_error(self):
        """Test DuplicateTransactionError exception."""
        with pytest.raises(DuplicateTransactionError, match="Test message"):
            raise DuplicateTransactionError("Test message")
        
        assert issubclass(DuplicateTransactionError, ValueError)
    
    def test_transaction_not_found_error(self):
        """Test TransactionNotFoundError exception."""
        with pytest.raises(TransactionNotFoundError, match="Test message"):
            raise TransactionNotFoundError("Test message")
        
        assert issubclass(TransactionNotFoundError, ValueError)
    
    def test_invalid_transaction_state_error(self):
        """Test InvalidTransactionStateError exception."""
        with pytest.raises(InvalidTransactionStateError, match="Test message"):
            raise InvalidTransactionStateError("Test message")
        
        assert issubclass(InvalidTransactionStateError, ValueError)
    
    def test_transaction_validation_error(self):
        """Test TransactionValidationError exception."""
        with pytest.raises(TransactionValidationError, match="Test message"):
            raise TransactionValidationError("Test message")
        
        assert issubclass(TransactionValidationError, ValueError)
    
    def test_duplicate_office_error(self):
        """Test DuplicateOfficeError exception."""
        with pytest.raises(DuplicateOfficeError, match="Test message"):
            raise DuplicateOfficeError("Test message")
        
        assert issubclass(DuplicateOfficeError, ValueError)
    
    def test_office_not_found_error(self):
        """Test OfficeNotFoundError exception."""
        with pytest.raises(OfficeNotFoundError, match="Test message"):
            raise OfficeNotFoundError("Test message")
        
        assert issubclass(OfficeNotFoundError, ValueError)
    
    def test_office_validation_error(self):
        """Test OfficeValidationError exception."""
        with pytest.raises(OfficeValidationError, match="Test message"):
            raise OfficeValidationError("Test message")
        
        assert issubclass(OfficeValidationError, ValueError)
    
    def test_referral_code_not_found_error(self):
        """Test ReferralCodeNotFoundError exception."""
        with pytest.raises(ReferralCodeNotFoundError, match="Test message"):
            raise ReferralCodeNotFoundError("Test message")
        
        assert issubclass(ReferralCodeNotFoundError, ValueError)
    
    def test_referral_code_validation_error(self):
        """Test ReferralCodeValidationError exception."""
        with pytest.raises(ReferralCodeValidationError, match="Test message"):
            raise ReferralCodeValidationError("Test message")
        
        assert issubclass(ReferralCodeValidationError, ValueError)
    
    def test_duplicate_referral_error(self):
        """Test DuplicateReferralError exception."""
        with pytest.raises(DuplicateReferralError, match="Test message"):
            raise DuplicateReferralError("Test message")
        
        assert issubclass(DuplicateReferralError, ValueError)