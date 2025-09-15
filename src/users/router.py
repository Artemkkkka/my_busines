from fastapi import Depends, APIRouter, status
from fastapi.responses import JSONResponse

from src.core.dependencies import CurrentUser
from src.auth.manager import UserManager, get_user_manager
from src.users.models import User


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
    await user_manager.delete(user)
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


@users_router.get("/me-team", status_code=status.HTTP_200_OK)
async def me_team(
    current_user: CurrentUser
):
    return {
        "team_id": current_user.team_id,
        "role_in_team": current_user.role_in_team
    }
