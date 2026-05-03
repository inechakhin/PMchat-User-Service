import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock

from routers.auth_router import auth_router
from dependencies.auth import get_auth_service, get_refresh_token
from services.auth_service import AuthService
from schemas.auth import JwtAuthResponse
from core.exceptions.user_error import UserExistError, UserNotFoundError
from core.exceptions.auth_error import InvalidCredentialError
from jwt.exceptions import InvalidTokenError

@pytest.fixture
def mock_auth_service():
    service = MagicMock(spec=AuthService)
    service.signup = AsyncMock()
    service.signin = AsyncMock()
    service.refresh = AsyncMock()
    return service

@pytest.fixture
def test_app(mock_auth_service):
    app = FastAPI()
    app.include_router(auth_router)

    async def override_get_auth_service():
        return mock_auth_service

    async def override_get_refresh_token():
        return "valid_refresh_token"

    app.dependency_overrides[get_auth_service] = override_get_auth_service
    app.dependency_overrides[get_refresh_token] = override_get_refresh_token
    return app

@pytest.fixture
async def client(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_signup_success(client, mock_auth_service):
    response = await client.post("/internal/api/auth/signup", json={
        "first_name": "Ivan",
        "last_name": "Petrov",
        "email": "ivan@example.com",
        "password": "secret"
    })
    assert response.status_code == 200
    assert response.json() is None
    mock_auth_service.signup.assert_awaited_once()

@pytest.mark.asyncio
async def test_signup_user_exists(client, mock_auth_service):
    mock_auth_service.signup.side_effect = UserExistError("Email exists")
    response = await client.post("/internal/api/auth/signup", json={
        "first_name": "Ivan",
        "last_name": "Petrov",
        "email": "ivan@example.com",
        "password": "secret"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email exists"

@pytest.mark.asyncio
async def test_signup_internal_error(client, mock_auth_service):
    mock_auth_service.signup.side_effect = Exception("DB down")
    response = await client.post("/internal/api/auth/signup", json={
        "first_name": "Ivan",
        "last_name": "Petrov",
        "email": "ivan@example.com",
        "password": "secret"
    })
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"

@pytest.mark.asyncio
async def test_signin_success(client, mock_auth_service):
    tokens = JwtAuthResponse(access_token="access", refresh_token="refresh")
    mock_auth_service.signin.return_value = tokens
    response = await client.post("/internal/api/auth/signin", json={
        "email": "ivan@example.com",
        "password": "secret"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "authenticated"
    cookies = response.cookies
    assert cookies.get("access_token") == "access"
    assert cookies.get("refresh_token") == "refresh"
    set_cookie_headers = response.headers.get_list("set-cookie")
    assert any("access_token=access" in h for h in set_cookie_headers)
    assert any("refresh_token=refresh" in h for h in set_cookie_headers)

@pytest.mark.asyncio
async def test_signin_user_not_found(client, mock_auth_service):
    mock_auth_service.signin.side_effect = UserNotFoundError("User not found")
    response = await client.post("/internal/api/auth/signin", json={
        "email": "missing@example.com",
        "password": "secret"
    })
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_signin_invalid_credentials(client, mock_auth_service):
    mock_auth_service.signin.side_effect = InvalidCredentialError("Invalid credentials")
    response = await client.post("/internal/api/auth/signin", json={
        "email": "ivan@example.com",
        "password": "wrong"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
    assert "WWW-Authenticate" in response.headers

@pytest.mark.asyncio
async def test_signin_internal_error(client, mock_auth_service):
    mock_auth_service.signin.side_effect = Exception("Oops")
    response = await client.post("/internal/api/auth/signin", json={
        "email": "ivan@example.com",
        "password": "secret"
    })
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"

@pytest.mark.asyncio
async def test_refresh_success(client, mock_auth_service):
    tokens = JwtAuthResponse(access_token="new_access", refresh_token="new_refresh")
    mock_auth_service.refresh.return_value = tokens
    response = await client.post("/internal/api/auth/refresh")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "refreshed"
    cookies = response.cookies
    assert cookies.get("access_token") == "new_access"
    assert cookies.get("refresh_token") == "new_refresh"

@pytest.mark.asyncio
async def test_refresh_invalid_token(client, mock_auth_service):
    mock_auth_service.refresh.side_effect = InvalidTokenError()
    response = await client.post("/internal/api/auth/refresh")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"
    assert "WWW-Authenticate" in response.headers

@pytest.mark.asyncio
async def test_refresh_user_not_found(client, mock_auth_service):
    mock_auth_service.refresh.side_effect = UserNotFoundError("User not found")
    response = await client.post("/internal/api/auth/refresh")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_refresh_internal_error(client, mock_auth_service):
    mock_auth_service.refresh.side_effect = Exception("Fail")
    response = await client.post("/internal/api/auth/refresh")
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"

@pytest.mark.asyncio
async def test_logout(client):
    response = await client.post("/internal/api/auth/logout")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "logged out"

    set_cookie_headers = response.headers.get_list("set-cookie")
    assert any("access_token=" in h and "Max-Age=0" in h for h in set_cookie_headers), \
        f"access_token not deleted, got headers: {set_cookie_headers}"
    assert any("refresh_token=" in h and "Max-Age=0" in h for h in set_cookie_headers), \
        f"refresh_token not deleted, got headers: {set_cookie_headers}"