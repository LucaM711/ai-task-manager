import uuid
from typing import List, Optional
from models import User, UserRoles
from repositories.user_repository import UserRepository
from repositories.task_repository import TaskRepository

class UserService:
    def __init__(self, user_repo: UserRepository = None, task_repo: TaskRepository = None):
        self.user_repo = user_repo or UserRepository()
        self.task_repo = task_repo or TaskRepository()

    def get_all_users(self) -> List[User]:
        return self.user_repo.find_all()

    def create_user(self, email: str, name: str, role: UserRoles = UserRoles.USER) -> User:
        new_user = User(
            id = str(uuid.uuid4()),
            email = email,
            name = name,
            role = role
        )
        self.user_repo.insert(new_user)
        return new_user
    
    def get_user(self, user_id: str) -> User:
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        return user
    
    def get_user_by_email(self, email: str) -> User:
        user = self.user_repo.find_by_email(email)
        if not user:
            raise ValueError(f"User with email {email} not found")
        return user

    def delete_user(self, user_id: str) -> bool:
        self.get_user(user_id)
        self.task_repo.unassign_by_user(user_id)
        return self.user_repo.delete(user_id)
    
    def update_user(self, user_id: str, name: str) -> bool:
        user = self.get_user(user_id)
        user.name = name
        return self.user_repo.update(user)
