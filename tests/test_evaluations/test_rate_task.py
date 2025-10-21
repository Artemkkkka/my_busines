import pytest

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.evaluations.crud import rate_task
from src.evaluations.models import Evaluation
from src.evaluations.permissions import ensure_can_rate_task
from src.tasks.models import Status
from src.users.models import TeamRole
from tests.helpers import _make_user, _make_task, _make_team


@pytest.mark.anyio
async def test_rate_task_success_creates_evaluation_with_utc_minute_trunc(session: AsyncSession):
    owner = await _make_user(session, "owner@example.com", role=TeamRole.admin)
    team = await _make_team(session, "Team A", owner_id=owner.id)
    t = await _make_task(session, team_id=team.id, author_id=owner.id, status=Status.done)

    rating_value = 4
    row = await rate_task(
        session,
        team_id=team.id,
        task_id=t.id,
        rating=rating_value,
    )

    assert row.task_id == t.id
    assert row.value == rating_value

    saved = (await session.scalars(select(Evaluation).where(Evaluation.id == row.id))).one()
    assert saved.value == rating_value
    assert saved.task_id == t.id


@pytest.mark.anyio
async def test_rate_task_404_when_task_not_found(session: AsyncSession):
    owner = await _make_user(session, "admin@example.com", role=TeamRole.admin)
    team_ok = await _make_team(session, "OK", owner_id=owner.id)

    stranger_owner = await _make_user(session, "stranger@example.com")
    stranger_team = await _make_team(session, "Other", owner_id=stranger_owner.id)
    other_task = await _make_task(session, team_id=stranger_team.id, author_id=stranger_owner.id, status=Status.done)

    with pytest.raises(HTTPException) as exc:
        await rate_task(session, team_id=team_ok.id, task_id=other_task.id, rating=5)

    assert exc.value.status_code == 404
    assert "Task not found" in exc.value.detail


@pytest.mark.anyio
async def test_rate_task_409_when_task_not_done(session: AsyncSession):
    owner = await _make_user(session, "owner2@example.com", role=TeamRole.admin)
    team = await _make_team(session, "Team B", owner_id=owner.id)

    not_done_status = next(s for s in Status if s != Status.done)
    t = await _make_task(session, team_id=team.id, author_id=owner.id, status=not_done_status)

    with pytest.raises(HTTPException) as exc:
        await rate_task(session, team_id=team.id, task_id=t.id, rating=3)

    assert exc.value.status_code == 409
    assert "Task must be done" in exc.value.detail


@pytest.mark.anyio
async def test_ensure_can_rate_task_permissions(session: AsyncSession):
    su = await _make_user(session, "su@example.com")
    su.is_superuser = True
    await session.flush()

    admin = await _make_user(session, "admin@example.com", role=TeamRole.admin)
    emp = await _make_user(session, "emp@example.com", role=TeamRole.employee)

    await ensure_can_rate_task(su)
    await ensure_can_rate_task(admin)

    with pytest.raises(HTTPException) as exc:
        await ensure_can_rate_task(emp)
    assert exc.value.status_code == 403
