import json

import pytest


def test_ping():
    assert 1 == 1


async def test_create_team(client):
    user_data = {
        "members": [
            {
                "role": "employee",
                "user_id": 3
            }
        ],
        "name": "Platform"
    }
    resp = client.post("/team/", data=json.dumps(user_data))
    data_from_resp = resp.json()
    assert resp.status_code == 200
    assert data_from_resp["name"] == user_data["name"]
    assert data_from_resp["surname"] == user_data["surname"]
    assert data_from_resp["email"] == user_data["email"]
    assert data_from_resp["is_active"] is True
