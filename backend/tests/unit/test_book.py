"""
Unit tests for the Book model.
"""

import pytest
from unittest.mock import Mock, patch
from models.book import Book
from models.exceptions import DuplicateBookError, BookNotFoundError


@pytest.mark.unit
class TestBook:
    """Test cases for the Book model."""
    
    def test_book_tablename(self):
        """Test that Book has correct table name."""
        assert Book.__tablename__ == 'books'
    
    def test_book_repr(self):
        """Test Book string representation."""
        book = Book()
        book.book_id = 'AUTH-001'
        book.isbn = '9781234567890'
        book.title = 'Test Book'
        
        expected = "<Book(book_id='AUTH-001', ISBN='9781234567890', title='Test Book')>"
        assert repr(book) == expected


@pytest.mark.unit
class TestGetNextBookNumber:
    """Test cases for the get_next_book_number class method."""
    
    def test_get_next_book_number_with_author(self):
        """Test getting next book number for an author."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = 5
        
        result = Book.get_next_book_number(mock_session, 'AUTH', 'PUB1')
        
        assert result == 6
    
    def test_get_next_book_number_with_publisher_no_author(self):
        """Test getting next book number for publisher when no author."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = 10
        
        result = Book.get_next_book_number(mock_session, None, 'PUB1')
        
        assert result == 11
    
    def test_get_next_book_number_no_existing_books(self):
        """Test getting next book number when no existing books."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        result = Book.get_next_book_number(mock_session, 'AUTH', 'PUB1')
        
        assert result == 1


@pytest.mark.unit
class TestGenerateBookId:
    """Test cases for the generate_book_id class method."""
    
    def test_generate_book_id_basic(self):
        """Test basic book ID generation."""
        result = Book.generate_book_id('AUTH', 1)
        assert result == 'AUTH-001'
    
    def test_generate_book_id_zero_padding(self):
        """Test book ID generation with zero padding."""
        result = Book.generate_book_id('PUB1', 25)
        assert result == 'PUB1-025'
    
    def test_generate_book_id_three_digit_number(self):
        """Test book ID generation with three-digit number."""
        result = Book.generate_book_id('AUTH', 123)
        assert result == 'AUTH-123'


@pytest.mark.unit
class TestCreateBook:
    """Test cases for the create_book class method."""
    
    @patch('models.book.uuid4')
    def test_create_book_success_with_author(self, mock_uuid):
        """Test successful book creation with author."""
        mock_uuid.return_value = 'test-uuid'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.side_effect = [None, 3]  # No existing book, next number is 3
        
        book_data = {
            'isbn': '9781234567890',
            'title': 'Test Book',
            'author_code': 'AUTH',
            'publisher_code': 'PUB1',
            'description': 'A test book',
            'contents': {'chapters': ['Chapter 1', 'Chapter 2']},
            'price': 29.99,
            'category': 'Fiction',
            'language': 'English',
            'base_difficulty': 3,
            'first_publication_year': 2023,
            'is_restricted_book': False
        }
        
        with patch.object(Book, 'get_next_book_number', return_value=3):
            Book.create_book(mock_session, **book_data)
        
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @patch('models.book.uuid4')
    def test_create_book_success_without_author(self, mock_uuid):
        """Test successful book creation without author."""
        mock_uuid.return_value = 'test-uuid'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.side_effect = [None, 5]  # No existing book, next number is 5
        
        book_data = {
            'isbn': '9781234567890',
            'title': 'Test Book',
            'author_code': None,
            'publisher_code': 'PUB1',
            'description': 'A test book',
            'contents': None,
            'price': 29.99,
            'category': 'Fiction',
            'language': 'English',
            'base_difficulty': 3,
            'first_publication_year': 2023,
            'is_restricted_book': False
        }
        
        with patch.object(Book, 'get_next_book_number', return_value=5):
            Book.create_book(mock_session, **book_data)
        
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_create_book_duplicate_isbn(self):
        """Test book creation with duplicate ISBN."""
        existing_book = Mock()
        existing_book.book_id = 'EXISTING-001'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_book
        
        book_data = {
            'isbn': '9781234567890',
            'title': 'Test Book',
            'author_code': 'AUTH',
            'publisher_code': 'PUB1',
            'description': 'A test book',
            'contents': None,
            'price': 29.99,
            'category': 'Fiction',
            'language': 'English',
            'base_difficulty': 3,
            'first_publication_year': 2023
        }
        
        with patch.object(Book, 'get_next_book_number', return_value=1):
            with pytest.raises(DuplicateBookError, match="Book with ISBN or Book id already exists"):
                Book.create_book(mock_session, **book_data)
    
    def test_create_book_duplicate_book_id(self):
        """Test book creation with duplicate book ID."""
        existing_book = Mock()
        existing_book.book_id = 'AUTH-001'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_book
        
        book_data = {
            'isbn': '9781234567891',  # Different ISBN
            'title': 'Test Book',
            'author_code': 'AUTH',
            'publisher_code': 'PUB1',
            'description': 'A test book',
            'contents': None,
            'price': 29.99,
            'category': 'Fiction',
            'language': 'English',
            'base_difficulty': 3,
            'first_publication_year': 2023
        }
        
        with patch.object(Book, 'get_next_book_number', return_value=1):
            with pytest.raises(DuplicateBookError, match="Book with ISBN or Book id already exists"):
                Book.create_book(mock_session, **book_data)


@pytest.mark.unit
class TestGetDetails:
    """Test cases for the get_details static method."""
    
    def test_get_details_success(self):
        """Test successful book details retrieval."""
        mock_book = Mock()
        mock_book.book_uuid = 'test-uuid'
        mock_book.book_id = 'AUTH-001'
        mock_book.language = 'English'
        mock_book.category = 'Fiction'
        mock_book.book_number = 1
        mock_book.isbn = '9781234567890'
        mock_book.title = 'Test Book'
        mock_book.description = 'A test book'
        mock_book.contents = {'chapters': ['Chapter 1']}
        mock_book.price = 29.99
        mock_book.author_code = 'AUTH'
        mock_book.publisher_code = 'PUB1'
        mock_book.base_difficulty = 3
        mock_book.first_publication_year = 2023
        mock_book.is_restricted_book = False
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_book
        
        result = Book.get_details(mock_session, 'AUTH-001')
        
        assert result['Book UUID'] == 'test-uuid'
        assert result['Book ID'] == 'AUTH-001'
        assert result['Title'] == 'Test Book'
        assert result['Book Number'] == '001'
        assert result['Price'] == 29.99
        assert result['Restricted'] is False
    
    def test_get_details_book_not_found(self):
        """Test get_details when book doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(BookNotFoundError, match="Book not found"):
            Book.get_details(mock_session, 'NONEXISTENT-001')


