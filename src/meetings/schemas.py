from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


class MeetingCreate(BaseModel):
    title: str
    description: str | None
    starts_at: datetime
    ends_at: datetime | None


class MeetingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class MeetingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    team_id: int
    title: str
    description: str
    starts_at: datetime
    ends_at: datetime
    status: str


class DateQuery(BaseModel):
    date: date
