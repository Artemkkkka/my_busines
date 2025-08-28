from fastapi import Depends, HTTPException, status

from src.auth.users import current_user
from src.core.dependencies import CurrentUser
from src.users.models import User, TeamRole


async def forbid_employee(user: CurrentUser) -> User:
    if user.role_in_team == TeamRole.employee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden for employees")
    return user
