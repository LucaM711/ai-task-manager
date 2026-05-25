from repositories.task_repository import TaskRepository
from models import Task, TaskStatus, TaskPriority
import uuid
import pytest
from datetime import datetime, timezone, timedelta

@pytest.fixture
def task_repo():
    repo = TaskRepository(db_name = "ai_task_manager_test")
    yield repo
    repo.collection.drop()  # Pulisce la collezione dopo ogni test

@pytest.fixture
def sample_task():
    return Task(
        id=str(uuid.uuid4()),
        project_id=str(uuid.uuid4()),
        title="Test Task",
        year=datetime.now(timezone.utc).year
    )

def test_insert_task(task_repo, sample_task):
    task_id = task_repo.insert(sample_task)
    assert task_id == sample_task.id

def test_find_by_id_existing(task_repo, sample_task):
    task_repo.insert(sample_task)
    found_task = task_repo.find_by_id(sample_task.id)
    assert found_task is not None
    assert found_task.id == sample_task.id
    assert found_task.title == sample_task.title

def test_find_by_id_not_existing(task_repo):
    found_task = task_repo.find_by_id(str(uuid.uuid4()))
    assert found_task is None

def test_find_by_project(task_repo, sample_task):
    task_repo.insert(sample_task)
    found_tasks = task_repo.find_by_project(sample_task.project_id)
    assert len(found_tasks) == 1
    assert found_tasks[0].project_id == sample_task.project_id

def test_find_by_status(task_repo, sample_task):
    task_repo.insert(sample_task)
    found_tasks = task_repo.find_by_status(TaskStatus.TODO)
    assert len(found_tasks) == 1
    assert found_tasks[0].status == TaskStatus.TODO

def test_find_by_priority(task_repo, sample_task):
    task_repo.insert(sample_task)
    found_tasks = task_repo.find_by_priority(TaskPriority.MEDIUM)
    assert len(found_tasks) == 1
    assert found_tasks[0].priority == TaskPriority.MEDIUM

def test_find_by_title_case_insensitive(task_repo, sample_task):
    sample_task.title = "Aggiornare CV"
    task_repo.insert(sample_task)
    # match esatto
    assert len(task_repo.find_by_title("Aggiornare CV")) == 1
    # case-insensitive
    assert len(task_repo.find_by_title("aggiornare cv")) == 1
    # match parziale (substring)
    assert len(task_repo.find_by_title("CV")) == 1
    assert len(task_repo.find_by_title("aggiornare")) == 1

def test_find_by_title_no_match(task_repo, sample_task):
    sample_task.title = "Aggiornare CV"
    task_repo.insert(sample_task)
    assert task_repo.find_by_title("inesistente") == []

def test_find_by_title_multiple_matches(task_repo):
    # due task con "CV" nel titolo
    t1 = Task(id=str(uuid.uuid4()), project_id=str(uuid.uuid4()),
              title="Aggiornare CV", year=datetime.now(timezone.utc).year)
    t2 = Task(id=str(uuid.uuid4()), project_id=str(uuid.uuid4()),
              title="Rivedere CV con cliente", year=datetime.now(timezone.utc).year)
    t3 = Task(id=str(uuid.uuid4()), project_id=str(uuid.uuid4()),
              title="Altro task", year=datetime.now(timezone.utc).year)
    for t in (t1, t2, t3):
        task_repo.insert(t)
    found = task_repo.find_by_title("cv")
    assert len(found) == 2

def test_find_by_title_special_chars_safe(task_repo, sample_task):
    # re.escape deve neutralizzare i metacharacter regex
    sample_task.title = "Task (importante)"
    task_repo.insert(sample_task)
    # se non fosse escapato, '(' darebbe errore regex o match non voluto
    assert len(task_repo.find_by_title("(importante)")) == 1
    # un pattern come '.+' NON deve matchare tutto: deve cercare la stringa letterale
    assert task_repo.find_by_title(".+") == []

def test_find_urgent_tasks(task_repo, sample_task):
    sample_task.priority = TaskPriority.HIGH
    sample_task.due_date = datetime.now(timezone.utc) + timedelta(days=1)
    task_repo.insert(sample_task)
    found_tasks = task_repo.find_urgent_tasks()
    assert len(found_tasks) == 1
    assert found_tasks[0].id == sample_task.id
    assert found_tasks[0].priority == TaskPriority.HIGH

def test_find_by_deadline(task_repo, sample_task):
    # task con scadenza tra 2 giorni → deve apparire nei "prossimi 7 giorni"
    sample_task.due_date = datetime.now(timezone.utc) + timedelta(days=2)
    task_repo.insert(sample_task)
    found = task_repo.find_by_deadline(days=7)
    assert len(found) == 1
    assert found[0].id == sample_task.id

def test_find_by_deadline_excludes_completed(task_repo, sample_task):
    sample_task.due_date = datetime.now(timezone.utc) + timedelta(days=2)
    sample_task.status = TaskStatus.COMPLETED
    task_repo.insert(sample_task)
    found = task_repo.find_by_deadline(days=7)
    assert len(found) == 0

def test_update_task(task_repo, sample_task):
    task_repo.insert(sample_task)
    original_updated_at = sample_task.updated_at  # salva PRIMA dell'update
    sample_task.title = "Updated Task"
    sample_task.status = TaskStatus.IN_PROGRESS
    sample_task.priority = TaskPriority.HIGH
    task_repo.update(sample_task)                  # un solo update
    updated_task = task_repo.find_by_id(sample_task.id)
    assert updated_task is not None                # is not None va PRIMA degli altri assert
    assert updated_task.title == "Updated Task"
    assert updated_task.status == TaskStatus.IN_PROGRESS
    assert updated_task.priority == TaskPriority.HIGH
    assert updated_task.updated_at.replace(tzinfo=timezone.utc) > original_updated_at

def test_delete_task(task_repo, sample_task):
    task_repo.insert(sample_task)
    task_repo.delete(sample_task.id)
    deleted_task = task_repo.find_by_id(sample_task.id)
    assert deleted_task is None

def test_delete_many_by_ids(task_repo):
    # inserisce 3 task, ne cancella 2 in una sola query
    tasks = [
        Task(id=str(uuid.uuid4()), project_id=str(uuid.uuid4()), title=f"T{i}",
             year=datetime.now(timezone.utc).year)
        for i in range(3)
    ]
    for t in tasks:
        task_repo.insert(t)
    deleted = task_repo.delete_many_by_ids([tasks[0].id, tasks[1].id])
    assert deleted == 2
    assert task_repo.find_by_id(tasks[0].id) is None
    assert task_repo.find_by_id(tasks[1].id) is None
    assert task_repo.find_by_id(tasks[2].id) is not None

def test_delete_many_by_ids_empty_list(task_repo, sample_task):
    # guard: lista vuota non deve generare query $in: [] né cancellare nulla
    task_repo.insert(sample_task)
    deleted = task_repo.delete_many_by_ids([])
    assert deleted == 0
    assert task_repo.find_by_id(sample_task.id) is not None

def test_delete_many_by_ids_nonexistent(task_repo, sample_task):
    # id che non esistono → 0 cancellati, task reale resta
    task_repo.insert(sample_task)
    deleted = task_repo.delete_many_by_ids([str(uuid.uuid4()), str(uuid.uuid4())])
    assert deleted == 0
    assert task_repo.find_by_id(sample_task.id) is not None

