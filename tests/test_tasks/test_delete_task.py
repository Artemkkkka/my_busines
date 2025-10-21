from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.tasks.crud import create_task, delete_task, get_task
from tests.helpers import _make_user, _make_team


@pytest.mark.anyio
async def test_delete_task_by_author_removes_row(session: AsyncSession, engine):
    owner = await _make_user(session, "owner4@example.com")
    team = await _make_team(session, "Team Delete", owner_id=owner.id)
    author = await _make_user(session, "author4@example.com", team_id=team.id)

    task = await create_task(
        session=session,
        team_id=team.id,
        author_id=author.id,
        name="To be deleted",
        description="",
        deadline_at=datetime(2025, 4, 1, 12, 0, 0),
    )

    await delete_task(session, team_id=team.id, task_id=task.id, user=author)

    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with Session() as s2:
        gone = await get_task(s2, team_id=team.id, task_id=task.id)
        assert gone is None