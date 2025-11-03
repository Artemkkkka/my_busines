from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.meetings.crud import MeetingCRUD
from tests.helpers import _make_user, _make_team, _make_meeting



@pytest.mark.anyio
async def test_get_meetings_by_date_filters_by_team_and_time(session: AsyncSession):
    team = await _make_team(session, "Alpha")
    user = await _make_user(session, "u@a.com", team_id=team.id)
    other_team = await _make_team(session, "Beta")

    now = datetime.now()
    date_cut = now - timedelta(hours=3)

    await _make_meeting(session, team_id=team.id, starts_at=now - timedelta(hours=4), ends_at=now - timedelta(hours=3, minutes=30))
    in_range = await _make_meeting(session, team_id=team.id, starts_at=now - timedelta(hours=2), ends_at=now - timedelta(hours=1, minutes=30))
    await _make_meeting(session, team_id=team.id, starts_at=now + timedelta(hours=1), ends_at=now + timedelta(hours=2))
    await _make_meeting(session, team_id=other_team.id, starts_at=now - timedelta(hours=2), ends_at=now - timedelta(hours=1, minutes=30))

    result = await MeetingCRUD.get_meetings_by_date(user=user, date=date_cut, session=session)

    assert [m.id for m in result] == [in_range.id]


@pytest.mark.anyio
async def test_get_user_meetings_respects_status_time_and_limit(session: AsyncSession):
    team = await _make_team(session, "Gamma")
    req = await _make_user(session, "req@g.com", team_id=team.id)
    other_team = await _make_team(session, "Delta")

    now = datetime.now()

    await _make_meeting(
        session, team_id=team.id,
        starts_at=now - timedelta(hours=4), ends_at=now - timedelta(hours=3, minutes=30)
    )
    m_ok = await _make_meeting(
        session, team_id=team.id,
        starts_at=now - timedelta(hours=2), ends_at=now - timedelta(hours=1, minutes=30)
    )
    await _make_meeting(
        session, team_id=team.id, status="canceled",
        starts_at=now - timedelta(hours=1), ends_at=now - timedelta(minutes=30)
    )
    await _make_meeting(
        session, team_id=other_team.id,
        starts_at=now - timedelta(hours=2), ends_at=now - timedelta(hours=1, minutes=30)
    )

    result = await MeetingCRUD.get_user_meetings(
        session=session,
        requester=req,
        starts_after=now - timedelta(hours=3),
        ends_before=now,
        limit=1,
    )

    assert len(result) == 1 and result[0].id == m_ok.id


@pytest.mark.anyio
async def test_get_team_meetings_sorted_desc(session: AsyncSession):
    team = await _make_team(session, "Omega")
    user = await _make_user(session, "me@o.com", team_id=team.id)
    other_team = await _make_team(session, "Zeta")

    t1 = datetime.now() - timedelta(hours=3)
    t2 = datetime.now() - timedelta(hours=1)
    t3 = datetime.now() + timedelta(hours=1)

    m1 = await _make_meeting(session, team_id=team.id, starts_at=t1, ends_at=t1 + timedelta(minutes=30))
    m2 = await _make_meeting(session, team_id=team.id, starts_at=t2, ends_at=t2 + timedelta(minutes=30))
    m3 = await _make_meeting(session, team_id=team.id, starts_at=t3, ends_at=t3 + timedelta(minutes=30))
    await _make_meeting(session, team_id=other_team.id, starts_at=t2, ends_at=t2 + timedelta(minutes=30))

    result = await MeetingCRUD.get_team_meetings(session=session, user=user)

    assert [m.id for m in result] == [m3.id, m2.id, m1.id]


@pytest.mark.anyio
async def test_get_meeting_returns_object_or_none(session: AsyncSession):
    team = await _make_team(session, "Sigma")
    await _make_user(session, "s@s.com", team_id=team.id)
    m = await _make_meeting(
        session, team_id=team.id,
        starts_at=datetime.now() - timedelta(hours=1),
        ends_at=datetime.now() - timedelta(minutes=10),
    )

    found = await MeetingCRUD.get_meeting(m.id, session)
    assert found is not None and found.id == m.id

    missing = await MeetingCRUD.get_meeting(m.id + 999, session)
    assert missing is None
