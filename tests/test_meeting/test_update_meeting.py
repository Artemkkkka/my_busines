from datetime import datetime, timedelta

from fastapi import HTTPException
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.meetings.crud import MeetingCRUD
from src.meetings.schemas import MeetingUpdate
from tests.helpers import _make_user, _make_team, _make_meeting


@pytest.mark.anyio
async def test_update_meeting_updates_fields_and_sets_canceled_if_ends_at_in_payload(session: AsyncSession):
    team = await _make_team(session, "Tau")
    await _make_user(session, "t@t.com", team_id=team.id)
    m = await _make_meeting(
        session, team_id=team.id,
        starts_at=datetime.now() - timedelta(hours=2),
        ends_at=datetime.now() - timedelta(hours=1, minutes=30),
        title="old",
        status="scheduled",
    )

    new_ends = datetime.now() - timedelta(hours=1)
    payload = MeetingUpdate(title="new", ends_at=new_ends)
    updated = await MeetingCRUD.update_meeting(meeting_id=m.id, payload=payload, session=session)

    assert updated.title == "new"
    assert updated.ends_at == new_ends
    status_val = updated.status.value if hasattr(updated.status, "value") else updated.status
    assert status_val == "canceled"

    with pytest.raises(HTTPException) as exc:
        await MeetingCRUD.update_meeting(meeting_id=m.id + 999, payload=MeetingUpdate(title="x"), session=session)
    assert exc.value.status_code == 404
