# tests/test_create_team.py
import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import StaticPool, select
from sqlalchemy.orm import registry

# --- поправьте импорты под свой проект ---
# Модели/enum
from src.teams.models import Base, Team
from src.users.models import TeamRole, User

# Pydantic-схемы
from src.teams.schemas import TeamCreate, TeamMemberIn

# Функция под тестом
from src.teams.crud import (
    create_team,
    get_team,
    get_all_team,
    update_team,
    delete_team,
    list_team_users,
    remove_team_users,
)

pytestmark = pytest.mark.asyncio

# ---------- ФИКСТУРЫ БД ----------


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture  # <-- scope по умолчанию = 'function': новая БД на каждый тест
async def engine():
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,  # один и тот же коннект в рамках ЭТОГО теста
        future=True,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        await eng.dispose()

@pytest_asyncio.fixture
async def session(engine):
    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with Session() as s:
        # НЕ начинаем транзакцию вручную и НЕ делаем rollback — SUT может коммитить
        yield s


# ---------- ХЕЛПЕРЫ ----------


async def _make_user(
    session: AsyncSession,
    email: str,
    *,
    role: TeamRole = TeamRole.employee,
    team_id: int | None = None,
):
    # SQLAlchemyBaseUserTable обычно требует эти поля
    u = User(
        email=email,
        hashed_password="not-really-hashed",  # тестовый placeholder
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

# --- TESTS ---------------------------------------------------

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


async def test_create_team_ignores_nonexistent_member_ids(session: AsyncSession):
    owner = await _make_user(session, "owner@example.com")
    existing = await _make_user(session, "exists@example.com")

    payload = TeamCreate(
        name="Ghosts",
        members=[
            TeamMemberIn(user_id=existing.id, role=TeamRole.employee),
            TeamMemberIn(user_id=99999, role=TeamRole.admin),  # не существует
        ],
    )

    team_read = await create_team(payload, session, user=owner)

    db_team = (await session.execute(select(Team).where(Team.name == "Ghosts"))).scalar_one()
    team_users = (await session.execute(select(User).where(User.team_id == db_team.id))).scalars().all()

    assert {u.id for u in team_users} == {owner.id, existing.id}

    by_id = {u.id: u for u in team_users}
    assert by_id[owner.id].role_in_team == TeamRole.admin
    assert by_id[existing.id].role_in_team == TeamRole.employee

    returned_ids = {m.user.id for m in team_read.members}
    assert returned_ids == {owner.id, existing.id}


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
            TeamMemberIn(user_id=owner.id, role=TeamRole.employee),  # попытка занизить роль владельца
            TeamMemberIn(user_id=dup.id, role=TeamRole.admin),
            TeamMemberIn(user_id=dup.id, role=TeamRole.employee),    # дубликат — должна победить последняя роль
        ],
    )

    team_read = await create_team(payload, session, user=owner)

    db_team = (await session.execute(select(Team).where(Team.name == "Dedup"))).scalar_one()
    users = (await session.execute(select(User).where(User.team_id == db_team.id))).scalars().all()
    by_id = {u.id: u for u in users}

    assert by_id[owner.id].role_in_team == TeamRole.admin     # владелец всегда admin
    assert by_id[dup.id].role_in_team == TeamRole.employee    # “последний побеждает”

    ret = {m.user.id: m.role for m in team_read.members}
    assert ret[owner.id] == TeamRole.admin
    assert ret[dup.id] == TeamRole.employee

async def test_get_team_returns_members_and_defaults_role(session: AsyncSession):
    team = await _make_team(session, "Alpha")
    # роли: admin, employee и None -> должен дефолтиться к employee
    u1 = await _make_user(session, "a1@example.com", role=TeamRole.admin, team_id=team.id)
    u2 = await _make_user(session, "a2@example.com", role=TeamRole.employee, team_id=team.id)
    u3 = await _make_user(session, "a3@example.com", role=None, team_id=team.id)

    dto = await get_team(team.id, session)

    assert dto.name == "Alpha"
    # порядок по id
    got_ids = [m.user.id for m in dto.members]
    assert got_ids == sorted([u1.id, u2.id, u3.id])
    # роли
    by_id = {m.user.id: m.role for m in dto.members}
    assert by_id[u1.id] == TeamRole.admin
    assert by_id[u2.id] == TeamRole.employee
    assert by_id[u3.id] == TeamRole.employee  # default for None

    # 404 для несуществующей команды
    with pytest.raises(HTTPException) as ei:
        await get_team(999_999, session)
    assert ei.value.status_code == 404