@pytest.mark.unit
class TestEditBook:
    """Test cases for the edit_book static method."""
    
    def test_edit_book_success(self):
        """Test successful book editing."""
        mock_book = Mock()
        mock_book.book_id = 'AUTH-001'
        mock_book.title = 'Old Title'
        mock_book.price = 25.99
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_book
        
        Book.edit_book(mock_session, 'AUTH-001', title='New Title', price=35.99)
        
        assert mock_book.title == 'New Title'
        assert mock_book.price == 35.99
        mock_session.commit.assert_called_once()
    
    def test_edit_book_nonexistent_attribute(self):
        """Test book editing with nonexistent attribute."""
        mock_book = Mock()
        mock_book.book_id = 'AUTH-001'
        
        # Configure mock to not have nonexistent_field attribute
        del mock_book.nonexistent_field  # Remove default Mock attribute if it exists
        mock_book.title = 'Old Title'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_book
        
        Book.edit_book(mock_session, 'AUTH-001', nonexistent_field='value', title='New Title')
        
        assert mock_book.title == 'New Title'
        # The nonexistent_field should not be set because hasattr returns False
        mock_session.commit.assert_called_once()
    
    def test_edit_book_not_found(self):
        """Test edit_book when book doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(BookNotFoundError, match="Book not found"):
            Book.edit_book(mock_session, 'NONEXISTENT-001', title='New Title')


@pytest.mark.unit
class TestDeleteBook:
    """Test cases for the delete_book static method."""
    
    def test_delete_book_success(self):
        """Test successful book deletion."""
        mock_book = Mock()
        mock_book.title = 'Test Book'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_book
        
        Book.delete_book(mock_session, 'AUTH-001')
        
        mock_session.delete.assert_called_once_with(mock_book)
        mock_session.commit.assert_called_once()
    
    def test_delete_book_not_found(self):
        """Test delete_book when book doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(BookNotFoundError, match="Book not found"):
            Book.delete_book(mock_session, 'NONEXISTENT-001')