from fastapi import APIRouter, Depends, HTTPException, status

from schemas.auth import (
    SignUpRequest,
    SignInRequest,
    RefreshRequest,
    JwtAuthResponse,
)
from services.auth_service import AuthService
from dependencies.auth import get_auth_service
from core.exceptions.user_error import UserExistError, UserNotFoundError
from core.exceptions.auth_error import InvalidCredentialError
from jwt.exceptions import InvalidTokenError

from utils.logging import logger

auth_router = APIRouter(prefix="/internal/api/auth", tags=["auth"])

@auth_router.post("/signup", response_model=None)
async def signup(
    request: SignUpRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        await auth_service.signup(request)
    except UserExistError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=e.message,
        )
    except Exception as e:
        logger.exception(f"Internal server error in signup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

@auth_router.post("/signin", response_model=JwtAuthResponse)
async def signin(
    request: SignInRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        return await auth_service.signin(request)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except InvalidCredentialError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.exception(f"Internal server error in signin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

@auth_router.post("/refresh", response_model=JwtAuthResponse)
async def refresh(
    request: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        return await auth_service.refresh(request)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        logger.exception(f"Internal server error in refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )