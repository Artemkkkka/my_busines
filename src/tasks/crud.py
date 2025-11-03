from typing import Optional, Any, Mapping
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .helpers import (
    _get_team_or_404,
    _get_user_or_404,
    _get_task_or_404,
)
from .models import Status, Task, TaskComment
from src.teams.models import Team
from src.users.models import User



class TaskCRUD:
    async def create_task(
        self,
        *,
        session: AsyncSession,
        team_id: int,
        author_id: int,
        name: str,
        description: Optional[str] = None,
        deadline_at: Optional[datetime] = None,
        assignee_id: Optional[int] = None,
    ) -> Task:
        team = await _get_team_or_404(session=session, team_id=team_id)
        author = await _get_user_or_404(session=session, user_id=author_id)

        assignee: Optional[User] = None
        if assignee_id is not None:
            assignee = await _get_user_or_404(session=session, user_id=assignee_id)

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

    async def get_task(self, *, session: AsyncSession, team_id: int, task_id: int) -> Task | None:
        stmt = select(Task).where(Task.id == task_id, Task.team_id == team_id)
        return await session.scalar(stmt)

    async def get_all_tasks(self, *, session: AsyncSession, team_id: int) -> list[Task]:
        stmt = select(Task).where(Task.team_id == team_id)
        return list((await session.scalars(stmt)).all())

    async def update_task(
        self,
        *,
        session: AsyncSession,
        team_id: int,
        task_id: int,
        data: Mapping[str, Any],
        user: User,
    ) -> Task:
        task = await _get_task_or_404(session=session, team_id=team_id, task_id=task_id)

        if task.author_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the author can update this task",
            )

        allowed = {"name", "description", "deadline_at", "assignee_id", "status"}
        for key, value in data.items():
            if key in allowed:
                setattr(task, key, value)

        await session.flush()
        await session.commit()
        await session.refresh(task)
        return task

    async def delete_task(
        self,
        *,
        session: AsyncSession,
        team_id: int,
        task_id: int,
        user: User,
    ) -> None:
        task = await _get_task_or_404(session=session, team_id=team_id, task_id=task_id)

        if task.author_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the author can update this task",
            )

        await session.delete(task)
        await session.commit()

    async def create_task_comment(
        self,
        *,
        session: AsyncSession,
        team_id: int,
        task_id: int,
        author_id: int,
        body: str,
    ) -> TaskComment:
        _ = await _get_task_or_404(session=session, team_id=team_id, task_id=task_id)

        comment = TaskComment(task_id=task_id, author_id=author_id, body=body)
        session.add(comment)

        await session.flush()
        await session.commit()
        await session.refresh(comment)
        return comment
