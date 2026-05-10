import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from routers.user_router import user_router
from dependencies.user import get_user_service, get_current_user_id
from services.user_service import UserService
from schemas.user import UserResponse, UserUpdateRequest
from core.exceptions.user_error import UserNotFoundError

USER_ID = 42
NOW = datetime.now(timezone.utc)

@pytest.fixture
def mock_user_service():
    service = MagicMock(spec=UserService)
    service.get_profile = AsyncMock()
    service.update_profile = AsyncMock()
    service.delete_profile = AsyncMock()
    return service

@pytest.fixture
def test_app(mock_user_service):
    app = FastAPI()
    app.include_router(user_router)

    async def override_get_current_user_id():
        return USER_ID

    async def override_get_user_service():
        return mock_user_service

    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    app.dependency_overrides[get_user_service] = override_get_user_service
    return app

@pytest.fixture
async def client(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac

def make_user_response(**overrides) -> UserResponse:
    data = {
        "id": USER_ID,
        "first_name": "Ivan",
        "last_name": "Petrov",
        "email": "ivan@example.com",
        "role": "user",
        "created_at": NOW,
        "updated_at": NOW,
    }
    data.update(overrides)
    return UserResponse(**data)

@pytest.mark.asyncio
async def test_get_profile_success(client, mock_user_service):
    profile = make_user_response()
    mock_user_service.get_profile.return_value = profile

    response = await client.get("/internal/api/users/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == USER_ID
    assert data["email"] == "ivan@example.com"
    mock_user_service.get_profile.assert_awaited_once_with(USER_ID)

@pytest.mark.asyncio
async def test_get_profile_not_found(client, mock_user_service):
    mock_user_service.get_profile.side_effect = UserNotFoundError("User not found")
    response = await client.get("/internal/api/users/profile")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_get_profile_internal_error(client, mock_user_service):
    mock_user_service.get_profile.side_effect = Exception("DB down")
    response = await client.get("/internal/api/users/profile")
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"

@pytest.mark.asyncio
async def test_update_profile_success(client, mock_user_service):
    updated = make_user_response(first_name="Petr", last_name="Sidorov")
    mock_user_service.update_profile.return_value = updated

    response = await client.patch(
        "/internal/api/users/profile",
        json={"first_name": "Petr", "last_name": "Sidorov"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Petr"
    assert data["last_name"] == "Sidorov"
    mock_user_service.update_profile.assert_awaited_once()
    args, _ = mock_user_service.update_profile.call_args
    assert args[0] == USER_ID
    assert args[1] == UserUpdateRequest(first_name="Petr", last_name="Sidorov")

@pytest.mark.asyncio
async def test_update_profile_partial(client, mock_user_service):
    updated = make_user_response(first_name="Anna")
    mock_user_service.update_profile.return_value = updated

    response = await client.patch(
        "/internal/api/users/profile",
        json={"first_name": "Anna"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Anna"
    assert data["last_name"] == "Petrov"  # не изменилось
    mock_user_service.update_profile.assert_awaited_once()
    args, _ = mock_user_service.update_profile.call_args
    assert args[1] == UserUpdateRequest(first_name="Anna")

@pytest.mark.asyncio
async def test_update_profile_not_found(client, mock_user_service):
    mock_user_service.update_profile.side_effect = UserNotFoundError("User not found")
    response = await client.patch("/internal/api/users/profile", json={"first_name": "X"})
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_update_profile_internal_error(client, mock_user_service):
    mock_user_service.update_profile.side_effect = Exception("fail")
    response = await client.patch("/internal/api/users/profile", json={"first_name": "X"})
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"

@pytest.mark.asyncio
async def test_delete_profile_success(client, mock_user_service):
    mock_user_service.delete_profile.return_value = None
    response = await client.delete("/internal/api/users/profile")
    assert response.status_code == 200
    assert response.json() is None
    mock_user_service.delete_profile.assert_awaited_once_with(USER_ID)

@pytest.mark.asyncio
async def test_delete_profile_not_found(client, mock_user_service):
    mock_user_service.delete_profile.side_effect = UserNotFoundError("User not found")
    response = await client.delete("/internal/api/users/profile")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_delete_profile_internal_error(client, mock_user_service):
    mock_user_service.delete_profile.side_effect = Exception("boom")
    response = await client.delete("/internal/api/users/profile")
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"