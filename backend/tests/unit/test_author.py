"""
Unit tests for the Author model.
"""

import pytest
from unittest.mock import Mock, patch
from models.author import Author
from models.exceptions import AuthorNotFoundError


@pytest.mark.unit
class TestAuthor:
    """Test cases for the Author model."""

    def test_author_tablename(self):
        """Test that Author has correct table name."""
        assert Author.__tablename__ == 'authors'


    def test_author_repr(self):
        """Test Author string representation."""
        author = Author()
        author.id = 1
        author.code = 'AUTH'
        author.name = 'Test Author'

        expected = "<Author(id='1', code='AUTH', name='Test Author')>"
        assert repr(author) == expected


@pytest.mark.unit
class TestCreateAuthor:
    """Test cases for the create_author class method."""

    def test_create_author_success(self):
        """Test successful author creation."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        result = Author.create_author(mock_session, 'AUTH', 'Test Author')

        assert isinstance(result, Author)
        assert result.code == 'AUTH'
        assert result.name == 'Test Author'
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


    def test_create_author_duplicate_code(self):
        """Test author creation with duplicate code."""
        existing_author = Mock()
        existing_author.code = 'AUTH'
        existing_author.name = 'Existing Author'

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_author

        result = Author.create_author(mock_session, 'AUTH', 'Test Author')

        assert result == existing_author
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


    def test_create_author_duplicate_name(self):
        """Test author creation with duplicate name."""
        existing_author = Mock()
        existing_author.code = 'AUTH'
        existing_author.name = 'Test Author'

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_author

        result = Author.create_author(mock_session, 'NEWC', 'Test Author')

        assert result == existing_author
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


    def test_create_author_logs_skip_message(self):
        """Test that duplicate author creation logs appropriate message."""
        existing_author = Mock()
        existing_author.code = 'AUTH'
        existing_author.name = 'Test Author'

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_author

        with patch('models.author.LOGGER') as mock_logger:
            Author.create_author(mock_session, 'AUTH', 'Test Author')
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert "Skipped author creation" in call_args
            assert "Test Author" in call_args
            assert "AUTH" in call_args


@pytest.mark.unit
class TestDeleteAuthor:
    """Test cases for the delete_author static method."""

    def test_delete_author_success(self):
        """Test successful author deletion."""
        mock_author = Mock()
        mock_author.name = 'Test Author'

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_author

        Author.delete_author(mock_session, 'AUTH')

        mock_session.delete.assert_called_once_with(mock_author)
        mock_session.commit.assert_called_once()


    def test_delete_author_not_found(self):
        """Test delete_author when author doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(AuthorNotFoundError, match="Author with code 'NONEXISTENT' not found"):
            Author.delete_author(mock_session, 'NONEXISTENT')

        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()


    def test_delete_author_logs_success_message(self):
        """Test that successful deletion logs appropriate message."""
        mock_author = Mock()
        mock_author.name = 'Test Author'

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_author

        with patch('models.author.LOGGER') as mock_logger:
            Author.delete_author(mock_session, 'AUTH')
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "Deleted Test Author successfully" in call_args


    def test_delete_author_logs_error_message(self):
        """Test that failed deletion logs appropriate error message."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with patch('models.author.LOGGER') as mock_logger:
            with pytest.raises(AuthorNotFoundError):
                Author.delete_author(mock_session, 'NONEXISTENT')
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "Author with code 'NONEXISTENT' not found" in call_args
