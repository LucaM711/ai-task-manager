import pytest
from unittest.mock import MagicMock
import uuid
from datetime import datetime, timezone
from services.task_service import TaskService
from models import Task, TaskStatus, TaskPriority

@pytest.fixture
def mock_task_repo():
    return MagicMock()

@pytest.fixture
def mock_project_repo():
    repo = MagicMock()
    repo.find_by_id.return_value = MagicMock()  # progetto sempre trovato nei test
    return repo

@pytest.fixture
def task_service(mock_task_repo, mock_project_repo):
    return TaskService(task_repo=mock_task_repo, project_repo=mock_project_repo)

def test_create_task(task_service, mock_task_repo, mock_project_repo):
    project_id = str(uuid.uuid4())
    task_data = task_service.create_task(title="New Task", project_id=project_id)
    mock_project_repo.find_by_id.assert_called_once_with(project_id)
    mock_task_repo.insert.assert_called_once()
    inserted_task = mock_task_repo.insert.call_args[0][0]
    assert inserted_task.title == "New Task"
    assert inserted_task.project_id == task_data.project_id
    assert inserted_task.year == datetime.now(timezone.utc).year

def test_get_task_if_exists(task_service, mock_task_repo):
    task_id = str(uuid.uuid4())
    expected_task = MagicMock()
    expected_task.id = task_id
    mock_task_repo.find_by_id.return_value = expected_task
    result = task_service.get_task(task_id)
    mock_task_repo.find_by_id.assert_called_once_with(task_id)
    assert result == expected_task

def test_get_task_not_exists(task_service, mock_task_repo):
    task_id = str(uuid.uuid4())
    mock_task_repo.find_by_id.return_value = None
    with pytest.raises(ValueError):
        task_service.get_task(task_id)
    mock_task_repo.find_by_id.assert_called_once_with(task_id)

def test_delete_task_if_exists(task_service, mock_task_repo):
    mock_task = MagicMock()
    mock_task.attachments = []
    mock_task_repo.find_by_id.return_value = mock_task
    mock_task_repo.delete.return_value = True
    result = task_service.delete_task(str(uuid.uuid4()))
    # find_by_id viene chiamato 2 volte: una da get_task, una dal cascade attachments
    assert mock_task_repo.find_by_id.call_count == 2
    mock_task_repo.delete.assert_called_once()
    assert result

def test_delete_task_not_exists(task_service, mock_task_repo):
    mock_task_repo.find_by_id.return_value = None
    with pytest.raises(ValueError):
        task_service.delete_task(str(uuid.uuid4()))
    mock_task_repo.delete.assert_not_called()


def test_update_task_status(task_service, mock_task_repo):
    task_id = str(uuid.uuid4())
    existing_task = MagicMock()
    existing_task.id = task_id
    existing_task.status = TaskStatus.TODO
    mock_task_repo.find_by_id.return_value = existing_task
    mock_task_repo.update.return_value = True
    result = task_service.update_task_status(task_id, new_status=TaskStatus.IN_PROGRESS, changed_by="user123")
    mock_task_repo.find_by_id.assert_called_once_with(task_id)
    mock_task_repo.update.assert_called_once()
    assert existing_task.status == TaskStatus.IN_PROGRESS
    assert result

def test_update_task_priority(task_service, mock_task_repo):
    task_id = str(uuid.uuid4())
    existing_task = MagicMock()
    existing_task.id = task_id
    existing_task.priority = TaskPriority.LOW
    mock_task_repo.find_by_id.return_value = existing_task
    mock_task_repo.update.return_value = True
    result = task_service.update_task_priority(task_id, new_priority=TaskPriority.HIGH, changed_by="user123")
    mock_task_repo.find_by_id.assert_called_once_with(task_id)
    mock_task_repo.update.assert_called_once()
    assert existing_task.priority == TaskPriority.HIGH
    assert result

def test_get_tasks_by_project(task_service, mock_task_repo):
    project_id = str(uuid.uuid4())
    task1 = MagicMock()
    task1.status = TaskStatus.TODO
    task2 = MagicMock()
    task2.status = TaskStatus.IN_PROGRESS
    mock_task_repo.find_by_project.return_value = [task1, task2]
    result = task_service.get_tasks_by_project(project_id)
    mock_task_repo.find_by_project.assert_called_once_with(project_id)
    assert TaskStatus.TODO in result
    assert TaskStatus.IN_PROGRESS in result
    assert result[TaskStatus.TODO] == [task1]
    assert result[TaskStatus.IN_PROGRESS] == [task2]

