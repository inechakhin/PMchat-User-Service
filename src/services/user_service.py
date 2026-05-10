from repositories.user_repository import UserRepository
from schemas.user import (
    UserResponse,
    UserUpdateRequest,
)
from core.exceptions.user_error import UserNotFoundError
from utils.logging import logger

class UserService:
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_profile(self, user_id: int) -> UserResponse:
        logger.info(f"Fetching profile for user id: {user_id}")
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            logger.error(f"User profile not found for id: {user_id}")
            raise UserNotFoundError(f"User with id {user_id} not found")
        
        logger.info(f"Profile retrieved for user {user_id}")
        return UserResponse.model_validate(user)

    async def update_profile(self, user_id: int, request: UserUpdateRequest) -> UserResponse:
        logger.info(f"Updating profile for user id: {user_id}")
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            logger.error(f"User profile not found for update id: {user_id}")
            raise UserNotFoundError(f"User with id {user_id} not found")
        
        update_data = request.model_dump(exclude_unset=True)
        update_user = await self.user_repository.update(user, update_data)
        logger.info(f"Profile updated successfully for user {user_id}")
        return UserResponse.model_validate(update_user)

    async def delete_profile(self, user_id: int) -> None:
        logger.info(f"Deleting profile for user id: {user_id}")
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            logger.error(f"User profile not found for deletion id: {user_id}")
            raise UserNotFoundError(f"User with id {user_id} not found")
        
        await self.user_repository.delete(user)
        logger.info(f"User {user_id} profile deleted successfully")