'''
1) Создание встречи. 
team_id проставляется в соответствии с team_id пользователя, которой создаёт ручку

2) Получение встречи по дате.
team_id проставляется в соответствии с team_id пользователя, которой дёргает ручку

3) Получение всех встреч пользователя. 
team_id проставляется в соответствии с team_id пользователя, которой дёргает ручку


4) Получение всех встреч команды.
team_id проставляется в соответствии с team_id пользователя, которой дёргает ручку
только админ или суперюзер
'''
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select, and_, exists
from sqlalchemy.orm import selectinload

from src.users.models import User
from src.meetings.models import Meeting, MeetingStatus, meeting_participants
from src.meetings.schemas import MeetingCreate, MeetingUpdate
from src.core.dependencies import AsyncSession


async def create_meeting(
    user: User,
    payload: MeetingCreate,
    session: AsyncSession
):
    obj = Meeting(
        team_id=user.team_id,
        title=payload.title,
        description=payload.description,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        status="scheduled",
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)

    return obj

async def get_meetings_by_date(
    user: User,
    date: datetime,
    session: AsyncSession,
):
    stmt = (
        select(Meeting)
        .where(
            and_(
                Meeting.team_id == user.team_id,
                Meeting.starts_at >= date,
                Meeting.starts_at <= datetime.now(),
            )
        )
        .order_by(Meeting.starts_at.asc())
    )

    return list(await session.scalars(stmt))


async def get_user_meetings(
    session: AsyncSession,
    requester: User,
    include_canceled: bool = False,
    starts_after: datetime | None = None,
    ends_before: datetime | None = None,
    limit: int | None = None,
) -> list[Meeting]:
    if requester.team_id is None:
        return []

    base_filters = [Meeting.team_id == requester.team_id]

    if not include_canceled:
        base_filters.append(Meeting.status == MeetingStatus.scheduled)

    # Временное окно — аккуратно по двум столбцам
    if starts_after is not None:
        base_filters.append(Meeting.ends_at >= starts_after)
    if ends_before is not None:
        base_filters.append(Meeting.starts_at <= ends_before)

    # База запроса
    stmt = (
        select(Meeting)
        .where(and_(*base_filters))
        .options(selectinload(Meeting.participants))
        .order_by(Meeting.starts_at.asc(), Meeting.id.asc())
    )

    if limit is not None:
        stmt = stmt.limit(limit)

    result = await session.scalars(stmt)
    # Из-за join возможны дубликаты: unique() убирает их на уровне ORM
    return result.unique().all()


async def get_team_meetings(
    session: AsyncSession,
    user: User,
):
    stmt = (
        select(Meeting)
        .where(Meeting.team_id == user.team_id)
        .order_by(Meeting.starts_at.desc())
    )

    return list(await session.scalars(stmt))

async def get_meeting(
    meeting_id: int,
    session: AsyncSession,
):
    return await session.get(Meeting, meeting_id)


async def update_meeting(
    meeting_id: int,
    payload: MeetingUpdate,
    session: AsyncSession,
):
    obj = await session.get(Meeting, meeting_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # применяем изменения
    data = payload.model_dump(exclude_unset=True)
    print(data)
    for k, v in data.items():
        setattr(obj, k, v)

    # спец-правило: ends_at в апдейте => canceled
    if "ends_at" in data and data["ends_at"] is not None:
        obj.status = "canceled"

    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_meeting(
    meeting_id: int,
    session: AsyncSession,
):
    obj = await session.get(Meeting, meeting_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Meeting not found")

    await session.delete(obj)
    await session.commit()