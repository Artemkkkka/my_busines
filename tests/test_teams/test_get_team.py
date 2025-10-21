from fastapi import HTTPException
import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from src.teams.crud import get_team, get_all_team, list_team_users
from src.users.models import TeamRole
from tests.helpers import _make_user, _make_team


async def test_get_team_returns_members_and_defaults_role(session: AsyncSession):
    team = await _make_team(session, "Alpha")
    u1 = await _make_user(session, "a1@example.com", role=TeamRole.admin, team_id=team.id)
    u2 = await _make_user(session, "a2@example.com", role=TeamRole.employee, team_id=team.id)
    u3 = await _make_user(session, "a3@example.com", role=None, team_id=team.id)

    dto = await get_team(team.id, session)

    assert dto.name == "Alpha"
    got_ids = [m.user.id for m in dto.members]
    assert got_ids == sorted([u1.id, u2.id, u3.id])
    by_id = {m.user.id: m.role for m in dto.members}
    assert by_id[u1.id] == TeamRole.admin
    assert by_id[u2.id] == TeamRole.employee
    assert by_id[u3.id] == TeamRole.employee

    with pytest.raises(HTTPException) as ei:
        await get_team(999_999, session)
    assert ei.value.status_code == 404


async def test_get_all_team_returns_all_with_members(session: AsyncSession):
    t1 = await _make_team(session, "A")
    t2 = await _make_team(session, "B")

    await _make_user(session, "b1@example.com", role=TeamRole.admin, team_id=t1.id)
    await _make_user(session, "b2@example.com", role=TeamRole.employee, team_id=t2.id)
    await _make_user(session, "b3@example.com", role=TeamRole.employee, team_id=t2.id)

    teams = await get_all_team(session)

    assert [t.name for t in teams] == ["A", "B"]
    members_count = {t.name: len(t.members) for t in teams}
    assert members_count == {"A": 1, "B": 2}


async def test_list_team_users_returns_sorted_and_404_for_missing_team(session: AsyncSession):
    t_empty = await _make_team(session, "Empty")
    assert await list_team_users(t_empty.id, session) == []

    with pytest.raises(HTTPException) as ei:
        await list_team_users(999_999, session)
    assert ei.value.status_code == 404
