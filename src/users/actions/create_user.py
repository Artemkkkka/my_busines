import contextlib

from fastapi_users.exceptions import UserAlreadyExists

from src.users.manager import get_user_manager
from src.database import db_helper, get_user_db
from src.auth.schemas import UserCreate


get_async_session_context = contextlib.asynccontextmanager(db_helper.session_getter)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_user(email: str, password: str, is_superuser: bool = False):
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.create(
                        UserCreate(
                            email=email, password=password, is_superuser=is_superuser
                        )
                    )
                    print(f"User created {user}")
                    return user
    except UserAlreadyExists:
        print(f"User {email} already exists")
        raise
