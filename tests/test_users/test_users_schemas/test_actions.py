import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from src.users.actions.route_superuser import make_user_admin, SuperuserIn
from src.users.models import TeamRole


@pytest.mark.asyncio
async def test_make_user_admin():
    mock_user = AsyncMock()
    mock_user.role_in_team = TeamRole.employee

    mock_session = AsyncMock()
    mock_session.scalar.return_value = mock_user

    mock_superuser = AsyncMock()

    response = await make_user_admin(1, mock_superuser, mock_session)

    assert mock_user.role_in_team == TeamRole.admin
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_make_user_admin_not_found():
    mock_session = AsyncMock()
    mock_session.scalar.return_value = None

    mock_superuser = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await make_user_admin(999, mock_superuser, mock_session)

    assert exc_info.value.status_code == 404


def test_superuser_in_schema():
    schema = SuperuserIn(email="test@test.com", password="pass123")
    assert schema.email == "test@test.com"
    assert schema.password == "pass123"
