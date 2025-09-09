from datetime import datetime, date, time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from src.core.dependencies import CurrentUser, SessionDep
from src.meetings.models import Meeting
from src.meetings.crud import (
    create_meeting as crud_create_meeting,
    get_meetings_by_date as crud_get_meetings_by_date,
    get_user_meetings as crud_get_user_meetings,
    get_team_meetings as crud_get_team_meetings,
    get_meeting as crud_get_meeting,
    update_meeting as crud_update_meeting,
    delete_meeting as crud_delete_meeting,
)
from src.meetings.schemas import MeetingCreate, MeetingUpdate, MeetingOut


meetings_router = APIRouter(prefix="/meetings", tags=["meetings"])


async def _validate_times(starts_at: Optional[datetime], ends_at: Optional[datetime]) -> None:
    if starts_at is not None and ends_at is not None:
        if ends_at <= starts_at:
            raise HTTPException(status_code=400, detail="ends_at must be after starts_at")


@meetings_router.post("", response_model=MeetingOut, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    payload: MeetingCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    await _validate_times(payload.starts_at, payload.ends_at)
    meeting = await crud_create_meeting(
        user=current_user,
        payload=payload,
        session=session,
    )

    return meeting


# 2) Получение встреч по дате (team_id = team пользователя)
@meetings_router.get("/by-date", response_model=List[MeetingOut])
async def get_meetings_by_date(
    session: SessionDep,
    current_user: CurrentUser,
    date: datetime = Query(..., alias="moment", description="ГГГГ-ММ-ДДTчч:мм:сс"),
):
    list_meeting = await crud_get_meetings_by_date(
        user=current_user,
        date=date,
        session=session,
    )

    return list_meeting


# 3) Получение всех встреч пользователя (созданных им) в его команде
@meetings_router.get("/my", response_model=List[MeetingOut])
async def get_user_meetings(
    session: SessionDep,
    current_user: CurrentUser,
):
    list_meetings = await crud_get_user_meetings(
        session=session,
        requester=current_user,
    )

    return list_meetings


# 4) Получение всех встреч команды пользователя
@meetings_router.get("/team", response_model=List[MeetingOut])
async def get_team_meetings(
    session: SessionDep,
    current_user: CurrentUser,
):
    meetings = await crud_get_team_meetings(
        session=session,
        user=current_user,
    )

    return meetings


@meetings_router.get("/{meeting_id}", response_model=MeetingOut)
async def get_meeting(
    meeting_id: int,
    session: SessionDep,
    current_user: CurrentUser,
):
    return await crud_get_meeting(
        meeting_id=meeting_id,
        session=session,
    )


# 5) Обновление встречи (частичное). Если ends_at передан — status="canceled".
@meetings_router.patch("/{meeting_id}", response_model=MeetingOut)
async def update_meeting(
    meeting_id: int,
    payload: MeetingUpdate,
    session: SessionDep,
    current_user: CurrentUser,
):
    await _validate_times(payload.starts_at, payload.ends_at)

    obj = await crud_update_meeting(
        meeting_id=meeting_id,
        payload=payload,
        session=session,
    )
    return obj


# 6) Удаление встречи в пределах команды пользователя
@meetings_router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: int,
    session: SessionDep,
    current_user: CurrentUser,
):
    return await crud_delete_meeting(
        meeting_id=meeting_id,
        session=session,
    )

