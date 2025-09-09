from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User


async def delete_user(session: AsyncSession, user_id: int):
    stmt = delete(User).where(User.id == user_id)
    await session.execute(stmt)
    await session.commit()
