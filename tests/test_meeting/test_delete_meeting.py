from datetime import datetime, timedelta

from fastapi import HTTPException
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.meetings.crud import MeetingCRUD
from src.meetings.models import Meeting
from tests.helpers import _make_user, _make_team, _make_meeting


@pytest.mark.anyio
async def test_delete_meeting_deletes_and_404_on_missing(session: AsyncSession):
    team = await _make_team(session, "Pi")
    await _make_user(session, "p@p.com", team_id=team.id)
    m = await _make_meeting(
        session, team_id=team.id,
        starts_at=datetime.now() - timedelta(hours=1),
        ends_at=datetime.now() - timedelta(minutes=5),
        title="to-delete",
    )

    await MeetingCRUD.delete_meeting(meeting_id=m.id, session=session)

    gone = await session.get(Meeting, m.id)
    assert gone is None

    with pytest.raises(HTTPException) as exc:
        await MeetingCRUD.delete_meeting(meeting_id=m.id, session=session)
    assert exc.value.status_code == 404
