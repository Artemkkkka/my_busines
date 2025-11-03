from fastapi import APIRouter, Depends, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..evaluations.permissions import forbid_employee
from .schemas import (
    TaskCommentCreate,
    TaskCommentRead,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)
from src.core.dependencies import CurrentUser, SessionDep
from src.tasks.crud import TaskCRUD 
from src.users.models import User


http_bearer = HTTPBearer(auto_error=True)
crud = TaskCRUD()


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
    task = await crud.create_task(
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
    task = await crud.get_task(session, team_id=team_id, task_id=task_id)

    return task


@tasks_router.get("", response_model=list[TaskRead])
async def list_tasks(
    team_id: int,
    session: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
):
    return await crud.get_all_tasks(session, team_id=team_id)


@tasks_router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    team_id: int,
    task_id: int,
    payload: TaskUpdate,
    session: SessionDep,
    user: User = Depends(forbid_employee),
):
    data = payload.model_dump(exclude_unset=True)
    task = await crud.update_task(
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
    await crud.delete_task(session, team_id=team_id, task_id=task_id, user=user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@tasks_router.post("/{task_id}", response_model=TaskCommentRead, status_code=status.HTTP_201_CREATED)
async def add_comment(
    team_id: int,
    task_id: int,
    payload: TaskCommentCreate,
    session: SessionDep,
    user: CurrentUser,
):
    comment = await crud.create_task_comment(
        session,
        team_id=team_id,
        task_id=task_id,
        author_id=user.id,
        body=payload.body,
    )
    return comment
