import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY

from services.auth_service import AuthService
from schemas.auth import SignUpRequest, SignInRequest, JwtAuthResponse
from core.exceptions.user_error import UserExistError, UserNotFoundError
from core.exceptions.auth_error import InvalidCredentialError
from jwt.exceptions import InvalidTokenError

@pytest.fixture
def mock_user_repo():
    return AsyncMock()

@pytest.fixture
def auth_service(mock_user_repo):
    service = AuthService(user_repository=mock_user_repo)
    service.password_hash = MagicMock()
    service.password_hash.hash.return_value = "hashed_password"
    service.password_hash.verify.return_value = True
    return service

def _jwt_subject(user_id: int = 42) -> dict:
    return {"id": str(user_id), "email": "ivan@example.com", "role": "user"}

def _mock_user(**overrides) -> MagicMock:
    user = MagicMock()
    user.id = 42
    user.email = "ivan@example.com"
    user.password = "hashed_password"
    user.jwt_subject = _jwt_subject()
    for k, v in overrides.items():
        setattr(user, k, v)
    return user

@pytest.mark.asyncio
async def test_signup_success(auth_service, mock_user_repo):
    mock_user_repo.exists_by_email.return_value = False
    request = SignUpRequest(
        first_name="Ivan",
        last_name="Petrov",
        email="ivan@example.com",
        password="secret"
    )
    await auth_service.signup(request)

    mock_user_repo.exists_by_email.assert_awaited_once_with("ivan@example.com")
    expected_create_data = request.model_dump(exclude_unset=True)
    expected_create_data["password"] = "hashed_password"
    mock_user_repo.create.assert_awaited_once_with(expected_create_data)

@pytest.mark.asyncio
async def test_signup_user_exists(auth_service, mock_user_repo):
    mock_user_repo.exists_by_email.return_value = True
    request = SignUpRequest(first_name="I", last_name="P", email="ivan@example.com", password="pass")

    with pytest.raises(UserExistError, match="Email ivan@example.com already registered"):
        await auth_service.signup(request)
    mock_user_repo.create.assert_not_awaited()

@pytest.mark.asyncio
async def test_signin_success(auth_service, mock_user_repo):
    user = _mock_user()
    mock_user_repo.get_by_email.return_value = user
    with patch("jwt.encode", side_effect=["fake_access_token", "fake_refresh_token"]):
        request = SignInRequest(email="ivan@example.com", password="secret")
        result = await auth_service.signin(request)

    assert isinstance(result, JwtAuthResponse)
    assert result.access_token == "fake_access_token"
    assert result.refresh_token == "fake_refresh_token"
    mock_user_repo.get_by_email.assert_awaited_once_with("ivan@example.com")
    auth_service.password_hash.verify.assert_called_once_with("secret", "hashed_password")

@pytest.mark.asyncio
async def test_signin_user_not_found(auth_service, mock_user_repo):
    mock_user_repo.get_by_email.return_value = None
    request = SignInRequest(email="no@user.com", password="x")
    with pytest.raises(UserNotFoundError):
        await auth_service.signin(request)

@pytest.mark.asyncio
async def test_signin_invalid_password(auth_service, mock_user_repo):
    user = _mock_user()
    mock_user_repo.get_by_email.return_value = user
    auth_service.password_hash.verify.return_value = False
    request = SignInRequest(email="ivan@example.com", password="wrong")

    with pytest.raises(InvalidCredentialError, match="Invalid credentials"):
        await auth_service.signin(request)

@pytest.mark.asyncio
async def test_refresh_success(auth_service, mock_user_repo):
    payload = {"type": "refresh", "id": "42", "exp": "..."}
    user = _mock_user(id=42)
    mock_user_repo.get_by_id.return_value = user

    with patch("jwt.decode", return_value=payload) as mock_decode, \
         patch("jwt.encode", side_effect=["new_access_token", "new_refresh_token"]):
        result = await auth_service.refresh("valid_refresh_token")

    assert isinstance(result, JwtAuthResponse)
    assert result.access_token == "new_access_token"
    assert result.refresh_token == "new_refresh_token"
    mock_decode.assert_called_once_with("valid_refresh_token", ANY, algorithms=[ANY])
    mock_user_repo.get_by_id.assert_awaited_once_with(42)

@pytest.mark.asyncio
async def test_refresh_wrong_token_type(auth_service, mock_user_repo):
    payload = {"type": "access", "id": "42"}
    with patch("jwt.decode", return_value=payload):
        with pytest.raises(InvalidTokenError):
            await auth_service.refresh("some_token")

@pytest.mark.asyncio
async def test_refresh_missing_id(auth_service, mock_user_repo):
    payload = {"type": "refresh"}
    with patch("jwt.decode", return_value=payload):
        with pytest.raises(TypeError):
            await auth_service.refresh("token_no_id")

@pytest.mark.asyncio
async def test_refresh_user_not_found(auth_service, mock_user_repo):
    payload = {"type": "refresh", "id": "99"}
    mock_user_repo.get_by_id.return_value = None
    with patch("jwt.decode", return_value=payload):
        with pytest.raises(UserNotFoundError, match="User with id 99 not found"):
            await auth_service.refresh("token")

@pytest.mark.asyncio
async def test_refresh_invalid_token_decode_error(auth_service):
    with patch("jwt.decode", side_effect=InvalidTokenError("bad signature")):
        with pytest.raises(InvalidTokenError):
            await auth_service.refresh("garbage_token")