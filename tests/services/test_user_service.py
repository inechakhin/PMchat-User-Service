import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timezone

from services.user_service import UserService
from schemas.user import UserResponse, UserUpdateRequest
from core.exceptions.user_error import UserNotFoundError

@pytest.fixture
def mock_user_repo():
    return AsyncMock()

@pytest.fixture
def user_service(mock_user_repo):
    return UserService(user_repository=mock_user_repo)

def _fake_user_entity(user_id: int, **overrides) -> Mock:
    now = datetime.now(timezone.utc)
    user = Mock()
    user.id = user_id
    user.first_name = "Ivan"
    user.last_name = "Petrov"
    user.email = "ivan@example.com"
    user.role = "user"
    user.created_at = now
    user.updated_at = now
    for k, v in overrides.items():
        setattr(user, k, v)
    return user

def _assert_user_response(response: UserResponse, expected_id: int, email: str = "ivan@example.com"):
    assert isinstance(response, UserResponse)
    assert response.id == expected_id
    assert response.email == email

@pytest.mark.asyncio
async def test_get_profile_success(user_service, mock_user_repo):
    user_id = 42
    fake_user = _fake_user_entity(user_id)
    mock_user_repo.get_by_id.return_value = fake_user

    result = await user_service.get_profile(user_id)

    _assert_user_response(result, user_id)
    mock_user_repo.get_by_id.assert_awaited_once_with(user_id)

@pytest.mark.asyncio
async def test_get_profile_not_found(user_service, mock_user_repo):
    mock_user_repo.get_by_id.return_value = None
    with pytest.raises(UserNotFoundError, match="User with id 7 not found"):
        await user_service.get_profile(7)

@pytest.mark.asyncio
async def test_update_profile_success(user_service, mock_user_repo):
    user_id = 1
    original_user = _fake_user_entity(user_id)
    updated_user = _fake_user_entity(
        user_id,
        first_name="Petr",
        last_name="Sidorov",
        updated_at=datetime.now(timezone.utc)
    )
    mock_user_repo.get_by_id.return_value = original_user
    mock_user_repo.update.return_value = updated_user

    request = UserUpdateRequest(first_name="Petr", last_name="Sidorov")
    result = await user_service.update_profile(user_id, request)

    _assert_user_response(result, user_id)
    assert result.first_name == "Petr"
    assert result.last_name == "Sidorov"
    mock_user_repo.update.assert_awaited_once_with(original_user, {"first_name": "Petr", "last_name": "Sidorov"})

@pytest.mark.asyncio
async def test_update_profile_partial(user_service, mock_user_repo):
    user_id = 2
    original_user = _fake_user_entity(user_id)
    updated_user = _fake_user_entity(user_id, first_name="Anna")
    mock_user_repo.get_by_id.return_value = original_user
    mock_user_repo.update.return_value = updated_user

    request = UserUpdateRequest(first_name="Anna")
    result = await user_service.update_profile(user_id, request)

    assert result.first_name == "Anna"
    assert result.last_name == "Petrov"
    mock_user_repo.update.assert_awaited_once_with(original_user, {"first_name": "Anna"})

@pytest.mark.asyncio
async def test_update_profile_not_found(user_service, mock_user_repo):
    mock_user_repo.get_by_id.return_value = None
    request = UserUpdateRequest(first_name="X")
    with pytest.raises(UserNotFoundError):
        await user_service.update_profile(99, request)

@pytest.mark.asyncio
async def test_delete_profile_success(user_service, mock_user_repo):
    fake_user = _fake_user_entity(33)
    mock_user_repo.get_by_id.return_value = fake_user

    await user_service.delete_profile(33)

    mock_user_repo.delete.assert_awaited_once_with(fake_user)

@pytest.mark.asyncio
async def test_delete_profile_not_found(user_service, mock_user_repo):
    mock_user_repo.get_by_id.return_value = None
    with pytest.raises(UserNotFoundError):
        await user_service.delete_profile(404)