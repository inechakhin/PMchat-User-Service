from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Request, HTTPException, status
import jwt

from core.config import settings
from db.postgres import get_session
from repositories.user_repository import UserRepository
from services.user_service import UserService
from jwt.exceptions import InvalidTokenError

async def get_user_repository(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(session)

async def get_user_service(user_repository: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(user_repository)

async def get_current_user_id(request: Request) -> int:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="No user id in token")
        return int(user_id)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")