from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class EvaluationCreate(BaseModel):
    rating: int = Field(ge=1, le=5)


class EvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: int
    value: int
    rated_at: datetime
