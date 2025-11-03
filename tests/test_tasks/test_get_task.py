from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.tasks.crud import TaskCRUD
from tests.helpers import _make_user, _make_team


crud = TaskCRUD()


@pytest.mark.anyio
async def test_get_all_tasks_filters_by_team(session: AsyncSession):
    owner = await _make_user(session, "owner2@example.com")
    t1 = await _make_team(session, "Team One", owner_id=owner.id)
    t2 = await _make_team(session, "Team Two", owner_id=owner.id)

    a1 = await _make_user(session, "a1@example.com", team_id=t1.id)
    a2 = await _make_user(session, "a2@example.com", team_id=t1.id)
    b1 = await _make_user(session, "b1@example.com", team_id=t2.id)

    await crud.create_task(session=session, team_id=t1.id, author_id=a1.id,
                      name="T1-1", description="", deadline_at=datetime(2025, 1, 2, 9, 0, 0))
    await crud.create_task(session=session, team_id=t1.id, author_id=a2.id,
                      name="T1-2", description="", deadline_at=datetime(2025, 1, 3, 9, 0, 0))
    await crud.create_task(session=session, team_id=t2.id, author_id=b1.id,
                      name="T2-1", description="", deadline_at=datetime(2025, 1, 4, 9, 0, 0))

    tasks_team1 = await crud.get_all_tasks(session=session, team_id=t1.id)

    assert len(tasks_team1) == 2
    assert all(t.team_id == t1.id for t in tasks_team1)
