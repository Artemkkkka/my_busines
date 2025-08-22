from sqlalchemy.ext.asyncio import AsyncSession

from .models import User


async def create_user(session: AsyncSession, email: str, password: str):
    user = User(email=email, password=password)
    session.add(user)
    await session.commit()

    return user
