from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone

class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    members: List[str] = Field(default_factory = list)  # List of user_ids
    created_at: datetime = Field(default_factory = lambda: datetime.now(timezone.utc))
