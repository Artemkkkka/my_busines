from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Team
from .schemas import TeamCreate


async def create_team(team_create: TeamCreate, session: AsyncSession):
    team = Team(**team_create.model_dump())
    session.add(team)
    await session.commit()
    await session.refresh(team)

    return team


async def get_team(team_id: int, session: AsyncSession):
    stmt = select(Team).where(Team.id == team_id)
    result = await session.execute(stmt)
    team = result.scalar_one()

    return team


async def get_all_team(session: AsyncSession):
    stmt = select(Team)
    result = await session.execute(stmt)

    users = result.scalars(result)

    return users

async def update_team(session: AsyncSession, team_id: int, new_name: str):
    team = await get_team(team_id, session)
    team.name = new_name

    session.add(team)
    await session.commit()

    return team

async def delete_team(session: AsyncSession, team_id: int):
    stmt = delete(Team).where(Team.id == team_id)
    await session.execute(stmt)
    await session.commit()