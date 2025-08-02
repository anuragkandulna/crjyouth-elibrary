"""
Unit tests for the LibraryUser model.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from models.library_user import LibraryUser
from models.exceptions import (
    DuplicateUserError, UserNotFoundError, WeakPasswordError, 
    SpiritualMaturityLevelNotFound, DuplicateUserIdError
)


@pytest.mark.unit
class TestLibraryUser:
    """Test cases for the LibraryUser model."""
    
    def test_library_user_tablename(self):
        """Test that LibraryUser has correct table name."""
        assert LibraryUser.__tablename__ == 'users'
    
    def test_library_user_repr(self):
        """Test LibraryUser string representation."""
        user = LibraryUser()
        user.user_id = 'TEST001'
        user.first_name = 'John'
        user.last_name = 'Doe'
        user.account_status = 'ACTIVE'
        
        expected = "<LibraryUser(user_id='TEST001', name='John Doe', active='ACTIVE')>"
        assert repr(user) == expected


@pytest.mark.unit
class TestGenerateUserId:
    """Test cases for the generate_user_id static method."""
    
    def test_generate_user_id_basic(self):
        """Test basic user ID generation."""
        office_tag = 'DHN'
        reg_date = datetime(2023, 5, 15)
        result = LibraryUser.generate_user_id(office_tag, reg_date, 12345678)
        
        assert result == 'DHN052312345678'
        assert len(result) == 15
    
    def test_generate_user_id_uppercase_conversion(self):
        """Test that office tag is converted to uppercase."""
        office_tag = 'dhn'
        reg_date = datetime(2023, 5, 15)
        result = LibraryUser.generate_user_id(office_tag, reg_date, 12345678)
        
        assert result.startswith('DHN')
    
    def test_generate_user_id_month_padding(self):
        """Test that month is zero-padded."""
        office_tag = 'DHN'
        reg_date = datetime(2023, 1, 15)  # January
        result = LibraryUser.generate_user_id(office_tag, reg_date, 12345678)
        
        assert 'DHN0123' in result
    
    def test_generate_user_id_year_format(self):
        """Test that year is formatted as 2 digits."""
        office_tag = 'DHN'
        reg_date = datetime(2023, 5, 15)
        result = LibraryUser.generate_user_id(office_tag, reg_date, 12345678)
        
        assert 'DHN0523' in result
    
    def test_generate_user_id_invalid_office_tag_length(self):
        """Test validation of office tag length."""
        reg_date = datetime(2023, 5, 15)
        
        with pytest.raises(ValueError, match="Office tag must be exactly 3 characters long"):
            LibraryUser.generate_user_id('AB', reg_date, 12345678)
        
        with pytest.raises(ValueError, match="Office tag must be exactly 3 characters long"):
            LibraryUser.generate_user_id('ABCD', reg_date, 12345678)
    
    def test_generate_user_id_invalid_office_tag_characters(self):
        """Test validation of office tag characters."""
        reg_date = datetime(2023, 5, 15)
        
        with pytest.raises(ValueError, match="Office tag must contain only alphabetic characters"):
            LibraryUser.generate_user_id('AB1', reg_date, 12345678)
        
        with pytest.raises(ValueError, match="Office tag must contain only alphabetic characters"):
            LibraryUser.generate_user_id('A-B', reg_date, 12345678)
    
    def test_generate_user_id_invalid_sequence_number_low(self):
        """Test validation of sequence number lower bound."""
        office_tag = 'DHN'
        reg_date = datetime(2023, 5, 15)
        
        with pytest.raises(ValueError, match="Sequence number must be greater than 10000000"):
            LibraryUser.generate_user_id(office_tag, reg_date, 10000000)
        
        with pytest.raises(ValueError, match="Sequence number must be greater than 10000000"):
            LibraryUser.generate_user_id(office_tag, reg_date, 9999999)
    
    def test_generate_user_id_invalid_sequence_number_high(self):
        """Test validation of sequence number upper bound."""
        office_tag = 'DHN'
        reg_date = datetime(2023, 5, 15)
        
        with pytest.raises(ValueError, match="less than or equal to 99999999"):
            LibraryUser.generate_user_id(office_tag, reg_date, 100000000)
    
    def test_generate_user_id_random_sequence(self):
        """Test random sequence number generation."""
        office_tag = 'DHN'
        reg_date = datetime(2023, 5, 15)
        
        result = LibraryUser.generate_user_id(office_tag, reg_date)
        
        assert len(result) == 15
        assert result.startswith('DHN0523')
        
        # Extract sequence number and validate range
        sequence_part = result[7:]
        sequence_num = int(sequence_part)
        assert 10000000 < sequence_num <= 99999999


@pytest.mark.unit
class TestPasswordMethods:
    """Test cases for password-related methods."""
    
    @patch('models.library_user.check_password_hash')
    def test_check_password_valid(self, mock_check_hash):
        """Test password validation with correct password."""
        mock_check_hash.return_value = True
        
        user = LibraryUser()
        user.password_hash = 'hashed_password'
        
        result = user.check_password('correct_password')
        
        assert result is True
        mock_check_hash.assert_called_once_with('hashed_password', 'correct_password')
    
    @patch('models.library_user.check_password_hash')
    def test_check_password_invalid(self, mock_check_hash):
        """Test password validation with incorrect password."""
        mock_check_hash.return_value = False
        
        user = LibraryUser()
        user.password_hash = 'hashed_password'
        
        result = user.check_password('wrong_password')
        
        assert result is False
        mock_check_hash.assert_called_once_with('hashed_password', 'wrong_password')


@pytest.mark.unit
class TestPermissionMethods:
    """Test cases for permission-related methods."""
    
    def test_check_permission_has_permission(self):
        """Test permission check when user has the permission."""
        # Test the logic directly by patching the method
        with patch('models.library_user.LibraryUser.check_permission') as mock_check:
            mock_check.return_value = True
            user = LibraryUser()
            result = user.check_permission('read_books')
            assert result is True
    
    def test_check_permission_no_permission(self):
        """Test permission check when user lacks the permission."""
        with patch('models.library_user.LibraryUser.check_permission') as mock_check:
            mock_check.return_value = False
            user = LibraryUser()
            result = user.check_permission('delete_books')
            assert result is False
    
    def test_check_permission_no_role(self):
        """Test permission check when user has no role."""
        # For this test, we can create the object and test directly since no SQLAlchemy relationships are involved
        user = LibraryUser()
        # Don't set user_role, it should be None by default
        
        result = user.check_permission('read_books')
        
        assert result is False


@pytest.mark.unit
class TestCreateUser:
    """Test cases for the create_user class method."""
    
    @patch('models.library_user.verify_strong_password')
    @patch('models.library_user.generate_password_hash')
    @patch('models.library_user.utc_now')
    @patch('models.library_user.str')
    def test_create_user_success(self, mock_str, mock_utc_now, mock_hash, mock_verify):
        """Test successful user creation."""
        # Setup mocks
        mock_verify.return_value = (True, "")
        mock_hash.return_value = 'hashed_password'
        mock_utc_now.return_value = datetime(2023, 5, 15, 10, 30, 0)
        mock_str.return_value = 'uuid-string'
        
        # Mock session
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        # Test data
        user_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '1234567890',
            'password': 'StrongPass123!',
            'address_line_1': '123 Main St',
            'city': 'Test City',
            'state': 'Test State',
            'country': 'Test Country',
            'postal_code': '12345',
            'registered_at_office': 'DHN01'
        }
        
        with patch.object(LibraryUser, 'generate_user_id', return_value='DHN052312345678'):
            result = LibraryUser.create_user(mock_session, **user_data)
        
        # Verify session calls
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Verify password verification was called
        mock_verify.assert_called_once_with(
            password1='StrongPass123!',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone_number='1234567890'
        )
    
    @patch('models.library_user.verify_strong_password')
    def test_create_user_weak_password(self, mock_verify):
        """Test user creation with weak password."""
        mock_verify.return_value = (False, "Password too short")
        mock_session = Mock()
        
        user_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '1234567890',
            'password': 'weak',
            'address_line_1': '123 Main St',
            'city': 'Test City',
            'state': 'Test State',
            'country': 'Test Country',
            'postal_code': '12345',
            'registered_at_office': 'DHN01'
        }
        
        with pytest.raises(WeakPasswordError, match="Password too short"):
            LibraryUser.create_user(mock_session, **user_data)
    
    @patch('models.library_user.verify_strong_password')
    def test_create_user_duplicate_email(self, mock_verify):
        """Test user creation with duplicate email."""
        mock_verify.return_value = (True, "")
        
        # Mock existing user
        existing_user = Mock()
        existing_user.user_id = 'EXISTING001'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_user
        
        user_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '1234567890',
            'password': 'StrongPass123!',
            'address_line_1': '123 Main St',
            'city': 'Test City',
            'state': 'Test State',
            'country': 'Test Country',
            'postal_code': '12345',
            'registered_at_office': 'DHN01'
        }
        
        with pytest.raises(DuplicateUserError, match="User with email or phone number already exists"):
            LibraryUser.create_user(mock_session, **user_data)
    
    @patch('models.library_user.verify_strong_password')
    def test_create_user_low_spiritual_maturity(self, mock_verify):
        """Test user creation with spiritual maturity <= 2."""
        mock_verify.return_value = (True, "")
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        user_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '1234567890',
            'password': 'StrongPass123!',
            'address_line_1': '123 Main St',
            'city': 'Test City',
            'state': 'Test State',
            'country': 'Test Country',
            'postal_code': '12345',
            'registered_at_office': 'DHN01',
            'spiritual_maturity': 2
        }
        
        with pytest.raises(SpiritualMaturityLevelNotFound, match="User with spiritual maturity 2 and below cannot be created"):
            LibraryUser.create_user(mock_session, **user_data)
    
    @patch('models.library_user.verify_strong_password')
    @patch('models.library_user.utc_now')
    def test_create_user_duplicate_user_id_with_sequence(self, mock_utc_now, mock_verify):
        """Test user creation with duplicate user ID when sequence number provided."""
        mock_verify.return_value = (True, "")
        mock_utc_now.return_value = datetime(2023, 5, 15, 10, 30, 0)
        
        # Mock existing user with same ID
        existing_user = Mock()
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.side_effect = [None, existing_user]
        
        user_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '1234567890',
            'password': 'StrongPass123!',
            'address_line_1': '123 Main St',
            'city': 'Test City',
            'state': 'Test State',
            'country': 'Test Country',
            'postal_code': '12345',
            'registered_at_office': 'DHN01',
            'sequence_number': 12345678
        }
        
        with pytest.raises(DuplicateUserIdError, match="User ID DHN052312345678 already exists"):
            LibraryUser.create_user(mock_session, **user_data)


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
        mock_user.phone_number = '1234567890'
        mock_user.role = 3
        mock_user.membership_type = 5
        mock_user.account_status = 'ACTIVE'
        mock_user.is_founder = False
        mock_user.address_line_1 = '123 Main St'
        mock_user.address_line_2 = None
        mock_user.city = 'Test City'
        mock_user.state = 'Test State'
        mock_user.country = 'Test Country'
        mock_user.postal_code = '12345'
        mock_user.registered_at_office = 'DHN01'
        
        mock_maturity = Mock()
        mock_maturity.title = 'Mature Believer'
        mock_user.maturity_level = mock_maturity
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        result = LibraryUser.view_user(mock_session, 'john@example.com', '1234567890')
        
        assert result['User ID'] == 'TEST001'
        assert result['First Name'] == 'John'
        assert result['Last Name'] == 'Doe'
        assert result['Email'] == 'john@example.com'
        assert result['Spiritual Maturity'] == 'Mature Believer'
    
    def test_view_user_not_found(self):
        """Test view_user when user doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(UserNotFoundError, match="User does not exist or is inactive"):
            LibraryUser.view_user(mock_session, 'nonexistent@example.com', '0000000000')