def test_update_task(task_service, mock_task_repo):
    task = MagicMock()
    task.history = []
    mock_task_repo.update.return_value = True
    result = task_service.update_task(task, field="title", old_value="Old Title", new_value="New Title", changed_by="user123")
    mock_task_repo.update.assert_called_once_with(task)
    assert len(task.history) == 1
    assert task.history[0].field == "title"
    assert task.history[0].old_value == "Old Title"
    assert task.history[0].new_value == "New Title"
    assert task.history[0].changed_by == "user123"
    assert result

def test_get_tasks_by_deadline(task_service, mock_task_repo):
    expected = [MagicMock(), MagicMock()]
    mock_task_repo.find_by_deadline.return_value = expected
    result = task_service.get_tasks_by_deadline(days=7)
    mock_task_repo.find_by_deadline.assert_called_once_with(7)
    assert result == expected

def test_update_task_description(task_service, mock_task_repo):
    task_id = str(uuid.uuid4())
    existing_task = MagicMock()
    existing_task.id = task_id
    existing_task.description = "old desc"
    existing_task.history = []
    mock_task_repo.find_by_id.return_value = existing_task
    mock_task_repo.update.return_value = True
    result = task_service.update_task_description(task_id, "new desc", changed_by="user123")
    mock_task_repo.find_by_id.assert_called_once_with(task_id)
    mock_task_repo.update.assert_called_once()
    assert existing_task.description == "new desc"
    assert len(existing_task.history) == 1
    assert existing_task.history[0].field == "description"
    assert existing_task.history[0].old_value == "old desc"
    assert existing_task.history[0].new_value == "new desc"
    assert result

def test_update_task_description_from_none(task_service, mock_task_repo):
    # caso: descrizione iniziale None → old_value deve essere "" non None (TaskHistory richiede str)
    task_id = str(uuid.uuid4())
    existing_task = MagicMock()
    existing_task.id = task_id
    existing_task.description = None
    existing_task.history = []
    mock_task_repo.find_by_id.return_value = existing_task
    mock_task_repo.update.return_value = True
    task_service.update_task_description(task_id, "first desc", changed_by="user123")
    assert existing_task.history[0].old_value == ""
    assert existing_task.history[0].new_value == "first desc"

def test_get_tasks_by_status(task_service, mock_task_repo):
    expected = [MagicMock(), MagicMock()]
    mock_task_repo.find_by_status.return_value = expected
    result = task_service.get_tasks_by_status(TaskStatus.COMPLETED)
    mock_task_repo.find_by_status.assert_called_once_with(TaskStatus.COMPLETED)
    assert result == expected

def test_get_tasks_by_priority(task_service, mock_task_repo):
    expected = [MagicMock(), MagicMock(), MagicMock()]
    mock_task_repo.find_by_priority.return_value = expected
    result = task_service.get_tasks_by_priority(TaskPriority.HIGH)
    mock_task_repo.find_by_priority.assert_called_once_with(TaskPriority.HIGH)
    assert result == expected

def test_get_tasks_by_title(task_service, mock_task_repo):
    expected = [MagicMock(), MagicMock()]
    mock_task_repo.find_by_title.return_value = expected
    result = task_service.get_tasks_by_title("cv")
    mock_task_repo.find_by_title.assert_called_once_with("cv")
    assert result == expected

def test_delete_tasks(task_service, mock_task_repo):
    task_ids = [str(uuid.uuid4()) for _ in range(3)]
    mock_task_repo.delete_many_by_ids.return_value = 3
    result = task_service.delete_tasks(task_ids)
    mock_task_repo.delete_many_by_ids.assert_called_once_with(task_ids)
    assert result == 3

def test_delete_tasks_empty_list(task_service, mock_task_repo):
    # delega comunque al repo: il guard è nel repo, non nel service
    mock_task_repo.delete_many_by_ids.return_value = 0
    result = task_service.delete_tasks([])
    mock_task_repo.delete_many_by_ids.assert_called_once_with([])
    assert result == 0
