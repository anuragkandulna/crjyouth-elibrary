"""
Unit tests for the Publisher model.
"""

import pytest
from unittest.mock import Mock, patch
from models.publisher import Publisher
from models.exceptions import PublisherNotFoundError


@pytest.mark.unit
class TestPublisher:
    """Test cases for the Publisher model."""
    
    def test_publisher_tablename(self):
        """Test that Publisher has correct table name."""
        assert Publisher.__tablename__ == 'publishers'
    
    def test_publisher_repr(self):
        """Test Publisher string representation."""
        publisher = Publisher()
        publisher.id = 1
        publisher.code = 'PUB1'
        publisher.name = 'Test Publisher'
        
        expected = "<Publisher(id='1', code='PUB1', name='Test Publisher')>"
        assert repr(publisher) == expected


@pytest.mark.unit
class TestCreatePublisher:
    """Test cases for the create_publisher class method."""
    
    def test_create_publisher_success(self):
        """Test successful publisher creation."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        result = Publisher.create_publisher(mock_session, 'PUB1', 'Test Publisher')
        
        assert isinstance(result, Publisher)
        assert result.code == 'PUB1'
        assert result.name == 'Test Publisher'
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_create_publisher_duplicate_code(self):
        """Test publisher creation with duplicate code."""
        existing_publisher = Mock()
        existing_publisher.code = 'PUB1'
        existing_publisher.name = 'Existing Publisher'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_publisher
        
        result = Publisher.create_publisher(mock_session, 'PUB1', 'Test Publisher')
        
        assert result == existing_publisher
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
    
    def test_create_publisher_duplicate_name(self):
        """Test publisher creation with duplicate name."""
        existing_publisher = Mock()
        existing_publisher.code = 'PUB1'
        existing_publisher.name = 'Test Publisher'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_publisher
        
        result = Publisher.create_publisher(mock_session, 'PUB2', 'Test Publisher')
        
        assert result == existing_publisher
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
    
    def test_create_publisher_logs_skip_message(self):
        """Test that duplicate publisher creation logs appropriate message."""
        existing_publisher = Mock()
        existing_publisher.code = 'PUB1'
        existing_publisher.name = 'Test Publisher'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_publisher
        
        with patch('models.publisher.LOGGER') as mock_logger:
            Publisher.create_publisher(mock_session, 'PUB1', 'Test Publisher')
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert "Skipped publication creation" in call_args
            assert "Test Publisher" in call_args
            assert "PUB1" in call_args
    
    def test_create_publisher_logs_success_message(self):
        """Test that successful publisher creation logs appropriate message."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with patch('models.publisher.LOGGER') as mock_logger:
            Publisher.create_publisher(mock_session, 'PUB1', 'Test Publisher')
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "Publisher added: 'PUB1' - 'Test Publisher' added successfully" in call_args


@pytest.mark.unit
class TestDeletePublisher:
    """Test cases for the delete_publisher static method."""
    
    def test_delete_publisher_success(self):
        """Test successful publisher deletion."""
        mock_publisher = Mock()
        mock_publisher.name = 'Test Publisher'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_publisher
        
        Publisher.delete_publisher(mock_session, 'PUB1')
        
        mock_session.delete.assert_called_once_with(mock_publisher)
        mock_session.commit.assert_called_once()
    
    def test_delete_publisher_not_found(self):
        """Test delete_publisher when publisher doesn't exist."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(PublisherNotFoundError, match="Publisher with code 'NONEXISTENT' not found"):
            Publisher.delete_publisher(mock_session, 'NONEXISTENT')
        
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()
    
    def test_delete_publisher_logs_success_message(self):
        """Test that successful deletion logs appropriate message."""
        mock_publisher = Mock()
        mock_publisher.name = 'Test Publisher'
        
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_publisher
        
        with patch('models.publisher.LOGGER') as mock_logger:
            Publisher.delete_publisher(mock_session, 'PUB1')
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "Deleted Test Publisher successfully" in call_args
    
    def test_delete_publisher_logs_error_message(self):
        """Test that failed deletion logs appropriate error message."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with patch('models.publisher.LOGGER') as mock_logger:
            with pytest.raises(PublisherNotFoundError):
                Publisher.delete_publisher(mock_session, 'NONEXISTENT')
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "Publisher with code 'NONEXISTENT' not found" in call_args