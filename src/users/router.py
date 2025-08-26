import contextlib

from fastapi import APIRouter
from src.core.dependencies import CurrentUser, SessionDep
from src.users.crud import delete_user as delete_user_crud


from fastapi import Depends, APIRouter, status
from fastapi.responses import JSONResponse

from src.auth.manager import UserManager, get_user_manager


users_router = APIRouter()


@users_router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "User not found"}},
)
async def delete_me(
    user: CurrentUser,
    user_manager: UserManager = Depends(get_user_manager),
):
    """
    Удаление текущего пользователя
    """
    await user_manager.delete(user)
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
