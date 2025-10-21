from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

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
