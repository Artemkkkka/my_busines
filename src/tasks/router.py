from fastapi import APIRouter, Depends, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .permissions import forbid_employee
from src.core.dependencies import CurrentUser, SessionDep
from src.tasks.schemas import TaskCreate, TaskRead,TaskUpdate
from src.tasks.crud import (
    create_task as crud_create_task,
    get_task as crud_get_task,
    get_all_tasks as crud_get_all_tasks,
    update_task as crud_update_task,
    delete_task as crud_delete_task,
)
from src.users.models import User


http_bearer = HTTPBearer(auto_error=True)


tasks_router = APIRouter(
    prefix="/teams/{team_id}/tasks",
    tags=["tasks"]
)


@tasks_router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    team_id: int,
    payload: TaskCreate,
    session: SessionDep,
    user: User = Depends(forbid_employee),
):
    task = await crud_create_task(
        session,
        team_id=team_id,
        author_id=user.id,
        name=payload.name,
        description=payload.description,
        deadline_at=payload.deadline_at,
        assignee_id=payload.assignee_id,
    )

    return task


@tasks_router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    team_id: int,
    task_id: int,
    session: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
):
    task = await crud_get_task(session, team_id=team_id, task_id=task_id)

    return task


@tasks_router.get("", response_model=list[TaskRead])
async def list_tasks(
    team_id: int,
    session: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
):
    return await crud_get_all_tasks(session, team_id=team_id)


@tasks_router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    team_id: int,
    task_id: int,
    payload: TaskUpdate,
    session: SessionDep,
    user: User = Depends(forbid_employee),
):
    data = payload.model_dump(exclude_unset=True)
    task = await crud_update_task(
        session,
        team_id=team_id,
        task_id=task_id,
        data=data,
        user=user,
    )
    return task


@tasks_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    team_id: int,
    task_id: int,
    session: SessionDep,
    user: User = Depends(forbid_employee),
):
    await crud_delete_task(session, team_id=team_id, task_id=task_id, user=user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
