import pytest


@pytest.mark.anyio
async def test_register_user_writes_to_test_database(client):
    response = await client.post(
        "/auth/register",
        json={
            "id": 100,
            "email": "student@example.com",
            "password": "strong-password",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "student@example.com"
