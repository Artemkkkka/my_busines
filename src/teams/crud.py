from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Team
from .schemas import TeamCreate, TeamMemberIn, TeamMemberRead, TeamRead, UserShort
from src.users.models import User, TeamRole


async def create_team(team_create: TeamCreate, session: AsyncSession, user: User):
    team = Team(name=team_create.name, owner_id=user.id)
    team.owner_id = user.id
    session.add(team)
    await session.flush()

    team_create.members.append(TeamMemberIn(user_id=user.id, role=TeamRole.admin))
    dct_members = {m.user_id: m.role for m in team_create.members}

    incoming_ids = {member.user_id for member in team_create.members}
    user_ids = list(incoming_ids)

    res = await session.execute(select(User).where(User.id.in_(user_ids)))
    db_users: list[User] = res.scalars().all()

    conflicts = [u.id for u in db_users if u.team_id and u.team_id != team.id]
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Users already in another team: {sorted(conflicts)}"
        )

    for u in db_users:
        u.team_id = team.id
        u.role_in_team = dct_members.get(u.id)

    await session.commit()
    await session.refresh(team)

    return team


async def get_team(team_id: int, session: AsyncSession) -> TeamRead:
    stmt_team = select(Team).where(Team.id == team_id)
    team = (await session.execute(stmt_team)).scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    q = (
        select(User.id, User.email, User.role_in_team)
        .where(User.team_id == team_id)
        .order_by(User.id)
    )
    rows = (await session.execute(q)).all()

    members = [
        TeamMemberRead(
            user=UserShort(id=r.id, email=r.email),
            role=r.role_in_team or TeamRole.employee,
        )
    for r in rows]

    return TeamRead(id=team.id, name=team.name, members=members)


async def get_all_team(session: AsyncSession):
    teams = (await session.execute(select(Team).order_by(Team.id))).scalars().all()
    if not teams:
        return []

    team_ids = [t.id for t in teams]

    q_users = (
        select(User.id, User.email, User.role_in_team, User.team_id)
        .where(User.team_id.in_(team_ids))
        .order_by(User.team_id, User.id)
    )
    rows = (await session.execute(q_users)).all()

    members_by_team: dict[int, list[TeamMemberRead]] = {tid: [] for tid in team_ids}
    for r in rows:
        members_by_team[r.team_id].append(
            TeamMemberRead(
                user=UserShort(id=r.id, email=r.email),
                role=r.role_in_team or TeamRole.employee,
            )
        )

    return [
        TeamRead(id=t.id, name=t.name, members=members_by_team.get(t.id, []))
        for t in teams
    ]

async def update_team(session: AsyncSession, team_id: int, new_name: str):
    team = await get_team(team_id, session)
    team.name = new_name

    session.add(team)
    await session.commit()

    return team

async def delete_team(session: AsyncSession, team_id: int):
    stmt = delete(Team).where(Team.id == team_id)
    await session.execute(stmt)
    await session.commit()