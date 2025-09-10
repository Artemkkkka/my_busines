from sqlalchemy import and_, cast, DateTime, literal
from sqlalchemy import select
from fastapi import HTTPException, status

from src.meetings.models import Meeting, MeetingStatus


async def ensure_no_overlap(
    session,
    *,
    team_id: int,
    starts_at,
    ends_at,
    exclude_meeting_id: int | None = None,
) -> None:
    conds = [
        Meeting.ends_at > starts_at,
        Meeting.starts_at < ends_at,
        Meeting.team_id == team_id,
        Meeting.status == MeetingStatus.scheduled,
    ]
    if exclude_meeting_id is not None:
        conds.append(Meeting.id != exclude_meeting_id)

    q = select(literal(True)).where(and_(*conds)).limit(1)
    exists_ = await session.scalar(q)
    if exists_:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Нельзя назначить встречу на пересекающиеся даты")
