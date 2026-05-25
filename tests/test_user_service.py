import pytest
from unittest.mock import MagicMock
import uuid
from services.user_service import UserService
from models import User, UserRoles

@pytest.fixture
def mock_user_repo():
    return MagicMock()

@pytest.fixture
def user_service(mock_user_repo):
    return UserService(user_repo=mock_user_repo)

def test_create_user(user_service, mock_user_repo):
    user_data = user_service.create_user(email="test@example.com", name="Test User")
    mock_user_repo.insert.assert_called_once()
    inserted_user = mock_user_repo.insert.call_args[0][0]
    assert inserted_user.email == "test@example.com"
    assert inserted_user.name == "Test User"

def test_get_user_if_exists(user_service, mock_user_repo):
    user_id = str(uuid.uuid4())
    expected_user = MagicMock()
    expected_user.id = user_id
    mock_user_repo.find_by_id.return_value = expected_user
    result = user_service.get_user(user_id)
    mock_user_repo.find_by_id.assert_called_once_with(user_id)
    assert result == expected_user

def test_get_user_not_exists(user_service, mock_user_repo):
    user_id = str(uuid.uuid4())
    mock_user_repo.find_by_id.return_value = None
    with pytest.raises(ValueError):
        user_service.get_user(user_id)
    mock_user_repo.find_by_id.assert_called_once_with(user_id)

def test_get_user_by_email_if_exists(user_service, mock_user_repo):
    expected_user = MagicMock()
    expected_user.email = "test@example.com"
    mock_user_repo.find_by_email.return_value = expected_user
    result = user_service.get_user_by_email("test@example.com")
    mock_user_repo.find_by_email.assert_called_once_with("test@example.com")
    assert result == expected_user

def test_get_user_by_email_not_exists(user_service, mock_user_repo):
    mock_user_repo.find_by_email.return_value = None
    with pytest.raises(ValueError):
        user_service.get_user_by_email("notfound@example.com")
    mock_user_repo.find_by_email.assert_called_once_with("notfound@example.com")

def test_delete_user_if_exists(user_service, mock_user_repo):
    user_id = str(uuid.uuid4())
    mock_user_repo.find_by_id.return_value = MagicMock()
    mock_user_repo.delete.return_value = True
    result = user_service.delete_user(user_id)
    mock_user_repo.find_by_id.assert_called_once()
    mock_user_repo.delete.assert_called_once_with(user_id)
    assert result

def test_delete_user_not_exists(user_service, mock_user_repo):
    mock_user_repo.find_by_id.return_value = None
    with pytest.raises(ValueError):
        user_service.delete_user(str(uuid.uuid4()))
    mock_user_repo.delete.assert_not_called()

def test_update_user(user_service, mock_user_repo):
    user_id = str(uuid.uuid4())
    existing_user = MagicMock()
    existing_user.id = user_id
    existing_user.name = "Old Name"
    mock_user_repo.find_by_id.return_value = existing_user
    mock_user_repo.update.return_value = True
    result = user_service.update_user(user_id, name="New Name")
    mock_user_repo.find_by_id.assert_called_once_with(user_id)
    mock_user_repo.update.assert_called_once()
    assert existing_user.name == "New Name"
    assert result