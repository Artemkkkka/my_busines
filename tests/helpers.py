from datetime import datetime

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from src.meetings.models import Meeting
from src.tasks.models import Status, Task
from src.teams.models import Team
from src.users.models import TeamRole, User


async def _make_user(
    session: AsyncSession,
    email: str,
    *,
    role: TeamRole = TeamRole.employee,
    team_id: int | None = None,
):
    u = User(
        email=email,
        hashed_password="not-really-hashed",
        is_active=True,
        is_superuser=False,
        is_verified=True,
        role_in_team=role,
        team_id=team_id,
    )
    session.add(u)
    await session.flush()
    return u


async def _make_team(session: AsyncSession, name: str, owner_id: int | None = None):
    t = Team(name=name, owner_id=owner_id)
    session.add(t)
    await session.flush()
    return t


async def _make_meeting(
    session: AsyncSession,
    *,
    team_id: int,
    starts_at: datetime,
    ends_at: datetime,
    title: str = "mtg",
    description: str | None = None,
    status: str = "scheduled",
    participants: list[User] = None,
) -> Meeting:
    meeting = Meeting(
        team_id=team_id,
        title=title,
        description=description,
        starts_at=starts_at,
        ends_at=ends_at,
        status=status,
    )
    if participants:
        meeting.participants.extend(participants)
    
    session.add(meeting)
    await session.commit()
    await session.refresh(meeting)
    return meeting

async def _make_task(
    session: AsyncSession,
    *,
    team_id: int,
    author_id: int,
    status: Status = Status.done,
    name: str = "Task",
    description: str = "Dscription Task",
) -> Task:
    obj = Task(
        team_id=team_id,
        author_id=author_id,
        name=name,
        status=status,
        description = description,
        deadline_at = datetime(2025, 1, 1, 1, 1, 1)
    )
    session.add(obj)
    await session.flush()
    return obj
