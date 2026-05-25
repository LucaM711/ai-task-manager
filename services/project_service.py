import uuid
from typing import List, Optional
from models import Project
from repositories.project_repository import ProjectRepository
from repositories.task_repository import TaskRepository


class ProjectService:
    def __init__(self, project_repo: ProjectRepository = None, task_repo: TaskRepository = None):
        self.project_repo = project_repo or ProjectRepository()
        self.task_repo = task_repo or TaskRepository()

    def create_project(self, name: str, description: Optional[str] = None) -> Project:
        new_project = Project(
            id = str(uuid.uuid4()),
            name = name,
            description = description,
        )
        self.project_repo.insert(new_project)
        return new_project

    def get_project(self, project_id: str) -> Project:
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise ValueError(f"Project with id {project_id} not found")
        return project
    
    def get_all_projects(self) -> List[Project]:
        return self.project_repo.find_all()

    def update_project(self, project_id: str, name: Optional[str] = None, description: Optional[str] = None) -> bool:
        project = self.get_project(project_id)
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        return self.project_repo.update(project)

    def delete_project(self, project_id: str) -> bool:
        project = self.get_project(project_id)
        self.task_repo.delete_by_project(project_id)
        self.project_repo.delete(project_id)
        return True
