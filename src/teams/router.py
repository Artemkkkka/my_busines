from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .crud import (
    create_team as crud_create_team,
    get_team as crud_get_team,
    get_all_team as crud_get_all_teams,
    update_team as crud_update_team,
    delete_team as crud_delete_team,
)
from .schemas import TeamCreate, TeamRead, TeamUpdate
from src.database import db_helper


teams_router = APIRouter(
    prefix="/team",
    tags=["team"],
)

@teams_router.post("/", response_model=TeamRead)
async def create_team(
    payload: TeamCreate,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    team = await crud_create_team(payload, session)

    return team


@teams_router.get("/{team_id}", response_model=TeamRead)
async def get_team(
    team_id: int,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    team = await crud_get_team(team_id, session)

    return team


@teams_router.get("/")
async def get_all_teams(
    session: AsyncSession = Depends(db_helper.session_getter)
) -> list[TeamRead]:
    users = await crud_get_all_teams(session=session)
    return users


@teams_router.patch("/{team_id}", response_model=TeamRead)
async def update_team(
    team_id: int,
    payload: TeamUpdate,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    team = await crud_update_team(session, team_id, payload.name)
    return team


@teams_router.delete("/{team_id}")
async def delete_team(
    team_id: int, 
    session: AsyncSession = Depends(db_helper.session_getter),
):
    await crud_delete_team(session, team_id)

    return {"message": "team was deleted"}