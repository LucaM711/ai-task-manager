import pytest
import uuid
from repositories.project_repository import ProjectRepository
from models import Project

@pytest.fixture
def project_repo():
    repo = ProjectRepository(db_name="ai_task_manager_test")
    yield repo
    repo.collection.drop()

@pytest.fixture
def sample_project():
    return Project(
        id=str(uuid.uuid4()),
        name="Test Project",
        description="Progetto di test",
        members=[]
    )

def test_insert_project(project_repo, sample_project):
    project_id = project_repo.insert(sample_project)
    assert project_id == sample_project.id

def test_find_by_id_existing(project_repo, sample_project):
    project_id = project_repo.insert(sample_project)
    found_project = project_repo.find_by_id(project_id)
    assert found_project is not None
    assert found_project.id == sample_project.id
    assert found_project.name == sample_project.name

def test_find_by_id_not_existing(project_repo):
    project_id = str(uuid.uuid4())
    found_project = project_repo.find_by_id(project_id)
    assert found_project is None

def test_find_by_name_existing(project_repo, sample_project):
    project_id = project_repo.insert(sample_project)
    found_project = project_repo.find_by_name(sample_project.name)
    assert found_project is not None
    assert found_project.id == sample_project.id

def test_find_by_name_not_existing(project_repo):
    found_project = project_repo.find_by_name("Non Existing Project")
    assert found_project is None

def test_find_by_member(project_repo, sample_project):
    member_id = str(uuid.uuid4())
    sample_project.members.append(member_id)
    project_repo.insert(sample_project)
    found_projects = project_repo.find_by_member(member_id)
    assert len(found_projects) == 1
    assert found_projects[0].id == sample_project.id

def test_find_all(project_repo, sample_project):
    project_repo.insert(sample_project)
    found_projects = project_repo.find_all()
    assert len(found_projects) >= 1

def test_update_project(project_repo, sample_project):
    project_id = project_repo.insert(sample_project)
    sample_project.name = "Updated Project Name"
    sample_project.description = "Updated description"
    project_repo.update(sample_project)
    updated_project = project_repo.find_by_id(project_id)
    assert updated_project.name == "Updated Project Name"
    assert updated_project.description == "Updated description"

def test_delete_project(project_repo, sample_project):
    project_id = project_repo.insert(sample_project)
    project_repo.delete(project_id)
    deleted_project = project_repo.find_by_id(project_id)
    assert deleted_project is None