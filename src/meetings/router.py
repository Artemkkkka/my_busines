from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query, status

from .validators import _validate_times
from src.core.dependencies import CurrentUser, SessionDep
from src.evaluations.permissions import forbid_employee
from src.users.models import User
from src.meetings.checks.check_time import ensure_no_overlap
from src.meetings.crud import MeetingCRUD
from src.meetings.schemas import MeetingCreate, MeetingUpdate, MeetingOut


crud = MeetingCRUD()
meetings_router = APIRouter(prefix="/meetings", tags=["meetings"])


@meetings_router.post("", response_model=MeetingOut, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    payload: MeetingCreate,
    session: SessionDep,
    current_user: User = Depends(forbid_employee),
):
    await _validate_times(payload.starts_at, payload.ends_at)

    await ensure_no_overlap(
        session,
        team_id=current_user.team_id,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
    )

    meeting = await crud.create_meeting(
        user=current_user,
        payload=payload,
        session=session,
    )
    return meeting


@meetings_router.get("/by-date", response_model=List[MeetingOut])
async def get_meetings_by_date(
    session: SessionDep,
    current_user: User = Depends(forbid_employee),
    date: datetime = Query(..., alias="moment", description="ГГГГ-ММ-ДДTчч:мм:сс"),
):
    list_meeting = await crud.get_meetings_by_date(
        user=current_user,
        date=date,
        session=session,
    )

    return list_meeting


@meetings_router.get("/my", response_model=List[MeetingOut])
async def get_user_meetings(
    session: SessionDep,
    current_user: CurrentUser,
    include_canceled: bool = Query(
        False, description="Include canceled meetings"
    ),
    starts_after: datetime | None = Query(
        None, description="Filter meetings starting after this time"
    ),
    ends_before: datetime | None = Query(
        None, description="Filter meetings ending before this time"
    ),
    limit: int | None = Query(
        None, description="Limit the number of results"
    ),
):
    list_meetings = await crud.get_user_meetings(
        session=session,
        requester=current_user,
        include_canceled=include_canceled,
        starts_after=starts_after,
        ends_before=ends_before,
        limit=limit,
    )

    return list_meetings


@meetings_router.get("/team", response_model=List[MeetingOut])
async def get_team_meetings(
    session: SessionDep,
    current_user: User = Depends(forbid_employee),
):
    meetings = await crud.get_team_meetings(
        session=session,
        user=current_user,
    )

    return meetings


@meetings_router.get("/{meeting_id}", response_model=MeetingOut)
async def get_meeting(
    meeting_id: int,
    session: SessionDep,
):
    return await crud.get_meeting(
        meeting_id=meeting_id,
        session=session,
    )


@meetings_router.patch("/{meeting_id}", response_model=MeetingOut)
async def update_meeting(
    meeting_id: int,
    payload: MeetingUpdate,
    session: SessionDep,
    current_user: User = Depends(forbid_employee),
):
    await _validate_times(payload.starts_at, payload.ends_at)

    obj = await crud.update_meeting(
        meeting_id=meeting_id,
        payload=payload,
        session=session,
    )
    return obj


@meetings_router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: int,
    session: SessionDep,
    current_user: User = Depends(forbid_employee),
):
    return await crud.delete_meeting(
        meeting_id=meeting_id,
        session=session,
    )
