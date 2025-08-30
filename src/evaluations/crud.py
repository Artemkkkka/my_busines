from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, func, join
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Evaluation
from src.tasks.models import Status, Task


async def rate_task(
    session: AsyncSession,
    team_id: int,
    task_id: int,
    actor_id: int,
    rating: int,
) -> Evaluation:
    task = await session.scalar(select(Task).where(Task.id == task_id, Task.team_id == team_id))
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != Status.done:
        raise HTTPException(status_code=409, detail="Task must be done to be rated")

    now_utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    rating_row = Evaluation(task_id=task.id, value=rating, rated_at=now_utc)
    session.add(rating_row)

    await session.flush()
    await session.commit()
    await session.refresh(rating_row)
    return rating_row


async def get_avg_rating_for_period(
    session: AsyncSession,
    team_id: int,
    date_from: datetime,
    date_to: datetime,
) -> tuple[float | None, int]:
    stmt = (
        select(func.avg(Evaluation.value), func.count(Evaluation.id))
        .select_from(join(Evaluation, Task, Evaluation.task_id == Task.id))
        .where(
            Task.team_id == team_id,
            Task.status == Status.done,
            Evaluation.rated_at >= date_from,
            Evaluation.rated_at <= date_to,
        )
    )
    avg_val, cnt = (await session.execute(stmt)).one_or_none() or (None, 0)
    return (float(avg_val) if avg_val is not None else None, int(cnt or 0))


async def list_user_ratings(
    session: AsyncSession,
    team_id: int,
    assignee_id: int,
):
    stmt = (
        select(Task, Evaluation)
        .join(Task, Task.id == Evaluation.task_id)
        .where(
            Task.team_id == team_id,
            Task.assignee_id == assignee_id,
            Task.status == Status.done,
        )
        .order_by(Evaluation.rated_at.desc().nullslast(), Task.id.desc())
    )
    rows = (await session.execute(stmt)).all()
    tasks = [r[0] for r in rows]
    ratings = [r[1] for r in rows]

    count = len(ratings)
    avg = (sum(r.value for r in ratings) / count) if count else None
    return tasks, ratings, avg, count
