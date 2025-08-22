from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User


async def create_user(session: AsyncSession, email: str, password: str):
    user = User(email=email, password=password)
    session.add(user)
    await session.commit()

    return user

async def get_user(session: AsyncSession, user_id: int):
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one()

    return user