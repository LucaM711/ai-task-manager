import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from models import Task, TaskStatus, TaskPriority, TaskHistory
from repositories.task_repository import TaskRepository
from repositories.project_repository import ProjectRepository


class TaskService:
    def __init__(self, task_repo: TaskRepository = None, project_repo: ProjectRepository = None):
        self.task_repo = task_repo or TaskRepository()
        self.project_repo = project_repo or ProjectRepository()

    def create_task(self, title: str, project_id: str, description: Optional[str] = None, priority: TaskPriority = TaskPriority.MEDIUM, assigned_to: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        if self.project_repo.find_by_id(project_id) is None:
            raise ValueError(f"Project with id {project_id} not found")
        new_task = Task(
            id = str(uuid.uuid4()),
            title = title,
            description = description,
            project_id = project_id,
            assigned_to = assigned_to,
            priority = priority,
            year = datetime.now(timezone.utc).year,
            due_date = due_date
        )
        self.task_repo.insert(new_task)
        return new_task

    def get_task(self, task_id: str) -> Task:
        task = self.task_repo.find_by_id(task_id)
        if not task:
            raise ValueError(f"Task with id {task_id} not found")
        return task
    
    def get_tasks_by_project(self, project_id: str) -> dict:
        tasks = self.task_repo.find_by_project(project_id)
        result = {}
        for task in tasks:
            result.setdefault(task.status, []).append(task)
        return result

    def get_tasks_by_user(self, user_id: str) -> List[Task]:
        return self.task_repo.find_by_user(user_id)
    
    def get_urgent_tasks(self, priority: TaskPriority = TaskPriority.HIGH) -> List[Task]:
        return self.task_repo.find_urgent_tasks(priority)

    def update_task(self, task: Task, field: str, old_value: str, new_value: str, changed_by: str) -> bool:
        history_entry = TaskHistory(
            field=field,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by
        )
        task.history.append(history_entry)
        return self.task_repo.update(task)

    def update_task_status(self, task_id: str, new_status: TaskStatus, changed_by: str) -> bool:
        task = self.get_task(task_id)
        old_status = task.status
        task.status = new_status
        return self.update_task(task, field = "status", old_value = old_status.value, new_value = new_status.value, changed_by = changed_by)
    
    def update_task_priority(self, task_id: str, new_priority: TaskPriority, changed_by: str) -> bool:
        task = self.get_task(task_id)
        old_priority = task.priority
        task.priority = new_priority
        return self.update_task(task, field = "priority", old_value = old_priority.value, new_value = new_priority.value, changed_by = changed_by)

    def update_task_description(self, task_id: str, new_description: str, changed_by: str) -> bool:
        task = self.get_task(task_id)
        old_description = task.description or ""
        task.description = new_description
        return self.update_task(task, field="description", old_value=old_description, new_value=new_description, changed_by=changed_by)

    def delete_task(self, task_id: str) -> bool:
        # Cascade: cancella gli allegati GridFS prima di rimuovere il task
        from services.attachment_service import AttachmentService
        task = self.get_task(task_id)
        AttachmentService(task_repo=self.task_repo).delete_all_for_task(task_id)
        return self.task_repo.delete(task_id)

    def delete_tasks(self, task_ids: List[str]) -> int:
        """Elimina più task in un'unica operazione. Restituisce il numero di task eliminati."""
        # Cascade: per ogni id valido cancella prima gli allegati GridFS
        from services.attachment_service import AttachmentService
        att_service = AttachmentService(task_repo=self.task_repo)
        for tid in task_ids:
            try:
                att_service.delete_all_for_task(tid)
            except ValueError:
                # task_id inesistente: tollerato (delete_many ignora gli id non in DB)
                pass
        return self.task_repo.delete_many_by_ids(task_ids)
    
    def get_tasks_by_deadline(self, days: int) -> List[Task]:
        """Recupera i task in scadenza entro N giorni (esclusi i completati)."""
        return self.task_repo.find_by_deadline(days)

    def get_tasks_by_priority(self, priority: TaskPriority) -> List[Task]:
        """Recupera tutti i task con la priorità specificata."""
        return self.task_repo.find_by_priority(priority)

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Recupera tutti i task con lo stato specificato."""
        return self.task_repo.find_by_status(status)

    def get_tasks_by_title(self, title: str) -> List[Task]:
        """Recupera i task il cui titolo contiene la stringa (case-insensitive)."""
        return self.task_repo.find_by_title(title)
