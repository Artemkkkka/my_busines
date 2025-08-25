from typing import Optional

from pydantic import BaseModel, ConfigDict


class TeamUpdate(BaseModel):
    name: str


class TeamCreate(TeamUpdate):
    owner_id: int | None


class TeamRead(TeamCreate):
    model_config = ConfigDict(from_attributes=True)



