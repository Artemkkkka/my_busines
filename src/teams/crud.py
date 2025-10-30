from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from .models import Team
from .schemas import TeamCreate, TeamMemberIn, TeamMemberRead, TeamRead, UserShort, TeamMembersDelete
from src.users.models import User, TeamRole


async def create_team(team_create: TeamCreate, session: AsyncSession, user: User):
    team = Team(name=team_create.name, owner_id=user.id)
    session.add(team)
    await session.flush()

    team_create.members.append(TeamMemberIn(user_id=user.id, role=TeamRole.admin))

    incoming_ids = {member.user_id for member in team_create.members}
    roles_by_user_id = {
        member.user_id: member.role for member in team_create.members
    }

    found_ids = set(
        (await session.execute(
            select(User.id).where(User.id.in_(incoming_ids))
        )).scalars().all()
    )
    missing = sorted(incoming_ids - found_ids)
    if missing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Users not found: {missing}")

    conflicts = (await session.execute(
        select(User.id).where(
            User.id.in_(found_ids),
            User.team_id.is_not(None),
            User.team_id != team.id,
        )
    )).scalars().all()

    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Users already in another team: {sorted(conflicts)}"
        )

    db_users = (await session.execute(
        select(User).where(User.id.in_(found_ids))
    )).scalars().all()

    for user in db_users:
        user.team_id = team.id
        user.role_in_team = roles_by_user_id.get(user.id)




    await session.commit()
    res = await session.execute(
        select(Team)
        .options(selectinload(Team.members))
        .where(Team.id == team.id)
    )
    team = res.scalar_one()
    team_read = TeamRead(
        name=team.name,
        members=[
            TeamMemberRead(
                user=UserShort(id=user.id, email=user.email),
                role=user.role_in_team,
            )
            for user in team.members
        ],
    )
    return team_read


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
            user=UserShort(id=row.id, email=row.email),
            role=row.role_in_team or TeamRole.employee,
        )
        for row in rows]

    return TeamRead(name=team.name, members=members)


async def get_all_team(session: AsyncSession):
    teams = (await session.execute(select(Team).order_by(Team.id))).scalars().all()
    if not teams:
        return []

    team_ids = [team.id for team in teams]

    q_users = (
        select(User.id, User.email, User.role_in_team, User.team_id)
        .where(User.team_id.in_(team_ids))
        .order_by(User.team_id, User.id)
    )
    rows = (await session.execute(q_users)).all()

    members_by_team: dict[int, list[TeamMemberRead]] = {tid: [] for tid in team_ids}
    for row in rows:
        members_by_team[row.team_id].append(
            TeamMemberRead(
                user=UserShort(id=row.id, email=row.email),
                role=row.role_in_team or TeamRole.employee,
            )
        )

    return [
        TeamRead(name=team.name, members=members_by_team.get(team.id, []))
        for team in teams
    ]


async def update_team(
    session: AsyncSession,
    team_id: int,
    new_name: str | None = None,
    members: list[TeamMemberIn] | None = None,
) -> TeamRead:
    res = await session.execute(
        select(Team)
        .options(selectinload(Team.members))
        .where(Team.id == team_id)
    )
    team = res.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if new_name is not None:
        team.name = new_name

    if members:
        roles_by_user_id: dict[int, TeamRole] = {}
        for member in members:
            roles_by_user_id[member.user_id] = member.role

        incoming_ids = set(roles_by_user_id.keys())
        res = await session.execute(select(User).where(User.id.in_(incoming_ids)))
        db_users: Sequence[User] = res.scalars().all()

        found_ids = set(
            (await session.execute(
                select(User.id).where(User.id.in_(incoming_ids))
            )).scalars().all()
        )

        missing = sorted(incoming_ids - found_ids)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Users not found: {missing}"
            )
        conflicts = (await session.execute(
            select(User.id).where(
                User.id.in_(found_ids),
                User.team_id.is_not(None),
                User.team_id != team.id,
            )
        )).scalars().all()
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Users already in another team: {sorted(conflicts)}"
            )

        for user in db_users:
            user.team_id = team.id
            user.role_in_team = roles_by_user_id.get(user.id, user.role_in_team)

    session.add(team)
    await session.commit()

    res = await session.execute(
        select(Team)
        .options(selectinload(Team.members))
        .where(Team.id == team.id)
    )

    return TeamRead(
        name=team.name,
        members=[
            TeamMemberRead(
                user=UserShort(id=u.id, email=u.email),
                role=u.role_in_team
            )
            for u in team.members
        ],
    )


async def delete_team(session: AsyncSession, team_id: int) -> bool:
    try:
        exists = await session.scalar(
            select(Team.id).where(Team.id == team_id)
        )
        if not exists:
            return False
        await session.execute(
            update(User)
            .where(User.team_id == team_id)
            .values(team_id=None, role_in_team=TeamRole.employee)
        )
        await session.execute(
            delete(Team).where(Team.id == team_id)
        )

        await session.commit()
        return True

    except IntegrityError:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise


async def list_team_users(
    team_id: int,
    session: AsyncSession,
):
    res = await session.execute(
        select(User)
        .where(User.team_id == team_id)
        .order_by(User.id)
    )
    users = res.scalars().all()

    if not users:
        exists = await session.execute(select(Team.id).where(Team.id == team_id))
        if exists.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Team not found")

    return [
        TeamMemberRead(
            user=UserShort(id=u.id, email=u.email),
            role=u.role_in_team,
        )
        for u in users
    ]


async def remove_team_users(
    team_id: int,
    payload: TeamMembersDelete,
    session: AsyncSession,
):
    res = await session.execute(
        select(Team).options(selectinload(Team.members)).where(Team.id == team_id)
    )
    team = res.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    to_remove_ids = set(payload.user_ids)

    if team.owner_id in to_remove_ids:
        raise HTTPException(status_code=400, detail="Cannot remove team owner")

    res = await session.execute(select(User).where(User.id.in_(to_remove_ids)))
    db_users = res.scalars().all()
    found_ids = {u.id for u in db_users}
    missing = sorted(to_remove_ids - found_ids)
    if missing:
        raise HTTPException(
            status_code=404, detail=f"Users not found: {missing}"
        )

    not_in_team = sorted([u.id for u in db_users if u.team_id != team.id])
    if not_in_team:
        raise HTTPException(
            status_code=409,
            detail=f"Users not in this team: {not_in_team}",
        )

    current_admin_ids = {u.id for u in team.members if u.role_in_team == TeamRole.admin}
    admins_after = current_admin_ids - to_remove_ids
    if not admins_after:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove the last admin of the team",
        )

    for u in db_users:
        u.team_id = None
        u.role_in_team = TeamRole.employee

    await session.commit()

    res = await session.execute(
        select(User)
        .where(User.team_id == team.id)
        .order_by(User.id)
    )
    users_left = res.scalars().all()

    return [
        TeamMemberRead(user=UserShort(id=u.id, email=u.email), role=u.role_in_team)
        for u in users_left
    ]
