# test_schemas.py
import pytest
from src.users.schemas import UserCreate, UserRead

def test_user_create_schema():
    """Проверка схемы создания пользователя"""
    user_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    user = UserCreate(**user_data)
    
    assert user.email == user_data["email"]
    assert user.password == user_data["password"]

def test_user_read_schema():
    """Проверка схемы чтения пользователя"""
    user_data = {
        "email": "test@example.com",
        "role_in_team": "employee",
        "team_id": 1
    }
    user = UserRead(**user_data)
    
    assert user.email == user_data["email"]
    assert user.role_in_team == user_data["role_in_team"]
    assert user.team_id == user_data["team_id"]
