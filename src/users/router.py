from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import db_helper
from .crud import create_user as crud_create_user
from .schemas import UserRead, UserCreate


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
