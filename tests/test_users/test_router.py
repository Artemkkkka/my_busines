import pytest
from unittest.mock import AsyncMock
from src.users.router import delete_me, me_team

@pytest.mark.asyncio
async def test_delete_me():
    """Проверка эндпоинта удаления текущего пользователя"""
    mock_user = AsyncMock()
    mock_user_manager = AsyncMock()
    
    response = await delete_me(
        user=mock_user,
        user_manager=mock_user_manager
    )
    
    # Проверяем вызов менеджера пользователей
    mock_user_manager.delete.assert_awaited_with(mock_user)
    
    # Проверяем формат ответа
    assert response.status_code == 204
    assert response.body == b"null"

@pytest.mark.asyncio
async def test_me_team():
    """Проверка эндпоинта получения информации о команде"""
    mock_user = AsyncMock()
    mock_user.team_id = 1
    mock_user.role_in_team = "employee"
    
    response = await me_team(mock_user)
    
    assert response == {
        "team_id": 1,
        "role_in_team": "employee"
    }

@pytest.mark.asyncio
async def test_me_team_without_team():
    """Проверка эндпоинта при отсутствии команды"""
    mock_user = AsyncMock()
    mock_user.team_id = None
    mock_user.role_in_team = "employee"
    
    response = await me_team(mock_user)
    
    assert response["team_id"] is None
