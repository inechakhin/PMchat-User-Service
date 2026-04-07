from fastapi import Depends, Request, HTTPException, status

from repositories.user_repository import UserRepository
from dependencies.user import get_user_repository
from services.auth_service import AuthService

async def get_auth_service(user_repository: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repository)

def get_refresh_token(request: Request) -> str:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing in cookies",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return refresh_token