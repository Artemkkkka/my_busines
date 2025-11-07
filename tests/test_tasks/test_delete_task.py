from datetime import datetime

from fastapi import HTTPException
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.tasks.crud import TaskCRUD
from tests.helpers import _make_user, _make_team


crud = TaskCRUD()


@pytest.mark.anyio
async def test_delete_task_by_author_removes_row(session: AsyncSession):
    owner = await _make_user(session, "owner4@example.com")
    team = await _make_team(session, "Team Delete", owner_id=owner.id)
    author = await _make_user(session, "author4@example.com", team_id=team.id)

    task = await crud.create_task(
        session=session,
        team_id=team.id,
        author_id=author.id,
        name="To be deleted",
        description="",
        deadline_at=datetime(2025, 4, 1, 12, 0, 0),
    )

    await crud.delete_task(session=session, team_id=team.id, task_id=task.id, user=author)

    with pytest.raises(HTTPException) as ex:
        await crud.get_task(session=session, team_id=team.id, task_id=task.id)
    assert ex.value.status_code == 404
