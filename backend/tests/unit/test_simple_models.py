"""
Unit tests for simpler models: BookCategory, BookLanguage, and StatusCode.
"""

import pytest
from unittest.mock import Mock, patch
from models.book_category import BookCategory
from models.book_language import BookLanguage
from models.status_codes import StatusCode
from models.exceptions import BookCategoryNotFoundError, BookLanguageNotFoundError


@pytest.mark.unit
class TestBookCategory:
    """Test cases for the BookCategory model."""
    
    def test_book_category_tablename(self):
        """Test that BookCategory has correct table name."""
        assert BookCategory.__tablename__ == 'book_categories'
    
    def test_book_category_repr(self):
        """Test BookCategory string representation."""
        category = BookCategory()
        category.name = 'Fiction'
        category.is_active = True
        
        expected = "<BookCategory(name='Fiction', active=True)>"
        assert repr(category) == expected
    
    def test_create_category_success(self):
        """Test successful category creation."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        result = BookCategory.create_category(mock_session, 'Fiction', 'Fiction books')
        
        assert isinstance(result, BookCategory)
        assert result.name == 'Fiction'
        assert result.description == 'Fiction books'
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_create_category_existing_active(self):
        """Test category creation when active category already exists."""
        existing_category = Mock()
        existing_category.is_active = True
        existing_category.name = 'Fiction'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_category
        
        result = BookCategory.create_category(mock_session, 'Fiction', 'Fiction books')
        
        assert result == existing_category
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
    
    def test_create_category_existing_inactive(self):
        """Test category creation when inactive category exists - should reactivate."""
        existing_category = Mock()
        existing_category.is_active = False
        existing_category.name = 'Fiction'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_category
        
        result = BookCategory.create_category(mock_session, 'Fiction', 'New description')
        
        assert result == existing_category
        assert existing_category.is_active is True
        assert existing_category.description == 'New description'
        mock_session.commit.assert_called_once()
    
    def test_delete_category_success(self):
        """Test successful category deletion."""
        mock_category = Mock()
        mock_category.name = 'Fiction'
        mock_category.is_active = True
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_category
        
        BookCategory.delete_category(mock_session, 'Fiction')
        
        assert mock_category.is_active is False
        mock_session.commit.assert_called_once()
    
    def test_delete_category_not_found(self):
        """Test category deletion when category doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(BookCategoryNotFoundError, match="Book category 'NonExistent' not found"):
            BookCategory.delete_category(mock_session, 'NonExistent')


@pytest.mark.unit
class TestBookLanguage:
    """Test cases for the BookLanguage model."""
    
    def test_book_language_tablename(self):
        """Test that BookLanguage has correct table name."""
        assert BookLanguage.__tablename__ == 'book_languages'
    
    def test_book_language_repr(self):
        """Test BookLanguage string representation."""
        language = BookLanguage()
        language.language = 'English'
        language.is_active = True
        
        expected = "<BookLanguage(language='English', active=True)>"
        assert repr(language) == expected
    
    def test_create_language_success(self):
        """Test successful language creation."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        result = BookLanguage.create_language(mock_session, 'English', 'English language')
        
        assert isinstance(result, BookLanguage)
        assert result.language == 'English'
        assert result.description == 'English language'
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_create_language_existing_active(self):
        """Test language creation when active language already exists."""
        existing_language = Mock()
        existing_language.is_active = True
        existing_language.language = 'English'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_language
        
        result = BookLanguage.create_language(mock_session, 'English', 'English language')
        
        assert result == existing_language
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
    
    def test_create_language_existing_inactive(self):
        """Test language creation when inactive language exists - should reactivate."""
        existing_language = Mock()
        existing_language.is_active = False
        existing_language.language = 'English'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_language
        
        result = BookLanguage.create_language(mock_session, 'English', 'New description')
        
        assert result == existing_language
        assert existing_language.is_active is True
        assert existing_language.description == 'New description'
        mock_session.commit.assert_called_once()
    
    def test_delete_language_success(self):
        """Test successful language deletion."""
        mock_language = Mock()
        mock_language.language = 'English'
        mock_language.is_active = True
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_language
        
        BookLanguage.delete_language(mock_session, 'English')
        
        assert mock_language.is_active is False
        mock_session.commit.assert_called_once()
    
    def test_delete_language_not_found(self):
        """Test language deletion when language doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(BookLanguageNotFoundError, match="Language NonExistent not found"):
            BookLanguage.delete_language(mock_session, 'NonExistent')


@pytest.mark.unit
class TestStatusCode:
    """Test cases for the StatusCode model."""
    
    def test_status_code_tablename(self):
        """Test that StatusCode has correct table name."""
        assert StatusCode.__tablename__ == 'status_codes'
    
    def test_status_code_repr(self):
        """Test StatusCode string representation."""
        status = StatusCode()
        status.code = 'ACTIVE'
        status.category = 'Account Status'
        status.description = 'Account is active'
        
        expected = "<StatusCode(code='ACTIVE', category='Account Status', description='Account is active')>"
        assert repr(status) == expected
    
    @patch('models.status_codes.STATUS_CODE_CATEGORY', ['TEST_CATEGORY', 'ANOTHER_CATEGORY'])
    def test_is_valid_category_true(self):
        """Test is_valid_category returns True for valid category."""
        result = StatusCode.is_valid_category('TEST_CATEGORY')
        assert result is True
    
    @patch('models.status_codes.STATUS_CODE_CATEGORY', ['TEST_CATEGORY', 'ANOTHER_CATEGORY'])
    def test_is_valid_category_false(self):
        """Test is_valid_category returns False for invalid category."""
        result = StatusCode.is_valid_category('INVALID_CATEGORY')
        assert result is False
    
    def test_create_new_code_success(self):
        """Test successful status code creation."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with patch.object(StatusCode, 'is_valid_category', return_value=True):
            result = StatusCode.create_new_code(
                mock_session, 'ACTIVE', 'Account Status', 'Account is active'
            )
        
        assert isinstance(result, StatusCode)
        assert result.code == 'ACTIVE'
        assert result.category == 'Account Status'
        assert result.description == 'Account is active'
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_create_new_code_duplicate(self):
        """Test status code creation with duplicate code."""
        existing_status = Mock()
        existing_status.code = 'ACTIVE'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_status
        
        with pytest.raises(ValueError, match="Status code ACTIVE already exists"):
            StatusCode.create_new_code(
                mock_session, 'ACTIVE', 'Account Status', 'Account is active'
            )
    
    def test_create_new_code_invalid_category(self):
        """Test status code creation with invalid category."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with patch.object(StatusCode, 'is_valid_category', return_value=False):
            with pytest.raises(ValueError, match="Status code category Invalid Category does not exist"):
                StatusCode.create_new_code(
                    mock_session, 'ACTIVE', 'Invalid Category', 'Account is active'
                )
    
    def test_delete_status_code_success(self):
        """Test successful status code deletion."""
        mock_status = Mock()
        mock_status.code = 'ACTIVE'
        mock_status.category = 'Account Status'
        mock_status.is_active = True
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_status
        
        StatusCode.delete_status_code(mock_session, 'ACTIVE')
        
        assert mock_status.is_active is False
        mock_session.commit.assert_called_once()
    
    def test_delete_status_code_not_found(self):
        """Test status code deletion when code doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(ValueError, match="Status code NONEXISTENT not found or is already deleted"):
            StatusCode.delete_status_code(mock_session, 'NONEXISTENT')