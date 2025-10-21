from fastapi import HTTPException, status

from src.users.models import User, TeamRole


def ensure_can_create_team(user: User) -> None:
    """Разрешаем создание команды только суперюзеру или администратору команды."""
    if getattr(user, "is_superuser", False):
        return
    if getattr(user, "role_in_team", None) == TeamRole.admin:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Создавать команды могут только администраторы команды или суперпользователи.",
    )