async def test_get_all_team_returns_all_with_members(session: AsyncSession):
    t1 = await _make_team(session, "A")
    t2 = await _make_team(session, "B")
    # участники
    await _make_user(session, "b1@example.com", role=TeamRole.admin, team_id=t1.id)
    await _make_user(session, "b2@example.com", role=TeamRole.employee, team_id=t2.id)
    await _make_user(session, "b3@example.com", role=TeamRole.employee, team_id=t2.id)

    teams = await get_all_team(session)

    assert [t.name for t in teams] == ["A", "B"]  # порядок по Team.id
    members_count = {t.name: len(t.members) for t in teams}
    assert members_count == {"A": 1, "B": 2}


async def test_update_team_renames_and_adds_members(session: AsyncSession):
    # существующая команда с 1 участником
    owner = await _make_user(session, "owner@example.com")
    team = await _make_team(session, "Old", owner_id=owner.id)
    existing = await _make_user(session, "ex@example.com", role=TeamRole.employee, team_id=team.id)

    # новые пользователи, которых добавим
    nu1 = await _make_user(session, "n1@example.com")  # пока без команды
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

    # имя обновилось
    assert dto.name == "New"

    # проверяем факт привязки и роли — источник истины БД
    rows = (await session.execute(select(User).where(User.team_id == team.id))).scalars().all()
    assert {u.id for u in rows} == {existing.id, nu1.id, nu2.id}
    by_id = {u.id: u for u in rows}
    assert by_id[nu1.id].role_in_team == TeamRole.admin
    assert by_id[nu2.id].role_in_team == TeamRole.employee

    # дополнительно сверим “публичное” представление через get_team (он собирает список участников корректно)
    team_after = await get_team(team.id, session)
    ids = {m.user.id for m in team_after.members}
    assert ids == {existing.id, nu1.id, nu2.id}
    roles = {m.user.id: m.role for m in team_after.members}
    assert roles[nu1.id] == TeamRole.admin
    assert roles[nu2.id] == TeamRole.employee


async def test_delete_team_unlinks_members_and_deletes_team(session: AsyncSession):
    t = await _make_team(session, "ToDel")
    u1 = await _make_user(session, "d1@example.com", role=TeamRole.admin, team_id=t.id)
    u2 = await _make_user(session, "d2@example.com", role=TeamRole.employee, team_id=t.id)

    ok = await delete_team(session, t.id)
    assert ok is True

    # команда удалена
    assert (await session.execute(select(Team).where(Team.id == t.id))).scalar_one_or_none() is None
    # пользователи отвязаны и получили безопасную роль employee
    users = (await session.execute(select(User).where(User.id.in_([u1.id, u2.id])))).scalars().all()
    assert all(u.team_id is None for u in users)
    assert all(u.role_in_team == TeamRole.employee for u in users)

    # несуществующая команда -> False
    assert await delete_team(session, 999_999) is False


async def test_list_team_users_returns_sorted_and_404_for_missing_team(session: AsyncSession):
    t = await _make_team(session, "List")
    u1 = await _make_user(session, "l1@example.com", role=TeamRole.admin, team_id=t.id)
    u2 = await _make_user(session, "l2@example.com", role=TeamRole.employee, team_id=t.id)

    members = await list_team_users(t.id, session)
    assert [m.user.id for m in members] == sorted([u1.id, u2.id])
    assert {m.user.id: m.role for m in members} == {u1.id: TeamRole.admin, u2.id: TeamRole.employee}

    # пустая команда возвращает пустой список
    t_empty = await _make_team(session, "Empty")
    assert await list_team_users(t_empty.id, session) == []

    # несуществующая команда -> 404
    with pytest.raises(HTTPException) as ei:
        await list_team_users(999_999, session)
    assert ei.value.status_code == 404


async def test_remove_team_users_success(session: AsyncSession):
    # владелец (админ), плюс ещё админ и сотрудник
    owner = await _make_user(session, "r-owner@example.com", role=TeamRole.admin)
    team = await _make_team(session, "Remove", owner_id=owner.id)
    owner.team_id = team.id  # явно включим владельца в состав

    admin2 = await _make_user(session, "r-admin@example.com", role=TeamRole.admin, team_id=team.id)
    emp = await _make_user(session, "r-emp@example.com", role=TeamRole.employee, team_id=team.id)

    # удаляем НЕ владельца
    left = await remove_team_users(team.id, payload=type("P", (), {"user_ids": [emp.id]}), session=session)

    # остались владелец и второй админ
    left_ids = {m.user.id for m in left}
    assert left_ids == {owner.id, admin2.id}

    # удалённый отвязан и роль сброшена
    emp_db = (await session.execute(select(User).where(User.id == emp.id))).scalar_one()
    assert emp_db.team_id is None and emp_db.role_in_team == TeamRole.employee
