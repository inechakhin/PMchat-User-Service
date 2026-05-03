from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash

from core.config import settings
from repositories.user_repository import UserRepository
from schemas.auth import (
    SignUpRequest,
    SignInRequest,
    JwtAuthResponse,
)
from core.exceptions.user_error import UserExistError, UserNotFoundError
from core.exceptions.auth_error import InvalidCredentialError
from jwt.exceptions import InvalidTokenError
from utils.logging import logger

class AuthService:
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.password_hash = PasswordHash.recommended()

    def _get_password_hash(self, password: str) -> str:
        return self.password_hash.hash(password)

    def _verify_password(self, plain: str, hashed: str) -> bool:
        return self.password_hash.verify(plain, hashed)
    
    def _create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def _create_refresh_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
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
        logger.info(f"Signup attempt for email: {request.email}")
        if await self.user_repository.exists_by_email(request.email):
            logger.error(f"Signup failed: email {request.email} already exists")
            raise UserExistError(f"Email {request.email} already registered")
        
        create_data = request.model_dump(exclude_unset=True)
        create_data["password"] = self._get_password_hash(request.password)
        await self.user_repository.create(create_data)
        logger.info(f"User created successfully with email: {request.email}")

    async def signin(self, request: SignInRequest) -> JwtAuthResponse:
        logger.info(f"Signin attempt for email: {request.email}")
        user = await self.user_repository.get_by_email(request.email)
        if not user:
            logger.error(f"Signin failed: user with email {request.email} not found")
            raise UserNotFoundError(f"User with email {request.email} not found")
        if not self._verify_password(request.password, user.password):
            logger.error(f"Signin failed: invalid password for email {request.email}")
            raise InvalidCredentialError("Invalid credentials")
        
        logger.info(f"User {user.id} signed in successfully")
        return self._create_jwt_auth_response(user.jwt_subject)

    async def refresh(self, refresh_token: str) -> JwtAuthResponse:
        logger.info("Token refresh attempt")
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != "refresh":
                logger.error("Refresh attempt with non-refresh token type")
                raise InvalidTokenError()
            user_id = int(payload.get("id"))
            if user_id is None:
                logger.error("Refresh token missing user id claim")
                raise InvalidTokenError()
            
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                logger.error(f"User id {user_id} from refresh token not found in database")
                raise UserNotFoundError(f"User with id {user_id} not found")
            
            logger.info(f"Tokens refreshed successfully for user {user_id}")
            return self._create_jwt_auth_response(user.jwt_subject)
        except InvalidTokenError as e:
            logger.error(f"Invalid refresh token: {e}")
            raise
