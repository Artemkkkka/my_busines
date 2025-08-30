from fastapi import HTTPException, status

from src.core.dependencies import CurrentUser
from src.users.models import User, TeamRole


async def forbid_employee(user: CurrentUser) -> User:
    if user.role_in_team == TeamRole.employee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden for employees")
    return user


async def ensure_can_rate_task(user: User) -> None:
    if getattr(user, "is_superuser", False):
        return
    if getattr(user, "role_in_team", None) == TeamRole.admin:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Оценивают только администраторы команды или суперпользователи.",
    )


async def require_team_admin_or_superuser(user: CurrentUser):
    await ensure_can_rate_task(user)
    return user
