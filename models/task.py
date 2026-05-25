from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, timezone

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# Etichette italiane per la UI (i .value restano inglesi per coerenza DB)
STATUS_LABELS = {
    TaskStatus.TODO: "Da fare",
    TaskStatus.IN_PROGRESS: "In corso",
    TaskStatus.COMPLETED: "Completati",
}

PRIORITY_LABELS = {
    TaskPriority.LOW: "Bassa",
    TaskPriority.MEDIUM: "Media",
    TaskPriority.HIGH: "Alta",
}

class SubTask(BaseModel):
    id: str
    title: str
    completed: bool = False
    created_at: datetime = Field(default_factory = lambda: datetime.now(timezone.utc))

class TaskHistory(BaseModel):
    field: str
    old_value: str
    new_value: str
    changed_by: str
    changed_at: datetime = Field(default_factory = lambda: datetime.now(timezone.utc))

class Attachment(BaseModel):
    file_id: str
    filename: str
    content_type: str
    uploaded_at: datetime = Field(default_factory = lambda: datetime.now(timezone.utc))

class Task(BaseModel):
    id: str
    project_id: str
    title: str
    description: Optional[str] = None
    notes: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to: Optional[str] = None          # user_id
    due_date: Optional[datetime] = None
    subtasks: List[SubTask] = Field(default_factory = list)
    attachments: List[Attachment] = Field(default_factory = list)
    history: List[TaskHistory] = Field(default_factory = list)     # Per tracciamento storico
    tags: List[str] = Field(default_factory = list)         # Per categorizzazione
    year: int                           # Per ricorrenza annuale
    recurring: bool = False
    created_at: datetime = Field(default_factory = lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory = lambda: datetime.now(timezone.utc))

    @field_validator("due_date", "created_at", "updated_at", mode="before")
    @classmethod
    def ensure_utc(cls, v):
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

