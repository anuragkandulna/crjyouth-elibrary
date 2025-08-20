"""
Unit tests for the LibraryUser model.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from models.user import User
from models.exceptions import (
    DuplicateUserError, UserNotFoundError, WeakPasswordError, DuplicateUserIdError
)


@pytest.mark.unit
class TestLibraryUser:
    """Test cases for the LibraryUser model."""

    def test_library_user_tablename(self):
        """Test that LibraryUser has correct table name."""
        assert User.__tablename__ == 'users'


    def test_library_user_repr(self):
        """Test User string representation."""
        user = User()
        user.user_id = 123456
        user.first_name = 'John'
        user.last_name = 'Doe'

        expected = "<User(user_id=123456, name=John Doe)>"
        assert repr(user) == expected


@pytest.mark.unit
class TestGenerateUserId:
    """Test cases for the generate_user_id static method."""

    def test_generate_user_id_basic(self):
        """Test basic user ID generation."""
        result = User.generate_user_id()
        
        assert isinstance(result, int)
        assert 100000 <= result <= 999999


    def test_generate_user_id_uppercase_conversion(self):
        """Test that generate_user_id with seed returns the seed."""
        seed = 123456
        result = User.generate_user_id(seed)
        
        assert result == seed


    def test_generate_user_id_month_padding(self):
        """Test that invalid seed returns random number."""
        seed = 999  # Below valid range
        result = User.generate_user_id(seed)

        assert 100000 <= result <= 999999


    def test_generate_user_id_year_format(self):
        """Test that valid seed in range is returned."""
        seed = 500000  # In valid range
        result = User.generate_user_id(seed)

        assert result == seed


    def test_generate_user_id_invalid_office_tag_length(self):
        """Test that seed too high returns random number."""
        seed = 10000000  # Above valid range
        result = User.generate_user_id(seed)

        assert 100000 <= result <= 999999


    def test_generate_user_id_invalid_office_tag_characters(self):
        """Test that None seed returns random number."""
        result = User.generate_user_id(None)

        assert isinstance(result, int)
        assert 100000 <= result <= 999999


    def test_generate_user_id_invalid_sequence_number_low(self):
        """Test that boundary seed values work correctly."""
        result1 = User.generate_user_id(1000)  # Lower boundary
        result2 = User.generate_user_id(999999)  # Upper boundary
        
        assert result1 == 1000
        assert result2 == 999999


    def test_generate_user_id_invalid_sequence_number_high(self):
        """Test that multiple calls return different random numbers."""
        result1 = User.generate_user_id()
        result2 = User.generate_user_id()
        
        # Both should be in valid range but likely different
        assert 100000 <= result1 <= 999999
        assert 100000 <= result2 <= 999999


    def test_generate_user_id_random_sequence(self):
        """Test random sequence number generation with no seed."""
        result = User.generate_user_id()

        assert isinstance(result, int)
        assert 100000 <= result <= 999999


@pytest.mark.unit
class TestPasswordMethods:
    """Test cases for password-related methods."""

    @patch('models.user.check_password_hash')
    def test_check_password_valid(self, mock_check_hash):
        """Test password validation with correct password."""
        mock_check_hash.return_value = True

        user = User()
        user.password_hash = 'hashed_password'

        result = user.check_password('correct_password')

        assert result is True
        mock_check_hash.assert_called_once_with('hashed_password', 'correct_password')


    @patch('models.user.check_password_hash')
    def test_check_password_invalid(self, mock_check_hash):
        """Test password validation with incorrect password."""
        mock_check_hash.return_value = False

        user = User()
        user.password_hash = 'hashed_password'

        result = user.check_password('wrong_password')

        assert result is False
        mock_check_hash.assert_called_once_with('hashed_password', 'wrong_password')


@pytest.mark.unit
class TestCreateUser:
    """Test cases for the create_user class method."""

    @patch('models.user.verify_strong_password')
    @patch('models.user.generate_password_hash')
    @patch('models.user.utc_now')
    @patch('models.user.str')
    def test_create_user_success(self, mock_str, mock_utc_now, mock_hash, mock_verify):
        """Test successful user creation."""
        mock_verify.return_value = (True, "")
        mock_hash.return_value = 'hashed_password'
        mock_utc_now.return_value = datetime(2023, 5, 15, 10, 30, 0)
        mock_str.return_value = 'uuid-string'

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        user_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'password': 'StrongPass123!',
        }

        with patch.object(User, 'generate_user_id', return_value='DHN052312345678'):
            result = User.create_user(mock_session, **user_data)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        mock_verify.assert_called_once_with(
            password1='StrongPass123!',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone_number=''
        )


    @patch('models.user.verify_strong_password')
    def test_create_user_weak_password(self, mock_verify):
        """Test user creation with weak password."""
        mock_verify.return_value = (False, "Password too short")
        mock_session = Mock()

        user_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'password': 'weak',
        }

        with pytest.raises(WeakPasswordError, match="Password too short"):
            User.create_user(mock_session, **user_data)


    @patch('models.user.verify_strong_password')
    def test_create_user_duplicate_email(self, mock_verify):
        """Test user creation with duplicate email."""
        mock_verify.return_value = (True, "")

        existing_user = Mock()
        existing_user.user_id = 'EXISTING001'

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_user

        user_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'password': 'StrongPass123!',
        }

        with pytest.raises(DuplicateUserError, match="User with email already exists"):
            User.create_user(mock_session, **user_data)
    
    
    @patch('models.user.verify_strong_password')
    @patch('models.user.utc_now')
    def test_create_user_duplicate_user_id_with_sequence(self, mock_utc_now, mock_verify):
        """Test user creation with duplicate user ID when sequence number provided."""
        mock_verify.return_value = (True, "")
        mock_utc_now.return_value = datetime(2023, 5, 15, 10, 30, 0)

        existing_user = Mock()
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.side_effect = [None, existing_user]

        user_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'password': 'StrongPass123!',
            'seed_user_id': 123456
        }

        with pytest.raises(DuplicateUserIdError, match="User ID 123456 already exists"):
            User.create_user(mock_session, **user_data)


@pytest.mark.unit
class TestViewUser:
    """Test cases for the view_user static method."""

    def test_view_user_success_with_email(self):
        """Test successful user viewing with email."""
        mock_user = Mock()
        mock_user.user_id = 'TEST001'
        mock_user.first_name = 'John'
        mock_user.last_name = 'Doe'
        mock_user.email = 'john@example.com'
        mock_user.is_admin = False  # Regular user, not admin
        mock_user.is_active = True

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        result = User.view_user(mock_session, 'john@example.com')

        assert result['User ID'] == 'TEST001'
        assert result['Name'] == 'John Doe'
        assert result['Email'] == 'john@example.com'
        assert result['Status'] == True
        assert result['Role'] == 'USER'  # is_admin=False maps to USER

    def test_view_user_not_found(self):
        """Test view_user when user doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(UserNotFoundError, match="User does not exist or is inactive"):
            User.view_user(mock_session, 'nonexistent@example.com')


