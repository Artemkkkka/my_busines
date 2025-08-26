from fastapi_users import FastAPIUsers

from .schemas import UserUpdate
from src.users.models import User
from src.auth.manager import get_user_manager
from src.auth.backend import auth_backend


fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_user = fastapi_users.current_user()
current_superuser = fastapi_users.current_user(superuser=True)
