from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.tasks.crud import create_task, get_task, update_task
from src.tasks.models import Status
from tests.helpers import _make_user, _make_team


@pytest.mark.anyio
async def test_update_task_by_author_changes_fields(session: AsyncSession, engine):
    owner = await _make_user(session, "owner3@example.com")
    team = await _make_team(session, "Team Edit", owner_id=owner.id)
    author = await _make_user(session, "author3@example.com", team_id=team.id)
    assignee = await _make_user(session, "assignee3@example.com", team_id=team.id)

    task = await create_task(
        session=session,
        team_id=team.id,
        author_id=author.id,
        name="Old name",
        description="old desc",
        deadline_at=datetime(2025, 2, 1, 10, 0, 0),
        assignee_id=None,
    )

    new_deadline = datetime(2025, 3, 1, 18, 30, 0)
    updated = await update_task(
        session=session,
        team_id=team.id,
        task_id=task.id,
        user=author,
        data={
            "name": "New name",
            "description": "new desc",
            "deadline_at": new_deadline,
            "assignee_id": assignee.id,
            "status": Status.open,
        },
    )

    assert updated.id == task.id
    assert updated.name == "New name"
    assert updated.description == "new desc"
    assert updated.deadline_at == new_deadline
    assert updated.assignee_id == assignee.id

    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with Session() as s2:
        again = await get_task(s2, team_id=team.id, task_id=task.id)
        assert again is not None
        assert again.name == "New name"
        assert again.description == "new desc"
        assert again.deadline_at == new_deadline
        assert again.assignee_id == assignee.id
