from datetime import datetime

from fastapi import APIRouter, Depends, status

from src.core.dependencies import CurrentUser, SessionDep
from src.users.models import User
from .crud import rate_task, get_avg_rating_for_period, list_user_ratings
from .permissions import require_team_admin_or_superuser
from .schemas import EvaluationCreate, EvaluationRead

evaluation_router = APIRouter(
    prefix="/teams/{team_id}/tasks",
    tags=["evaluation"]
)


@evaluation_router.post(
        "/{task_id}/rate",
        response_model=EvaluationRead,
        status_code=status.HTTP_200_OK
)
async def rate_task_endpoint(
    team_id: int,
    task_id: int,
    payload: EvaluationCreate,
    session: SessionDep,
    user: User = Depends(require_team_admin_or_superuser),
):
    row = await rate_task(
        session,
        team_id=team_id,
        task_id=task_id,
        rating=payload.rating,
    )
    return EvaluationRead(task_id=row.task_id, value=row.value, rated_at=row.rated_at)


@evaluation_router.get("/ratings/avg")
async def ratings_avg_endpoint(
    team_id: int,
    date_from: datetime,
    date_to: datetime,
    session: SessionDep,
    user: CurrentUser,
):
    avg, count = await get_avg_rating_for_period(
        session, team_id=team_id, date_from=date_from, date_to=date_to
    )
    return {
        "date_from": date_from,
        "date_to": date_to,
        "avg_rating": avg,
    }


@evaluation_router.get("/ratings/user")
async def my_ratings_endpoint(
    team_id: int,
    session: SessionDep,
    actor: CurrentUser,
):
    tasks, ratings, avg, count = await list_user_ratings(session, team_id=team_id, assignee_id=actor.id)
    items = [
        {"task_id": t.id, "name": t.name, "rating": r.value, "rated_at": r.rated_at}
        for t, r in zip(tasks, ratings)
    ]
    return {"avg_rating": (round(avg, 2) if avg is not None else None), "count": count, "items": items}
