from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.tasks.models import Task
from src.teams.models import Team
from src.users.models import User


async def _get_user_or_404(session: AsyncSession, user_id: int) -> User:
    user = await session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return user


async def _get_team_or_404(session: AsyncSession, team_id: int) -> Team:
    team = await session.scalar(select(Team).where(Team.id == team_id))
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return team

async def _get_task_or_404(session: AsyncSession, team_id: int, task_id: int) -> Task:
    task = await session.scalar(
        select(Task).where(Task.id == task_id, Task.team_id == team_id)
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task
