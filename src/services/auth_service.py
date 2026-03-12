from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash

from core.config import settings
from repositories.user_repository import UserRepository
from schemas.auth import (
    SignUpRequest,
    SignInRequest,
    RefreshRequest,
    JwtAuthResponse,
)
from core.exceptions.user_error import UserExistError, UserNotFoundError
from core.exceptions.auth_error import InvalidCredentialError
from jwt.exceptions import InvalidTokenError

class AuthService:
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.password_hash = PasswordHash.recommended()

    def _get_password_hash(self, password: str) -> str:
        return self.password_hash.hash(password)

    def _verify_password(self, plain: str, hashed: str) -> bool:
        return self.password_hash.verify(plain, hashed)
    
    def _create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def _create_refresh_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=7)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def _create_jwt_auth_response(self, data: dict) -> JwtAuthResponse:
        return JwtAuthResponse(
            access_token=self._create_access_token(data),
            refresh_token=self._create_refresh_token(data),
        )

    async def signup(self, request: SignUpRequest) -> None:
        if await self.user_repository.exists_by_email(request.email):
            raise UserExistError(f"Email {request.email} already registered")
        
        create_data = request.model_dump(exclude_unset=True)
        create_data["password"] = self._get_password_hash(request.password)
        await self.user_repository.create(create_data)

    async def signin(self, request: SignInRequest) -> JwtAuthResponse:
        user = await self.user_repository.get_by_email(request.email)
        if not user:
            raise UserNotFoundError(f"User with email {request.email} not found")
        if not self._verify_password(request.password, user.password):
            raise InvalidCredentialError("Invalid credentials")
        
        return self._create_jwt_auth_response(user.jwt_subject)

    async def refresh(self, request: RefreshRequest) -> JwtAuthResponse:
        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise InvalidTokenError()
        user_id = int(payload.get("id"))
        if user_id is None:
            raise InvalidTokenError()
        
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        
        return self._create_jwt_auth_response(user.jwt_subject)