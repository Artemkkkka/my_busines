
from pydantic import BaseModel, ConfigDict, Field

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
    name: str | None = None
    members: list[TeamMemberIn] | None = Field(
        None,
        description="Кого добавить/чьи роли обновить"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Platform",
                "members": [
                    {"user_id": 3, "role": "employee"},
                    {"user_id": 4, "role": "admin"}
                ]
            }
        }
    )


class TeamCreate(TeamUpdate):
    name: str
    members: list[TeamMemberIn] = Field(default_factory=list)


class TeamRead(TeamUpdate):
    name: str
    members: list[TeamMemberRead]

    model_config = ConfigDict(from_attributes=True)


class TeamMembersDelete(BaseModel):
    user_ids: list[int] = Field(..., min_items=1)
    model_config = ConfigDict(
        json_schema_extra={"example": {"user_ids": [2, 3, 4]}}
    )
