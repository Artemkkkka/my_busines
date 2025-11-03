from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.teams.crud import TeamCRUD
from src.teams.models import Team
from src.users.models import TeamRole, User
from tests.helpers import _make_user, _make_team


crud = TeamCRUD()


async def test_delete_team_unlinks_members_and_deletes_team(session: AsyncSession):
    t = await _make_team(session, "ToDel")
    u1 = await _make_user(session, "d1@example.com", role=TeamRole.admin, team_id=t.id)
    u2 = await _make_user(session, "d2@example.com", role=TeamRole.employee, team_id=t.id)

    ok = await crud.delete_team(session, t.id)
    assert ok is True

    assert (await session.execute(select(Team).where(Team.id == t.id))).scalar_one_or_none() is None
    users = (await session.execute(select(User).where(User.id.in_([u1.id, u2.id])))).scalars().all()
    assert all(u.team_id is None for u in users)
    assert all(u.role_in_team == TeamRole.employee for u in users)

    assert await crud.delete_team(session, 999_999) is False


async def test_remove_team_users_success(session: AsyncSession):
    owner = await _make_user(session, "r-owner@example.com", role=TeamRole.admin)
    team = await _make_team(session, "Remove", owner_id=owner.id)
    owner.team_id = team.id

    admin2 = await _make_user(session, "r-admin@example.com", role=TeamRole.admin, team_id=team.id)
    emp = await _make_user(session, "r-emp@example.com", role=TeamRole.employee, team_id=team.id)

    left = await crud.remove_team_users(team.id, payload=type("P", (), {"user_ids": [emp.id]}), session=session)

    left_ids = {m.user.id for m in left}
    assert left_ids == {owner.id, admin2.id}

    emp_db = (await session.execute(select(User).where(User.id == emp.id))).scalar_one()
    assert emp_db.team_id is None and emp_db.role_in_team == TeamRole.employee
