from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.teams.crud import get_team, update_team
from src.teams.schemas import TeamMemberIn
from src.users.models import TeamRole, User
from tests.helpers import _make_user, _make_team


async def test_update_team_renames_and_adds_members(session: AsyncSession):
    owner = await _make_user(session, "owner@example.com")
    team = await _make_team(session, "Old", owner_id=owner.id)
    existing = await _make_user(session, "ex@example.com", role=TeamRole.employee, team_id=team.id)

    nu1 = await _make_user(session, "n1@example.com")
    nu2 = await _make_user(session, "n2@example.com")

    dto = await update_team(
        session=session,
        team_id=team.id,
        new_name="New",
        members=[
            TeamMemberIn(user_id=nu1.id, role=TeamRole.admin),
            TeamMemberIn(user_id=nu2.id, role=TeamRole.employee),
        ],
    )

    assert dto.name == "New"

    rows = (await session.execute(select(User).where(User.team_id == team.id))).scalars().all()
    assert {u.id for u in rows} == {existing.id, nu1.id, nu2.id}
    by_id = {u.id: u for u in rows}
    assert by_id[nu1.id].role_in_team == TeamRole.admin
    assert by_id[nu2.id].role_in_team == TeamRole.employee

    team_after = await get_team(team.id, session)
    ids = {m.user.id for m in team_after.members}
    assert ids == {existing.id, nu1.id, nu2.id}
    roles = {m.user.id: m.role for m in team_after.members}
    assert roles[nu1.id] == TeamRole.admin
    assert roles[nu2.id] == TeamRole.employee

