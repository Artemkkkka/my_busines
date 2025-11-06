from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from src.core.dependencies import SessionDep, CurrentSuperUser
from src.users.models import User, TeamRole


superuser_router = APIRouter(prefix="/superuser", tags=["superuser"])


class SuperuserIn(BaseModel):
    email: EmailStr = 'admin@admin.com'
    password: str = 'admin_password'


@superuser_router.patch("/{user_id}/make-admin", status_code=status.HTTP_204_NO_CONTENT)
async def make_user_admin(
    user_id: int,
    _: CurrentSuperUser,
    session: SessionDep,
):
    user = await session.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role_in_team != TeamRole.admin:
        user.role_in_team = TeamRole.admin
        await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
