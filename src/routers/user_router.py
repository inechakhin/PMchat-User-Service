from fastapi import APIRouter, Depends, HTTPException, status

from schemas.user import (
    UserResponse, 
    UserUpdateRequest,
)
from services.user_service import UserService
from dependencies.user import get_user_service, get_current_user_id
from core.exceptions.user_error import UserNotFoundError
from utils.logging import logger

user_router = APIRouter(prefix="/internal/api/users", tags=["users"])

@user_router.get("/profile", response_model=UserResponse)
async def get_profile(
    user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    try:
        return await user_service.get_profile(user_id)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        logger.exception(f"Internal server error in get_profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

@user_router.patch("/profile", response_model=UserResponse)
async def update_profile(
    request: UserUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    try:
        return await user_service.update_profile(user_id, request)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        logger.exception(f"Internal server error in update_profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

@user_router.delete("/profile")
async def delete_profile(
    user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    try:
        await user_service.delete_profile(user_id)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        logger.exception(f"Internal server error in delete_profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
