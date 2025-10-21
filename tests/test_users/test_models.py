# test_models.py
import pytest
from src.users.models import User, TeamRole

def test_user_model_initialization():
    """Проверка корректного создания модели пользователя"""
    user = User(
        email="test@example.com",
        role_in_team=TeamRole.employee,
        team_id=1
    )
    
    assert user.email == "test@example.com"
    assert user.role_in_team == TeamRole.employee
    assert user.team_id == 1
    assert hasattr(user, 'authored_tasks')
    assert hasattr(user, 'assigned_tasks')

def test_team_role_enum():
    """Проверка значений enum TeamRole"""
    assert TeamRole.admin.value == "admin"
    assert TeamRole.manager.value == "manager"
    assert TeamRole.employee.value == "employee"
