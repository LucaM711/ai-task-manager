import pytest
import uuid
from repositories.user_repository import UserRepository
from models import User, UserRoles

@pytest.fixture
def user_repo():
    """Crea un'istanza di UserRepository per i test, usando un database di test."""
    repo = UserRepository(db_name = "ai_task_manager_test")
    yield repo
    repo.collection.drop()  # Pulisce la collezione dopo ogni test

@pytest.fixture
def sample_user():
    """Crea un utente di esempio per i test."""
    return User(
        id = str(uuid.uuid4()),
        name = "Test User",
        email = "test@example.com",
        role = UserRoles.USER
    )

def test_insert_user(user_repo, sample_user):
    """Crea un nuovo utente e verifica che venga inserito correttamente."""
    user_id = user_repo.insert(sample_user)
    assert user_id == sample_user.id

def test_find_by_id_existing(user_repo, sample_user):
    user_repo.insert(sample_user)
    found_user = user_repo.find_by_id(sample_user.id)
    assert found_user is not None
    assert found_user.id == sample_user.id
    assert found_user.name == sample_user.name

def test_find_by_id_not_existing(user_repo):
    found_user = user_repo.find_by_id(str(uuid.uuid4()))
    assert found_user is None

def test_find_by_email_existing(user_repo, sample_user):
    user_repo.insert(sample_user)
    found_user = user_repo.find_by_email(sample_user.email)
    assert found_user is not None
    assert found_user.email == sample_user.email
    assert found_user.name == sample_user.name
    assert found_user.role == sample_user.role

def test_find_by_email_not_existing(user_repo):
    found_user = user_repo.find_by_email(str(uuid.uuid4()) + "@example.com")
    assert found_user is None

def test_find_by_role(user_repo, sample_user):
    user_repo.insert(sample_user)
    found_user = user_repo.find_by_role(sample_user.role)
    assert len(found_user) == 1
    assert found_user[0].role == sample_user.role

def test_update_user(user_repo, sample_user):
    user_repo.insert(sample_user)
    sample_user.name = "Update name"
    sample_user.email = "update@example.com"
    sample_user.role = UserRoles.ADMIN
    user_repo.update(sample_user)
    updated_user = user_repo.find_by_id(sample_user.id)
    assert updated_user is not None
    assert updated_user.name == "Update name"
    assert updated_user.email == "update@example.com"
    assert updated_user.role == UserRoles.ADMIN

def test_delete_user(user_repo, sample_user):
    user_repo.insert(sample_user)
    user_repo.delete(sample_user.id)
    deleted_user = user_repo.find_by_id(sample_user.id)
    assert deleted_user is None
