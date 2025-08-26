from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class UserCreate(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    role_in_team: str


class UserUpdate(UserCreate):
    pass