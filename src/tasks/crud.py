from typing import Optional, Any, Mapping
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .helpers import (
    _get_team_or_404,
    _get_user_or_404,
)
from .models import Status, Task, TaskComment
from src.users.models import User



class TaskCRUD:
    @staticmethod
    async def create_task(
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
        conflict = await session.scalar(
            select(Task.id).where(
                Task.team_id == team_id,
                func.lower(Task.name) == func.lower(name),
            )
        )
        if conflict:
            raise HTTPException(status_code=409, detail="Task name already exists in this team")
        session.add(task)
        await session.flush()
        await session.commit()
        return task

    @staticmethod
    async def get_task(session: AsyncSession, team_id: int, task_id: int) -> Task | None:
        stmt = select(Task).where(Task.id == task_id, Task.team_id == team_id)
        task = await session.scalar(stmt)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return task

    @staticmethod
    async def get_all_tasks(session: AsyncSession, team_id: int) -> list[Task]:
        stmt = select(Task).where(Task.team_id == team_id)
        return list((await session.scalars(stmt)).all())

    async def update_task(
        self,
        session: AsyncSession,
        team_id: int,
        task_id: int,
        data: Mapping[str, Any],
        user: User,
    ) -> Task:
        task = await self.get_task(session=session, team_id=team_id, task_id=task_id)
        if task.author_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the author can update this task",
            )
        if "name" in data:
            new_name = data["name"]
            conflict = await session.scalar(
                select(Task.id).where(
                    Task.team_id == team_id,
                    Task.id != task_id,
                    func.lower(Task.name) == func.lower(new_name),
                )
            )
            if conflict:
                raise HTTPException(status_code=409, detail="Task name already exists in this team")
            task.name = new_name
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
        session: AsyncSession,
        team_id: int,
        task_id: int,
        user: User,
    ) -> None:
        task = await self.get_task(session=session, team_id=team_id, task_id=task_id)

        if task.author_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the author can update this task",
            )

        await session.delete(task)
        await session.commit()

    async def create_task_comment(
        self,
        session: AsyncSession,
        team_id: int,
        task_id: int,
        author_id: int,
        body: str,
    ) -> TaskComment:
        _ = await self.get_task(session=session, team_id=team_id, task_id=task_id)

        comment = TaskComment(task_id=task_id, author_id=author_id, body=body)
        session.add(comment)

        await session.flush()
        await session.commit()
        await session.refresh(comment)
        return comment
