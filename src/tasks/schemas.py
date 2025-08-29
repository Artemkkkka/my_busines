from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from .models import Status


class TaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    deadline_at: Optional[datetime] = None
    assignee_id: Optional[int] = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: Optional[str]
    deadline_at: Optional[datetime]
    status: Status
    author_id: int
    assignee_id: Optional[int]
    created_at: datetime
    updated_at: datetime


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    deadline_at: Optional[datetime] = None
    assignee_id: Optional[int] = None
    status: Optional[Status] = None


class TaskCommentCreate(BaseModel):
    body: str


class TaskCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    author_id: int
    body: str
    created_at: datetime
    updated_at: datetime
