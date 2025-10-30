import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from src.teams.crud import (
    create_team,
)
from src.teams.models import Team
from src.teams.schemas import TeamCreate, TeamMemberIn
from src.users.models import TeamRole, User
from tests.helpers import _make_team, _make_user


pytestmark = pytest.mark.asyncio


async def test_create_team_success_adds_owner_and_members(session: AsyncSession):
    owner = await _make_user(session, "owner@example.com")
    emp = await _make_user(session, "emp@example.com")
    adm = await _make_user(session, "adm@example.com")

    payload = TeamCreate(
        name="Platform",
        members=[
            TeamMemberIn(user_id=emp.id, role=TeamRole.employee),
            TeamMemberIn(user_id=adm.id, role=TeamRole.admin),
        ],
    )

    team_read = await create_team(payload, session, user=owner)

    db_team = (await session.execute(select(Team).where(Team.name == "Platform"))).scalar_one()
    assert db_team.owner_id == owner.id

    team_users = (await session.execute(select(User).where(User.team_id == db_team.id))).scalars().all()
    assert {u.id for u in team_users} == {owner.id, emp.id, adm.id}

    by_id = {u.id: u for u in team_users}
    assert by_id[owner.id].role_in_team == TeamRole.admin
    assert by_id[emp.id].role_in_team == TeamRole.employee
    assert by_id[adm.id].role_in_team == TeamRole.admin

    returned = {(m.user.id, m.role) for m in team_read.members}
    expected = {(owner.id, TeamRole.admin), (emp.id, TeamRole.employee), (adm.id, TeamRole.admin)}
    assert returned == expected
    assert team_read.name == "Platform"


async def test_create_team_rejects_nonexistent_member_ids(session):
    owner = await _make_user(session, "owner@example.com")
    existing = await _make_user(session, "exists@example.com")

    payload = TeamCreate(
        name="Ghosts",
        members=[
            TeamMemberIn(user_id=existing.id, role=TeamRole.employee),
            TeamMemberIn(user_id=99999, role=TeamRole.admin),
        ],
    )

    with pytest.raises(HTTPException) as exc:
        await create_team(payload, session, user=owner)

    assert exc.value.status_code == 404
    assert "Users not found" in str(exc.value.detail)

    owner_db = (await session.execute(select(User).where(User.id == owner.id))).scalar_one()
    existing_db = (await session.execute(select(User).where(User.id == existing.id))).scalar_one()
    assert owner_db.team_id is None
    assert existing_db.team_id is None


async def test_create_team_conflict_when_user_in_another_team(session: AsyncSession):
    owner = await _make_user(session, "owner@example.com")
    foreign_team = await _make_team(session, "Other")
    busy = await _make_user(session, "busy@example.com", team_id=foreign_team.id)

    payload = TeamCreate(
        name="NewTeam",
        members=[TeamMemberIn(user_id=busy.id, role=TeamRole.employee)],
    )

    with pytest.raises(HTTPException) as ei:
        await create_team(payload, session, user=owner)

    assert ei.value.status_code == 409
    assert str(busy.id) in str(ei.value.detail)

    busy_after = (await session.execute(select(User).where(User.id == busy.id))).scalar_one()
    assert busy_after.team_id == foreign_team.id


async def test_create_team_duplicate_members_last_wins_and_owner_overrides_to_admin(session: AsyncSession):
    owner = await _make_user(session, "owner@example.com")
    dup = await _make_user(session, "dup@example.com")

    payload = TeamCreate(
        name="Dedup",
        members=[
            TeamMemberIn(user_id=owner.id, role=TeamRole.employee),
            TeamMemberIn(user_id=dup.id, role=TeamRole.admin),
            TeamMemberIn(user_id=dup.id, role=TeamRole.employee),
        ],
    )

    team_read = await create_team(payload, session, user=owner)

    db_team = (await session.execute(select(Team).where(Team.name == "Dedup"))).scalar_one()
    users = (await session.execute(select(User).where(User.team_id == db_team.id))).scalars().all()
    by_id = {u.id: u for u in users}

    assert by_id[owner.id].role_in_team == TeamRole.admin
    assert by_id[dup.id].role_in_team == TeamRole.employee

    ret = {m.user.id: m.role for m in team_read.members}
    assert ret[owner.id] == TeamRole.admin
    assert ret[dup.id] == TeamRole.employee
