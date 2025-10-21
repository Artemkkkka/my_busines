import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from src.users.actions.route_superuser import create_superuser_endpoint, make_user_admin, SuperuserIn
from src.users.models import TeamRole

@pytest.mark.asyncio
@patch('src.users.actions.route_superuser.create_superuser')
async def test_create_superuser_success(mock_create_superuser):
    mock_body = AsyncMock()
    mock_body.email = "admin@test.com"
    mock_body.password = "admin123"
    
    mock_user = AsyncMock()
    mock_create_superuser.return_value = mock_user
    
    result = await create_superuser_endpoint(mock_body)
    
    mock_create_superuser.assert_awaited_once_with(email="admin@test.com", password="admin123")
    assert result == mock_user

@pytest.mark.asyncio
@patch('src.users.actions.route_superuser.create_superuser')
async def test_create_superuser_already_exists(mock_create_superuser):
    mock_body = AsyncMock()
    mock_body.email = "admin@test.com"
    mock_body.password = "admin123"
    
    mock_create_superuser.side_effect = Exception("User already exists with unique constraint")
    
    with pytest.raises(HTTPException) as exc_info:
        await create_superuser_endpoint(mock_body)
    
    assert exc_info.value.status_code == 409
    assert "уже существует" in exc_info.value.detail

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
