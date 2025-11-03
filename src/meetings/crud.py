from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from src.users.models import User
from src.meetings.models import Meeting, MeetingStatus
from src.meetings.schemas import MeetingCreate, MeetingUpdate
from src.core.dependencies import AsyncSession


class MeetingCRUD:
    @staticmethod
    async def create_meeting(
        user: User,
        payload: MeetingCreate,
        session: AsyncSession,
    ) -> Meeting:
        obj = Meeting(
            team_id=user.team_id,
            title=payload.title,
            description=payload.description,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            status=MeetingStatus.scheduled,
        )
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    @staticmethod
    async def get_meetings_by_date(
        user: User,
        date: datetime,
        session: AsyncSession,
    ) -> list[Meeting]:
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
        result = await session.scalars(stmt)
        return list(result.all())

    @staticmethod
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

        filters = [Meeting.team_id == requester.team_id]
        if not include_canceled:
            filters.append(Meeting.status == MeetingStatus.scheduled)
        if starts_after is not None:
            filters.append(Meeting.ends_at >= starts_after)
        if ends_before is not None:
            filters.append(Meeting.starts_at <= ends_before)

        stmt = (
            select(Meeting)
            .where(and_(*filters))
            .options(selectinload(Meeting.participants))
            .order_by(Meeting.starts_at.asc(), Meeting.id.asc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await session.scalars(stmt)
        return result.unique().all()

    @staticmethod
    async def get_team_meetings(
        session: AsyncSession,
        user: User,
    ) -> list[Meeting]:
        stmt = (
            select(Meeting)
            .where(Meeting.team_id == user.team_id)
            .order_by(Meeting.starts_at.desc())
        )
        result = await session.scalars(stmt)
        return list(result.all())

    @staticmethod
    async def get_meeting(
        meeting_id: int,
        session: AsyncSession,
    ) -> Meeting | None:
        return await session.get(Meeting, meeting_id)

    @staticmethod
    async def update_meeting(
        meeting_id: int,
        payload: MeetingUpdate,
        session: AsyncSession,
    ) -> Meeting:
        obj = await session.get(Meeting, meeting_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Meeting not found")

        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(obj, k, v)

        if "ends_at" in data and data["ends_at"] is not None:
            obj.status = MeetingStatus.canceled

        await session.commit()
        await session.refresh(obj)
        return obj

    @staticmethod
    async def delete_meeting(
        meeting_id: int,
        session: AsyncSession,
    ) -> None:
        obj = await session.get(Meeting, meeting_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Meeting not found")
        await session.delete(obj)
        await session.commit()
