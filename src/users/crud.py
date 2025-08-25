from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User

# # TODO: добавить проверку уникальности юзера
# async def create_user(session: AsyncSession, email: str, password: str):
#     user = User(email=email, password=password)
#     session.add(user)
#     await session.commit()

#     return user

# # TODO: добавить проверку наличия юзера
# async def get_user(session: AsyncSession, user_id: int):
#     stmt = select(User).where(User.id == user_id)
#     result = await session.execute(stmt)
#     user = result.scalar_one()

#     return user

# async def get_all_users(session: AsyncSession):
#     stmt = select(User)
#     result = await session.execute(stmt)

#     users = result.scalars(result)

#     return users

# # TODO: можно ли поменять на email, который уже есть в БД?
# async def update_user(session: AsyncSession, user_id: int, new_email: str, new_password: str):
#     user = await get_user(session, user_id)
#     user.email = new_email
#     user.password = new_password

#     session.add(user)
#     await session.commit()

#     return user

async def delete_user(session: AsyncSession, user_id: int):
    stmt = delete(User).where(User.id == user_id)
    await session.execute(stmt)
    await session.commit()
