from fastapi import Depends

from src.teams.service import ensure_can_create_team
from src.core.dependencies import CurrentUser


async def require_team_admin_or_superuser(user: CurrentUser):
    ensure_can_create_team(user)
    return user
