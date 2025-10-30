from typing import Optional
import logging

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin

from src.users.models import User
from src.config import settings
from src.database import get_user_db


log = logging.getLogger(__name__)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = settings.secret
    verification_token_secret = settings.secret

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        log.warning(
            "User " + str(user.id) + " has registered.",
        )

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        log.warning("User " + str(user.id) + " has forgot their password. Reset token: " + str(token))

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        log.warning("Verification requested for user " + str(user.id) + ". Verification token: " + str(token))


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
