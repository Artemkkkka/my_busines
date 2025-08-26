import contextlib

from src.auth.manager import get_user_manager, UserManager
from src.database import db_helper, get_user_db
from src.auth.schemas import UserCreate


get_async_session_context = contextlib.asynccontextmanager(db_helper.session_getter)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_user(
    user_manager: UserManager,
    user_create: UserCreate,
):
    user = await user_manager.create(
        user_create=user_create,
        safe=False,
    )
    return user


async def create_superuser(
    email: str = 'admin@admin.com',
    password: str = 'admin_password',
    is_active: bool = True,
    is_superuser: bool = True,
    is_verified: bool = True,

):
    user_create = UserCreate(
        email=email,
        password=password,
        is_active=is_active,
        is_superuser=is_superuser,
        is_verified=is_verified,
    )
    async with get_async_session_context() as session:
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                return await create_user(
                    user_manager=user_manager,
                    user_create=user_create,
                )
