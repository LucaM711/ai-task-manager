from enum import Enum
from pydantic import BaseModel
from typing import Optional

class UserRoles(str, Enum):
    USER = "user"
    ADMIN = "admin"

class User(BaseModel):
    id: str
    name: str
    email: str
    role: UserRoles = UserRoles.USER