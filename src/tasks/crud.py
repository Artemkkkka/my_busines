from typing import Optional, Any, Mapping
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Status, Task, TaskComment
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


async def create_task_comment(
    session: AsyncSession,
    team_id: int,
    task_id: int,
    author_id: int,
    body: str,
) -> TaskComment:
    task = await session.scalar(
        select(Task).where(Task.id == task_id, Task.team_id == team_id)
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    comment = TaskComment(task_id=task.id, author_id=author_id, body=body)
    session.add(comment)

    await session.flush()
    await session.commit()
    await session.refresh(comment)
    return comment


async def rate_task(
    session: AsyncSession,
    team_id: int,
    task_id: int,
    actor_id: int,
    rating: int,
) -> Task:
    task = await session.scalar(
        select(Task).where(Task.id == task_id, Task.team_id == team_id)
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if task.status != Status.done:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task must be done to be rated")

    if not (1 <= rating <= 5):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rating must be between 1 and 5")

    task.rating = rating
    task.rated_at = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    await session.flush()
    await session.commit()
    await session.refresh(task)
    return task


async def get_avg_rating_for_period(
    session: AsyncSession,
    team_id: int,
    date_from: datetime,
    date_to: datetime,
    user: User,
) -> tuple[float | None, int]:
    if date_from > date_to:
        raise HTTPException(status_code=422, detail="'date_from' must be <= 'date_to'")

    res = await session.execute(
        select(func.avg(Task.rating), func.count())
        .where(
            Task.assignee_id == user.id,
            Task.team_id == team_id,
            Task.status == Status.done,
            Task.rating.isnot(None),
            Task.rated_at.isnot(None),
            Task.rated_at >= date_from,
            Task.rated_at <= date_to,
        )
    )
    avg_val, cnt = res.one_or_none() or (None, 0)
    return (float(avg_val) if avg_val is not None else None, int(cnt or 0))


async def list_user_ratings(
    session: AsyncSession,
    team_id: int,
    user: User,
):
    stmt = (
        select(Task)
        .where(
            Task.team_id == team_id,
            Task.assignee_id == user.id,
            Task.status == Status.done,
            Task.rating.isnot(None),
        )
        .order_by(Task.rated_at.desc().nullslast(), Task.id.desc())
    )
    tasks = list((await session.scalars(stmt)).all())

    if tasks:
        count = len(tasks)
        avg = sum(t.rating for t in tasks if t.rating is not None) / count
    else:
        count, avg = 0, None

    return tasks, avg, count
