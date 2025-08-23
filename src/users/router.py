from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .crud import (
    create_user as crud_create_user,
    get_user as crud_get_user,
    get_all_users as crud_get_all_users,
    update_user as crud_update_user,
    delete_user as crud_delete_user,
    )
from .schemas import UserRead, UserCreate, UserUpdate
from src.database import db_helper



users_router = APIRouter(
    prefix='/user',
    tags=['user'],
)


@users_router.post("/", response_model=UserRead)
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    user = await crud_create_user(session, email=payload.email, password=payload.password)
    return user

@users_router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    user = await crud_get_user(user_id=user_id, session=session)
    return user

@users_router.get("/")
async def get_users(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> list[UserRead]:
    users = await crud_get_all_users(session=session)
    return users

@users_router.patch("/{user_id}",  response_model=UserRead)
async def update_user(
    user_id: int, 
    payload: UserUpdate,
    session: AsyncSession = Depends(db_helper.session_getter),
) -> list[UserRead]:
    user = await crud_update_user(session, user_id, payload.email, payload.password)
    return user

@users_router.delete("/{user_id}")
async def delete_user(
    user_id: int, 
    session: AsyncSession = Depends(db_helper.session_getter),
):
    await crud_delete_user(session, user_id)

    return {"message": "user was deleted"}
