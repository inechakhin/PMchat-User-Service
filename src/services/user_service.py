from repositories.user_repository import UserRepository
from schemas.user import (
    UserResponse, 
    UserUpdateRequest,
)
from core.exceptions.user_error import UserNotFoundError

class UserService:
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_profile(self, user_id: int) -> UserResponse:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        
        return UserResponse.model_validate(user)

    async def update_profile(self, user_id: int, request: UserUpdateRequest) -> UserResponse:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        
        # Фильтруем только переданные поля (исключаем None)
        update_data = request.model_dump(exclude_unset=True)
        update_user = await self.user_repository.update(user, update_data)
        return UserResponse.model_validate(update_user)

    async def delete_profile(self, user_id: int) -> None:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        
        await self.user_repository.delete(user)
