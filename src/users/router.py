from fastapi import APIRouter

from sqlalchemy import delete
from src.auth.users import fastapi_users
from src.core.dependencies import CurrentUser, SessionDep
from src.users.crud import delete_user as delete_user_crud


users_router = APIRouter()

@users_router.delete("/me")
async def delete_me(
    user: CurrentUser,
    session: SessionDep,
):
    await delete_user_crud(session, user.id)

    return {"delete": "yes"}
