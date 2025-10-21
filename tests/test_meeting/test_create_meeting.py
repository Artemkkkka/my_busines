from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.meetings.crud import create_meeting
from src.meetings.checks.check_time import ensure_no_overlap
from src.meetings.models import Meeting
from src.meetings.schemas import MeetingCreate, MeetingOut
from src.users.models import TeamRole
from tests.helpers import _make_user, _make_team


@pytest.mark.anyio
async def test_create_meeting_success(session: AsyncSession):
    team = await _make_team(session, "R&D")
    manager = await _make_user(
        session,
        "boss@example.com",
        role=TeamRole.manager,
        team_id=team.id,
    )
    starts = datetime(2025, 1, 1, 10, 0, 0)
    ends = starts + timedelta(hours=1)

    payload = MeetingCreate(
        title="Weekly sync",
        description="Первый синк года",
        starts_at=starts,
        ends_at=ends,
    )

    await ensure_no_overlap(
        session,
        team_id=manager.team_id,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
    )
    created = await create_meeting(user=manager, payload=payload, session=session)

    assert isinstance(created, Meeting)
    assert created.id is not None
    assert created.team_id == team.id
    assert created.title == payload.title
    assert created.description == payload.description
    assert created.starts_at == starts
    assert created.ends_at == ends

    if hasattr(created.status, "value"):
        assert created.status.value == "scheduled"
    else:
        assert created.status == "scheduled"

    out = MeetingOut.model_validate(created)
    assert out.team_id == team.id
    assert out.title == payload.title
    assert out.starts_at == starts and out.ends_at == ends
    assert out.status == "scheduled"

    saved = await session.get(Meeting, created.id)
    assert saved is not None


@pytest.mark.anyio
async def test_create_meeting_conflict_overlap_raises_409(session: AsyncSession):
    team = await _make_team(session, "R&D")
    manager = await _make_user(session, "boss@example.com", role=TeamRole.manager, team_id=team.id)

    base_start = datetime(2025, 1, 2, 10, 0, 0)
    base_end = base_start + timedelta(hours=1)

    first = MeetingCreate(
        title="Base",
        description="Базовая встреча",
        starts_at=base_start,
        ends_at=base_end,
    )
    await ensure_no_overlap(session, team_id=team.id, starts_at=first.starts_at, ends_at=first.ends_at)
    await create_meeting(user=manager, payload=first, session=session)

    conflict = MeetingCreate(
        title="Overlap",
        description="Пересекается",
        starts_at=base_start + timedelta(minutes=30),
        ends_at=base_end + timedelta(minutes=30),
    )
    with pytest.raises(HTTPException) as exc:
        await ensure_no_overlap(session, team_id=team.id, starts_at=conflict.starts_at, ends_at=conflict.ends_at)
    assert exc.value.status_code == 409
    assert "пересекающиеся" in str(exc.value.detail).lower()


@pytest.mark.anyio
async def test_back_to_back_meetings_are_allowed(session: AsyncSession):
    team = await _make_team(session, "Ops")
    manager = await _make_user(session, "lead@example.com", role=TeamRole.manager, team_id=team.id)

    start1 = datetime(2025, 1, 3, 9, 0, 0)
    end1 = start1 + timedelta(hours=1)
    p1 = MeetingCreate(title="A", description=None, starts_at=start1, ends_at=end1)
    await ensure_no_overlap(session, team_id=team.id, starts_at=p1.starts_at, ends_at=p1.ends_at)
    await create_meeting(user=manager, payload=p1, session=session)

    start2 = end1
    end2 = start2 + timedelta(minutes=45)
    p2 = MeetingCreate(title="B", description=None, starts_at=start2, ends_at=end2)

    await ensure_no_overlap(session, team_id=team.id, starts_at=p2.starts_at, ends_at=p2.ends_at)
    created2 = await create_meeting(user=manager, payload=p2, session=session)

    rows = (
        await session.execute(select(Meeting).where(Meeting.team_id == team.id))
    ).scalars().all()
    assert any(m.id == created2.id for m in rows)
    assert created2.starts_at == start2 and created2.ends_at == end2
