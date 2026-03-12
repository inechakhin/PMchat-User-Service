from fastapi import Depends

from repositories.user_repository import UserRepository
from dependencies.user import get_user_repository
from services.auth_service import AuthService

async def get_auth_service(user_repository: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repository)
