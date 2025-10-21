import pytest
from unittest.mock import AsyncMock, patch
from src.users.crud import delete_user

@pytest.mark.asyncio
async def test_delete_user():
    """Проверка функции удаления пользователя"""
    mock_session = AsyncMock()
    
    await delete_user(mock_session, user_id=1)
    
    mock_session.execute.assert_called_once()
    call_args = mock_session.execute.call_args[0][0]
    assert str(call_args).startswith("DELETE FROM")
    
    mock_session.commit.assert_awaited_once()
