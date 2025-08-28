from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .crud import (
    create_team as crud_create_team,
    get_team as crud_get_team,
    get_all_team as crud_get_all_teams,
    update_team as crud_update_team,
    delete_team as crud_delete_team,
    list_team_users as crud_list_team_users,
    remove_team_users as crud_remove_team_users,
)
from .schemas import TeamCreate, TeamRead, TeamUpdate, TeamMemberRead, TeamMembersDelete
from.permissions import require_team_admin_or_superuser
from src.core.dependencies import SessionDep
from src.users.models import User


http_bearer = HTTPBearer(auto_error=True)


teams_router = APIRouter(
    prefix="/team",
    tags=["team"],
)


@teams_router.post("/", response_model=TeamRead)
async def create_team(
    payload: TeamCreate,
    session: SessionDep,
    user: User = Depends(require_team_admin_or_superuser),
):
    team = await crud_create_team(payload, session, user)

    return team


@teams_router.get("/{team_id}", response_model=TeamRead)
async def get_team(
    team_id: int,
    session: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
):
    team = await crud_get_team(team_id, session)

    return team


@teams_router.get("/")
async def get_all_teams(
    session: SessionDep,
    redentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> list[TeamRead]:
    users = await crud_get_all_teams(session=session)
    return users


@teams_router.patch("/{team_id}", response_model=TeamRead)
async def update_team(
    team_id: int,
    payload: TeamUpdate,
    session: SessionDep,
    user: User = Depends(require_team_admin_or_superuser),
):
    team = await crud_update_team(session, team_id, payload.name, payload.members)
    return team


@teams_router.delete("/{team_id}")
async def delete_team(
    team_id: int,
    session: SessionDep,
    user: User = Depends(require_team_admin_or_superuser),
):
    await crud_delete_team(session, team_id)

    return {"message": "team was deleted"}


@teams_router.get(
    "/{team_id}/users",
    response_model=list[TeamMemberRead],
)
async def list_team_users(
    team_id: int,
    session: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),

):
    users = await crud_list_team_users(team_id, session)
    return users


@teams_router.delete(
    "/teams/{team_id}/users",
    response_model=list[TeamMemberRead],
)
async def remove_team_users(
    team_id: int,
    payload: TeamMembersDelete,
    session: SessionDep,
    user: User = Depends(require_team_admin_or_superuser),
):
    users = await crud_remove_team_users(team_id, payload, session)
    return users
