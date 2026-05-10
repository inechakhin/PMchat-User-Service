from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from schemas.auth import (
    SignUpRequest,
    SignInRequest,
    JwtAuthResponse,
)
from services.auth_service import AuthService
from dependencies.auth import get_auth_service, get_refresh_token
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
        tokens = await auth_service.signin(request)
        return _build_auth_response("authenticated", tokens)
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
    refresh_token: str = Depends(get_refresh_token),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        tokens = await auth_service.refresh(refresh_token)
        return _build_auth_response("refreshed", tokens)
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
       
@auth_router.post("/logout")
async def logout():
    return _build_auth_response("logged out", None)
 
def _build_auth_response(status: str, tokens: JwtAuthResponse):
    response = JSONResponse(content={"status": status})
    if tokens is None:
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
    else:
        response.set_cookie(
            key="access_token",
            value=tokens.access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=15 * 60, # 15 минут
        )
        response.set_cookie(
            key="refresh_token",
            value=tokens.refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=7 * 24 * 3600, # 7 дней
        )
    return response