from typing import Optional, Any, Mapping
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Status, Task
from src.users.models import User
from src.teams.models import Team


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


async def create_task(
    session: AsyncSession,
    team_id: int,
    author_id: int,
    name: str,
    description: Optional[str] = None,
    deadline_at: Optional[datetime] = None,
    assignee_id: Optional[int] = None,
) -> Task:
    """Создать задачу внутри конкретной команды."""

    team = await _get_team_or_404(session, team_id)
    author = await _get_user_or_404(session, author_id)

    # Автор обязан состоять в этой команде
    # if author.team_id != team.id:
    #     raise ForbiddenError("Author is not a member of this team")

    assignee: Optional[User] = None
    if assignee_id is not None:
        assignee = await _get_user_or_404(session, assignee_id)
    #     if assignee.team_id != team.id:
    #         raise ValidationError("Assignee must belong to the same team")

    task = Task(
        team_id=team.id,
        author_id=author.id,
        assignee_id=assignee.id if assignee else None,
        name=name,
        description=description,
        deadline_at=deadline_at,
        status=Status.open,
    )

    session.add(task)
    await session.flush()
    await session.commit()
    return task


async def get_task(session: AsyncSession, *, team_id: int, task_id: int) -> Task | None:
    stmt = select(Task).where(Task.id == task_id, Task.team_id == team_id)
    return await session.scalar(stmt)


async def get_all_tasks(session: AsyncSession, team_id: int) -> list[Task]:
    stmt = select(Task).where(Task.team_id == team_id)
    return list((await session.scalars(stmt)).all())


async def update_task(
    session: AsyncSession,
    *,
    team_id: int,
    task_id: int,
    data: Mapping[str, Any],
    user: User,
) -> Task:
    task = await session.scalar(
        select(Task).where(Task.id == task_id, Task.team_id == team_id)
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can update this task")

    allowed = {"name", "description", "deadline_at", "assignee_id", "status"}
    for key, value in data.items():
        if key in allowed:
            setattr(task, key, value)

    await session.flush()
    await session.commit()
    await session.refresh(task)
    return task


async def delete_task(
    session: AsyncSession,
    *,
    team_id: int,
    task_id: int,
    user: User,
) -> None:
    task = await session.scalar(
        select(Task).where(Task.id == task_id, Task.team_id == team_id)
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can update this task")

    await session.delete(task)
    await session.commit()