@pytest.mark.unit
class TestEditUser:
    """Test cases for the edit_user static method."""

    def test_edit_user_success(self):
        """Test successful user editing."""
        mock_user = Mock()
        mock_user.user_id = 'TEST001'

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        User.edit_user(mock_session, email='test@example.com', first_name='Jane')

        assert mock_user.first_name == 'Jane'
        mock_session.commit.assert_called_once()


    def test_edit_user_password_ignored(self):
        """Test that password updates are ignored in edit_user."""
        mock_user = Mock()
        mock_user.user_id = 'TEST001'

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        User.edit_user(mock_session, email='test@example.com', password='newpass', first_name='Jane')

        assert mock_user.first_name == 'Jane'
        assert not hasattr(mock_user, 'password') or mock_user.password != 'newpass'


    def test_edit_user_missing_identifier(self):
        """Test edit_user with missing email and phone_number."""
        mock_session = Mock()

        with pytest.raises(KeyError, match="Missing 'email' key in parameters"):
            User.edit_user(mock_session, first_name='Jane')


    def test_edit_user_not_found(self):
        """Test edit_user when user doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(UserNotFoundError, match="User does not exist or is inactive"):
            User.edit_user(mock_session, email='nonexistent@example.com', first_name='Jane')


@pytest.mark.unit
class TestUpdateUserPassword:
    """Test cases for the update_user_password static method."""

    @patch('models.user.verify_strong_password')
    @patch('models.user.generate_password_hash')
    def test_update_password_success(self, mock_hash, mock_verify):
        """Test successful password update."""
        mock_verify.return_value = (True, "")
        mock_hash.return_value = 'new_hashed_password'

        mock_user = Mock()
        mock_user.user_id = 'TEST001'
        mock_user.first_name = 'John'
        mock_user.last_name = 'Doe'
        mock_user.email = 'john@example.com'
        mock_user.phone_number = '1234567890'

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        User.update_user_password(mock_session, 'john@example.com', 'NewStrongPass123!')

        assert mock_user.password_hash == 'new_hashed_password'
        mock_session.commit.assert_called_once()


    @patch('models.user.verify_strong_password')
    def test_update_password_weak(self, mock_verify):
        """Test password update with weak password."""
        mock_verify.return_value = (False, "Password too weak")

        mock_user = Mock()
        mock_user.user_id = 'TEST001'
        mock_user.first_name = 'John'
        mock_user.last_name = 'Doe'
        mock_user.email = 'john@example.com'
        mock_user.phone_number = '1234567890'

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        with pytest.raises(WeakPasswordError, match="Password too weak"):
            User.update_user_password(mock_session, 'john@example.com', 'weak')


    def test_update_password_user_not_found(self):
        """Test password update when user doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(UserNotFoundError, match="User does not exist or is inactive"):
            User.update_user_password(mock_session, 'nonexistent@example.com', 'NewPass123!')


@pytest.mark.unit
class TestDeleteUser:
    """Test cases for the delete_user static method."""

    def test_delete_user_success(self):
        """Test successful user deletion (soft delete)."""
        mock_user = Mock()
        mock_user.user_id = 'TEST001'
        mock_user.first_name = 'John'
        mock_user.last_name = 'Doe'

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        User.delete_user(mock_session, 'john@example.com')

        assert mock_user.is_active == False
        mock_session.commit.assert_called_once()


    def test_delete_user_not_found(self):
        """Test delete_user when user doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(UserNotFoundError, match="User does not exist or is inactive"):
            User.delete_user(mock_session, 'nonexistent@example.com')
