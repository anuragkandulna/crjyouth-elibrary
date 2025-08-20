"""
Unit tests for simpler models: BookGenre, BookLanguage.
"""

import pytest
from unittest.mock import Mock, patch
from models.genre import Genre
from models.language import Language
from models.exceptions import GenreNotFoundError, LanguageNotFoundError


@pytest.mark.unit
class TestBookGenre:
    """Test cases for the BookGenre model."""

    def test_book_genre_tablename(self):
        """Test that BookGenre has correct table name."""
        assert Genre.__tablename__ == 'genres'


    def test_book_genre_repr(self):
        """Test Genre string representation."""
        genre = Genre()
        genre.name = 'Fiction'
        genre.is_active = True

        expected = "<Genre(name='Fiction', active=True)>"
        assert repr(genre) == expected


    def test_create_genre_success(self):
        """Test successful category creation."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        result = Genre.create_genre(mock_session, 'Fiction', 'Fiction books')

        assert isinstance(result, Genre)
        assert result.name == 'Fiction'
        assert result.description == 'Fiction books'
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


    def test_create_genre_existing_active(self):
        """Test category creation when active category already exists."""
        existing_category = Mock()
        existing_category.is_active = True
        existing_category.name = 'Fiction'

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_category

        result = Genre.create_genre(mock_session, 'Fiction', 'Fiction books')

        assert result == existing_category
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


    def test_create_genre_existing_inactive(self):
        """Test category creation when inactive category exists - should reactivate."""
        existing_category = Mock()
        existing_category.is_active = False
        existing_category.name = 'Fiction'

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_category

        result = Genre.create_genre(mock_session, 'Fiction', 'New description')

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

        Genre.delete_genre(mock_session, 'Fiction')

        assert mock_category.is_active is False
        mock_session.commit.assert_called_once()

    def test_delete_category_not_found(self):
        """Test category deletion when category doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(GenreNotFoundError, match="Genre 'NonExistent' not found"):
            Genre.delete_genre(mock_session, 'NonExistent')


@pytest.mark.unit
class TestBookLanguage:
    """Test cases for the BookLanguage model."""

    def test_book_language_tablename(self):
        """Test that BookLanguage has correct table name."""
        assert Language.__tablename__ == 'languages'


    def test_book_language_repr(self):
        """Test Language string representation."""
        language = Language()
        language.language = 'English'
        language.is_active = True

        expected = "<Language(language='English', active=True)>"
        assert repr(language) == expected


    def test_create_language_success(self):
        """Test successful language creation."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        result = Language.create_language(mock_session, 'English')

        assert isinstance(result, Language)
        assert result.language == 'English'
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


    def test_create_language_existing_active(self):
        """Test language creation when active language already exists."""
        existing_language = Mock()
        existing_language.is_active = True
        existing_language.language = 'English'

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_language

        result = Language.create_language(mock_session, 'English')

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

        result = Language.create_language(mock_session, 'English')

        assert result == existing_language
        assert existing_language.is_active is True
        mock_session.commit.assert_called_once()


    def test_delete_language_success(self):
        """Test successful language deletion."""
        mock_language = Mock()
        mock_language.language = 'English'
        mock_language.is_active = True

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_language

        Language.delete_language(mock_session, 'English')

        assert mock_language.is_active is False
        mock_session.commit.assert_called_once()


    def test_delete_language_not_found(self):
        """Test language deletion when language doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(LanguageNotFoundError, match="Language NonExistent not found"):
            Language.delete_language(mock_session, 'NonExistent')
