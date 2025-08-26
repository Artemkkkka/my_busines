
from pydantic import BaseModel, ConfigDict

from src.users.models import TeamRole
from src.users.schemas import UserRead


class UserShort(BaseModel):
    id: int
    email: str | None = None

class TeamMemberRead(BaseModel):
    user: UserShort
    role: TeamRole

class TeamMemberIn(BaseModel):
    user_id: int
    role: TeamRole = TeamRole.employee

class TeamUpdate(BaseModel):
    name: str

class TeamCreate(TeamUpdate):
    members: list[TeamMemberIn] = []

class TeamRead(TeamUpdate):
    members: list[TeamMemberRead]
    model_config = ConfigDict(from_attributes=True)