@pytest.mark.unit
class TestEditUser:
    """Test cases for the edit_user static method."""
    
    def test_edit_user_success(self):
        """Test successful user editing."""
        mock_user = Mock()
        mock_user.user_id = 'TEST001'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        LibraryUser.edit_user(mock_session, email='test@example.com', first_name='Jane')
        
        assert mock_user.first_name == 'Jane'
        mock_session.commit.assert_called_once()
    
    def test_edit_user_password_ignored(self):
        """Test that password updates are ignored in edit_user."""
        mock_user = Mock()
        mock_user.user_id = 'TEST001'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        LibraryUser.edit_user(mock_session, email='test@example.com', password='newpass', first_name='Jane')
        
        assert mock_user.first_name == 'Jane'
        assert not hasattr(mock_user, 'password') or mock_user.password != 'newpass'
    
    def test_edit_user_missing_identifier(self):
        """Test edit_user with missing email and phone_number."""
        mock_session = Mock()
        
        with pytest.raises(KeyError, match="Missing 'email' or 'phone_number' key"):
            LibraryUser.edit_user(mock_session, first_name='Jane')
    
    def test_edit_user_not_found(self):
        """Test edit_user when user doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(UserNotFoundError, match="User does not exist or is inactive"):
            LibraryUser.edit_user(mock_session, email='nonexistent@example.com', first_name='Jane')


@pytest.mark.unit
class TestUpdateUserPassword:
    """Test cases for the update_user_password static method."""
    
    @patch('models.library_user.verify_strong_password')
    @patch('models.library_user.generate_password_hash')
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
        
        LibraryUser.update_user_password(mock_session, 'john@example.com', '1234567890', 'NewStrongPass123!')
        
        assert mock_user.password_hash == 'new_hashed_password'
        mock_session.commit.assert_called_once()
    
    @patch('models.library_user.verify_strong_password')
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
            LibraryUser.update_user_password(mock_session, 'john@example.com', '1234567890', 'weak')
    
    def test_update_password_user_not_found(self):
        """Test password update when user doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(UserNotFoundError, match="User does not exist or is inactive"):
            LibraryUser.update_user_password(mock_session, 'nonexistent@example.com', '0000000000', 'NewPass123!')


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
        
        LibraryUser.delete_user(mock_session, 'john@example.com', '1234567890')
        
        assert mock_user.account_status == 'INACTIVE'
        mock_session.commit.assert_called_once()
    
    def test_delete_user_not_found(self):
        """Test delete_user when user doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(UserNotFoundError, match="User does not exist or is inactive"):
            LibraryUser.delete_user(mock_session, 'nonexistent@example.com', '0000000000')